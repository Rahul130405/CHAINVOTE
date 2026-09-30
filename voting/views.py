from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Count
from django.db import transaction
from django.core.cache import cache

from .models import Election, Candidate, Vote, SecurityLog
from .serializers import ElectionSerializer, ElectionListSerializer, VoteSerializer
import hashlib
import logging
import os
import hmac
import re
from .utils.encryption import encrypt_vote, decrypt_vote
from .utils.blockchain import verify_election_blockchain
from .utils.candidate_automation import execute_candidate_automation, ensure_initial_election_data
from .decorators import admin_required
from .forms import ElectionForm, CandidateForm, candidate_has_recorded_votes

logger = logging.getLogger('chainvote.views')



# ─────────────────────────────────────────────
# FRONTEND VIEWS
# ─────────────────────────────────────────────

def home(request):
    """Landing page — Command Center with stats and elections (Optimized queries & caching)."""
    cache_key = 'home_landing_context'
    context = cache.get(cache_key)

    if context is None:
        now = timezone.now()
        # Single DB query with Count annotation and prefetch_related for candidates only
        elections = list(
            Election.objects.exclude(title='ChainVote Network Audit & Protocol Ledger')
            .annotate(total_votes_count=Count('votes'))
            .prefetch_related('candidates')
            .order_by('-start_time')
        )

        active = [e for e in elections if e.start_time <= now <= e.end_time]
        if not active:
            ensure_initial_election_data()
            elections = list(
                Election.objects.exclude(title='ChainVote Network Audit & Protocol Ledger')
                .annotate(total_votes_count=Count('votes'))
                .prefetch_related('candidates')
                .order_by('-start_time')
            )
            active = [e for e in elections if e.start_time <= now <= e.end_time]

        upcoming = [e for e in elections if e.start_time > now]
        ended = [e for e in elections if e.end_time < now]

        total_blocks = Vote.objects.count()
        latest_threat = (
            SecurityLog.objects.only('id', 'level', 'action', 'ip_address', 'details', 'timestamp').first()
            if hasattr(SecurityLog, 'objects') else None
        )

        context = {
            'active_elections': active,
            'upcoming_elections': upcoming,
            'ended_elections': ended,
            'total_blocks': total_blocks,
            'latest_threat': latest_threat,
        }
        # In-memory micro-cache: eliminates repeated DB round-trips on refreshes
        cache.set(cache_key, context, timeout=20)

    return render(request, 'voting/home.html', context)

@login_required
def election_detail(request, election_id):
    """Single election page with secure voting form (Prefetches candidates)."""
    election = get_object_or_404(
        Election.objects.prefetch_related('candidates'),
        id=election_id
    )
    candidates = election.candidates.all()
    user_vote = None

    return render(request, 'voting/election_detail.html', {
        'election': election,
        'candidates': candidates,
        'user_vote': user_vote,
    })

VOTER_ID_REGEX = re.compile(r'^[A-Za-z0-9]{10}$')

def validate_voter_id(identity):
    """
    Strictly validates that a voter ID consists of exactly 10 alphanumeric characters (A-Z, a-z, 0-9).
    No spaces, hyphens, or special characters are permitted.
    Returns True if valid, False otherwise.
    """
    if not identity or not isinstance(identity, str):
        return False
    return bool(VOTER_ID_REGEX.match(identity))

def hash_identity(identity):
    return hashlib.sha256(identity.encode()).hexdigest()


@login_required
def cast_vote(request, election_id):
    """Handle vote form submission and log threats."""
    if request.method != "POST":
        return redirect('election_detail', election_id=election_id)

    election = get_object_or_404(Election, id=election_id)

    # 🌐 Get IP Address FIRST so we can log threats
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    # 🧾 Get ID (Aadhaar/College ID)
    identity = request.POST.get("aadhaar")
    if not identity:
        messages.error(request, "ID is required")
        return redirect('election_detail', election_id=election_id)

    if not validate_voter_id(identity):
        messages.error(request, "Invalid Voter ID: Must be exactly 10 alphanumeric characters.")
        return redirect('election_detail', election_id=election_id)

    # 🔐 Hash identity
    voter_hash = hash_identity(identity)

    # 🗳 Get candidate
    candidate_id = request.POST.get("candidate_id")
    if not candidate_id:
        messages.error(request, "Please select a candidate")
        return redirect('election_detail', election_id=election_id)

    with transaction.atomic():
        # 1. Acquire Candidate row lock before checking election status
        candidate = (
            Candidate.objects
            .select_for_update()
            .select_related('election')
            .filter(id=candidate_id, election=election)
            .first()
        )
        if not candidate:
            raise Http404("Candidate not found or no longer available.")

        # 2. Revalidate election status only after acquiring candidate lock
        if not candidate.election.is_active:
            messages.error(request, f"This election is {candidate.election.status}. Voting is not allowed.")
            return redirect('election_detail', election_id=election_id)

        # 3. 🚨 SOC SECURITY TRIGGER: Prevent duplicate voting & LOG THE THREAT
        if Vote.objects.filter(election=candidate.election, voter_hash=voter_hash).exists():
            SecurityLog.objects.create(
                level='CRITICAL',
                action='Duplicate Vote Blocked',
                ip_address=ip,
                details=f"Voter hash {voter_hash[:15]}... attempted to bypass the ledger in '{candidate.election.title}'."
            )
            messages.error(request, "SECURITY ALERT: You have already voted with this ID. This attempt has been logged.")
            return redirect('election_detail', election_id=election_id)

        # 4. 🔐 Encrypt vote
        encrypted = encrypt_vote(candidate.id)

        # 5. 💾 Save vote
        new_vote = Vote.objects.create(
            election=candidate.election,
            encrypted_vote=encrypted,
            voter_hash=voter_hash,
            voter_ip=ip
        )

    # Invalidate landing cache so stats update immediately
    cache.delete('home_landing_context')

    messages.success(request, "Your vote has been securely recorded on the blockchain!")
    return redirect('election_detail', election_id=election_id)

def results_view(request, election_id):
    """Show election results (Only if ended and blockchain is valid). Single-query vote fetch."""
    election = get_object_or_404(
        Election.objects.prefetch_related('candidates'),
        id=election_id
    )

    # 🚫 BLOCK RESULTS BEFORE END
    if election.status != 'ended':
        return render(request, 'voting/results.html', {
            'election': election,
            'candidates': [],
            'message': "Results are locked until election ends"
        })

    # Fetch votes in a single query
    votes = list(Vote.objects.filter(election=election).order_by('id'))

    # 🔗 VERIFY BLOCKCHAIN BEFORE SHOWING RESULTS (Reuses votes list, zero duplicate queries)
    is_valid, bc_message = verify_election_blockchain(election, votes=votes)
    if not is_valid:
        return render(request, 'voting/results.html', {
            'election': election,
            'candidates': [],
            'message': f"🚨 SECURITY ALERT: {bc_message} Results cannot be verified."
        })

    vote_count = {}
    for vote in votes:
        try:
            candidate_id = decrypt_vote(vote.encrypted_vote)
            vote_count[int(candidate_id)] = vote_count.get(int(candidate_id), 0) + 1
        except Exception:
            pass # Skip corrupted decryption

    candidates = list(election.candidates.all())
    for c in candidates:
        c.decrypted_votes = vote_count.get(c.id, 0)

    return render(request, 'voting/results.html', {
        'election': election,
        'candidates': candidates,
        'blockchain_status': bc_message
    })


@login_required
def blockchain_explorer(request, election_id):
    """Hackathon UI: Visualize the Live Blockchain."""
    election = get_object_or_404(Election, id=election_id)
    # Defer unneeded heavy fields and use index on (election, id)
    votes = (
        Vote.objects.filter(election=election)
        .only('id', 'voted_at', 'previous_hash', 'encrypted_vote', 'voter_hash', 'block_hash')
        .order_by('id')
    )
    return render(request, 'voting/explorer.html', {'election': election, 'votes': votes})


# ─────────────────────────────────────────────
# AUTHENTICATION VIEWS
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'home'))
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'voting/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if password != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            messages.success(request, f"Welcome to ChainVote, {username}!")
            return redirect('home')
    return render(request, 'voting/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────
# REST API VIEWS
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def api_election_list(request):
    """GET /api/elections/ (Single query with annotated total_votes, no unneeded prefetch)."""
    elections = Election.objects.annotate(total_votes_count=Count('votes')).order_by('-start_time')
    serializer = ElectionListSerializer(elections, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_election_detail(request, election_id):
    """GET /api/elections/<id>/"""
    election = get_object_or_404(
        Election.objects.prefetch_related('candidates'),
        id=election_id
    )
    serializer = ElectionSerializer(election)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_cast_vote(request, election_id):
    """POST /api/elections/<id>/vote/"""
    election = get_object_or_404(Election, id=election_id)

    identity = request.data.get("aadhaar")
    if not identity:
        return Response({'error': 'ID (aadhaar) is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if not validate_voter_id(identity):
        return Response({'error': 'Invalid Voter ID: Must be exactly 10 alphanumeric characters.'}, status=status.HTTP_400_BAD_REQUEST)

    voter_hash = hash_identity(identity)

    candidate_id = request.data.get("candidate_id")
    if not candidate_id:
        return Response({'error': 'candidate_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    with transaction.atomic():
        # 1. Acquire Candidate row lock before checking election status
        candidate = (
            Candidate.objects
            .select_for_update()
            .select_related('election')
            .filter(id=candidate_id, election=election)
            .first()
        )
        if not candidate:
            return Response({'error': 'Invalid candidate for this election.'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Revalidate election status only after acquiring candidate lock
        if not candidate.election.is_active:
            return Response({'error': f'Election is {candidate.election.status}. Voting is not open.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Duplicate check inside transaction
        if Vote.objects.filter(election=candidate.election, voter_hash=voter_hash).exists():
            return Response({'error': 'You have already voted with this ID.'}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Encrypt vote
        encrypted = encrypt_vote(candidate.id)

        # 5. 💾 Save vote - The Vote model's save() method automatically handles the Blockchain math!
        vote = Vote.objects.create(
            election=candidate.election,
            encrypted_vote=encrypted,
            voter_hash=voter_hash,
            voter_ip=ip
        )

    # Invalidate landing cache
    cache.delete('home_landing_context')

    return Response({
        'message': 'Vote cast securely on blockchain.',
        'block_hash': vote.block_hash,
        'election': election.title
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_results(request, election_id):
    """GET /api/elections/<id>/results/ (Optimized single-query vote verification)."""
    election = get_object_or_404(
        Election.objects.prefetch_related('candidates'),
        id=election_id
    )

    if election.status != "ended":
        return Response({"message": "Results are locked until election ends"})

    votes = list(Vote.objects.filter(election=election).order_by('id'))

    # 🔗 API BLOCKCHAIN VERIFICATION
    is_valid, bc_message = verify_election_blockchain(election, votes=votes)
    if not is_valid:
        return Response({
            "error": "Blockchain Verification Failed",
            "details": bc_message
        }, status=status.HTTP_409_CONFLICT)

    vote_count = {}
    for vote in votes:
        try:
            candidate_id = decrypt_vote(vote.encrypted_vote)
            vote_count[int(candidate_id)] = vote_count.get(int(candidate_id), 0) + 1
        except Exception:
            pass

    results = []
    for c in election.candidates.all():
        results.append({
            "candidate_id": c.id,
            "name": c.name,
            "votes": vote_count.get(c.id, 0)
        })

    results.sort(key=lambda x: x["votes"], reverse=True)

    return Response({
        "election": election.title,
        "blockchain_status": "Secure",
        "total_votes": len(votes),
        "results": results
    })


@admin_required
def threat_dashboard(request):
    """SOC Admin view to monitor active threats. Restricted server-side to staff and admin users."""
    logs = SecurityLog.objects.only('id', 'level', 'action', 'ip_address', 'details', 'timestamp').all()[:50]
    critical_count = SecurityLog.objects.filter(level='CRITICAL').count()

    return render(request, 'voting/threat_dashboard.html', {
        'logs': logs,
        'critical_count': critical_count
    })




@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_cron_add_candidate(request):
    """
    Secure backend endpoint to automatically generate a new candidate every 6 days.
    Triggered daily via Vercel Cron.
    Protected by CRON_SECRET environment variable.
    """
    expected_secret = os.environ.get('CRON_SECRET')
    if not expected_secret:
        return Response(
            {'error': 'Unauthorized: Server CRON_SECRET is not configured.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    auth_header = request.headers.get('Authorization', '')
    token = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
    elif 'X-Cron-Secret' in request.headers:
        token = request.headers.get('X-Cron-Secret', '').strip()
    elif 'secret' in request.GET:
        token = request.GET.get('secret', '').strip()

    if not token or not hmac.compare_digest(token, expected_secret):
        return Response(
            {'error': 'Unauthorized: Invalid or missing CRON_SECRET.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    force = (
        request.GET.get('force', '').lower() in ('true', '1') or
        (isinstance(request.data, dict) and request.data.get('force') in (True, 'true', '1'))
    )

    result = execute_candidate_automation(force=force)
    http_status = status.HTTP_200_OK if result.get('status') in ('success', 'skipped') else status.HTTP_500_INTERNAL_SERVER_ERROR
    return Response(result, status=http_status)


# ─────────────────────────────────────────────
# ADMIN MANAGEMENT VIEWS (/manage/)
# ─────────────────────────────────────────────

@admin_required
def manage_dashboard(request):
    """Admin dashboard listing all elections and metrics."""
    elections = list(Election.objects.prefetch_related('candidates').all().order_by('-start_time'))
    
    # Compute counts and attached vote numbers
    total_elections = len(elections)
    active_elections = 0
    completed_elections = 0
    total_candidates = 0

    for e in elections:
        e.vote_count = Vote.objects.filter(election=e).count()
        total_candidates += e.candidates.count()
        if e.status == 'active':
            active_elections += 1
        elif e.status == 'ended':
            completed_elections += 1

    return render(request, 'voting/manage/dashboard.html', {
        'elections': elections,
        'total_elections': total_elections,
        'active_elections': active_elections,
        'completed_elections': completed_elections,
        'total_candidates': total_candidates,
    })


@admin_required
def manage_election_create(request):
    """Admin view to create a new election."""
    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            election = form.save()
            cache.delete('home_landing_context')
            messages.success(request, f"Election '{election.title}' was successfully created.")
            return redirect('manage_dashboard')
    else:
        form = ElectionForm()

    return render(request, 'voting/manage/election_form.html', {
        'form': form,
        'title': 'Create New Election',
        'action': 'create',
    })


@admin_required
def manage_election_edit(request, election_id):
    """Admin view to edit an existing election."""
    election = get_object_or_404(Election, id=election_id)
    if request.method == 'POST':
        form = ElectionForm(request.POST, instance=election)
        if form.is_valid():
            form.save()
            cache.delete('home_landing_context')
            messages.success(request, f"Election '{election.title}' was successfully updated.")
            return redirect('manage_dashboard')
    else:
        form = ElectionForm(instance=election)

    return render(request, 'voting/manage/election_form.html', {
        'form': form,
        'election': election,
        'title': f"Edit Election: {election.title}",
        'action': 'edit',
    })


@admin_required
def manage_election_candidates(request, election_id):
    """Admin view to list and manage candidates for a specific election."""
    election = get_object_or_404(Election, id=election_id)
    candidates = list(election.candidates.all())

    for c in candidates:
        c.has_votes = candidate_has_recorded_votes(c)

    return render(request, 'voting/manage/candidates.html', {
        'election': election,
        'candidates': candidates,
    })


@admin_required
def manage_candidate_create(request, election_id):
    """Admin view to add a candidate to an election."""
    election = get_object_or_404(Election, id=election_id)
    if request.method == 'POST':
        form = CandidateForm(request.POST, election=election)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.election = election
            candidate.save()
            cache.delete('home_landing_context')
            messages.success(request, f"Candidate '{candidate.name}' was successfully added to '{election.title}'.")
            return redirect('manage_election_candidates', election_id=election.id)
    else:
        form = CandidateForm(election=election)

    return render(request, 'voting/manage/candidate_form.html', {
        'form': form,
        'election': election,
        'title': f"Add Candidate — {election.title}",
    })


@admin_required
def manage_candidate_edit(request, candidate_id):
    """Admin view to edit candidate information."""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    election = candidate.election
    if request.method == 'POST':
        form = CandidateForm(request.POST, instance=candidate, election=election)
        if form.is_valid():
            form.save()
            cache.delete('home_landing_context')
            messages.success(request, f"Candidate '{candidate.name}' was successfully updated.")
            return redirect('manage_election_candidates', election_id=election.id)
    else:
        form = CandidateForm(instance=candidate, election=election)

    return render(request, 'voting/manage/candidate_form.html', {
        'form': form,
        'election': election,
        'candidate': candidate,
        'title': f"Edit Candidate: {candidate.name}",
    })


@admin_required
def manage_candidate_delete(request, candidate_id):
    """
    Admin view to safely delete a candidate only if:
    1. The election status is strictly 'upcoming' (candidates cannot be deleted once active or ended).
    2. NO votes have been cast for that candidate (verified fail-closed).
    Server-side blocked if votes exist on the blockchain ledger or election is active/ended.
    """
    candidate = get_object_or_404(Candidate, id=candidate_id)
    election_id = candidate.election_id

    # 1. Pre-flight user feedback check (actual enforcement is inside the POST transaction under lock)
    if candidate.election.status != 'upcoming':
        messages.error(
            request,
            f"Security Alert: Cannot delete candidate '{candidate.name}'. Candidates can only be modified before voting opens (while election status is upcoming). Deletion is prohibited while an election is actively ongoing or concluded."
        )
        return redirect('manage_election_candidates', election_id=election_id)

    # 2. Pre-flight safety check against recorded votes
    if candidate_has_recorded_votes(candidate):
        messages.error(
            request,
            f"Security Alert: Cannot delete candidate '{candidate.name}' because votes have already been recorded for this candidate on the blockchain ledger."
        )
        return redirect('manage_election_candidates', election_id=election_id)

    if request.method == 'POST':
        with transaction.atomic():
            cand_locked = (
                Candidate.objects
                .select_for_update()
                .select_related('election')
                .filter(id=candidate_id)
                .first()
            )
            if not cand_locked:
                messages.error(request, "Candidate no longer exists.")
                return redirect('manage_election_candidates', election_id=election_id)

            # Strict enforcement under row lock: must be strictly 'upcoming'
            if cand_locked.election.status != 'upcoming':
                messages.error(
                    request,
                    f"Security Alert: Cannot delete candidate '{cand_locked.name}'. Candidates can only be deleted before voting opens (while election status is upcoming). Deletion is prohibited while an election is actively ongoing or concluded."
                )
                return redirect('manage_election_candidates', election_id=election_id)

            # Fail-closed recorded vote check under lock
            if candidate_has_recorded_votes(cand_locked):
                messages.error(
                    request,
                    f"Security Alert: Cannot delete candidate '{cand_locked.name}' because votes have already been recorded for this candidate on the blockchain ledger."
                )
                return redirect('manage_election_candidates', election_id=election_id)

            name = cand_locked.name
            election_title = cand_locked.election.title
            cand_locked.delete()
            cache.delete('home_landing_context')
            messages.success(request, f"Candidate '{name}' was successfully removed from '{election_title}'.")
            return redirect('manage_election_candidates', election_id=election_id)

    return render(request, 'voting/manage/candidate_confirm_delete.html', {
        'candidate': candidate,
    })

