from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Election, Candidate, Vote
from .serializers import ElectionSerializer, ElectionListSerializer, VoteSerializer
import hashlib
from .utils.encryption import encrypt_vote, decrypt_vote
from .utils.blockchain import verify_election_blockchain


# ─────────────────────────────────────────────
# FRONTEND VIEWS
# ─────────────────────────────────────────────

def home(request):
    """Landing page — list all elections with their status."""
    elections = Election.objects.prefetch_related('candidates', 'votes').all()

    active = [e for e in elections if e.status == 'active']
    upcoming = [e for e in elections if e.status == 'upcoming']
    ended = [e for e in elections if e.status == 'ended']

    voted_election_ids = set()
    # If you want to track which ones the logged-in user voted in, you can add that logic here.

    return render(request, 'voting/home.html', {
        'active_elections': active,
        'upcoming_elections': upcoming,
        'ended_elections': ended,
        'voted_election_ids': voted_election_ids,
    })


@login_required
def election_detail(request, election_id):
    """Single election page with voting form."""
    election = get_object_or_404(Election, id=election_id)
    candidates = election.candidates.all()
    user_vote = None

    return render(request, 'voting/election_detail.html', {
        'election': election,
        'candidates': candidates,
        'user_vote': user_vote,
    })


def hash_identity(identity):
    return hashlib.sha256(identity.encode()).hexdigest()


@login_required
def cast_vote(request, election_id):
    """Handle vote form submission from the frontend."""
    if request.method != "POST":
        return redirect('election_detail', election_id=election_id)

    election = get_object_or_404(Election, id=election_id)

    # 🚫 Election must be active
    if not election.is_active:
        messages.error(request, f"This election is {election.status}. Voting is not allowed.")
        return redirect('election_detail', election_id=election_id)

    # 🧾 Get ID (Aadhaar/College ID)
    identity = request.POST.get("aadhaar")
    if not identity:
        messages.error(request, "ID is required")
        return redirect('election_detail', election_id=election_id)

    # 🔐 Hash identity
    voter_hash = hash_identity(identity)

    # 🚫 Prevent duplicate voting
    if Vote.objects.filter(election=election, voter_hash=voter_hash).exists():
        messages.error(request, "You have already voted with this ID")
        return redirect('election_detail', election_id=election_id)

    # 🗳 Get candidate
    candidate_id = request.POST.get("candidate_id")
    if not candidate_id:
        messages.error(request, "Please select a candidate")
        return redirect('election_detail', election_id=election_id)

    candidate = get_object_or_404(Candidate, id=candidate_id, election=election)

    # 🌐 Get IP
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    # 🔐 Encrypt vote
    encrypted = encrypt_vote(candidate.id)

    # 💾 Save vote - The Vote model's save() method automatically handles the Blockchain math!
    Vote.objects.create(
        election=election,
        encrypted_vote=encrypted,
        voter_hash=voter_hash,
        voter_ip=ip
    )

    messages.success(request, "Your vote has been securely recorded on the blockchain!")
    return redirect('election_detail', election_id=election_id)


def results_view(request, election_id):
    """Show election results (Only if ended and blockchain is valid)."""
    election = get_object_or_404(Election, id=election_id)

    # 🚫 BLOCK RESULTS BEFORE END
    if election.status != 'ended':
        return render(request, 'voting/results.html', {
            'election': election,
            'candidates': [],
            'message': "Results are locked until election ends"
        })

    # 🔗 VERIFY BLOCKCHAIN BEFORE SHOWING RESULTS
    is_valid, bc_message = verify_election_blockchain(election)
    if not is_valid:
        return render(request, 'voting/results.html', {
            'election': election,
            'candidates': [],
            'message': f"🚨 SECURITY ALERT: {bc_message} Results cannot be verified."
        })

    votes = election.votes.all()
    vote_count = {}

    for vote in votes:
        try:
            candidate_id = decrypt_vote(vote.encrypted_vote)
            # Ensure type matches depending on how decrypt_vote returns the ID
            vote_count[int(candidate_id)] = vote_count.get(int(candidate_id), 0) + 1
        except Exception:
            pass # Skip corrupted decryption

    candidates = election.candidates.all()
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
    # Get all votes in chronological order to visualize the chain
    votes = Vote.objects.filter(election=election).order_by('id')
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
    """GET /api/elections/"""
    elections = Election.objects.prefetch_related('candidates', 'votes').all()
    serializer = ElectionListSerializer(elections, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_election_detail(request, election_id):
    """GET /api/elections/<id>/"""
    election = get_object_or_404(Election, id=election_id)
    serializer = ElectionSerializer(election)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_cast_vote(request, election_id):
    """POST /api/elections/<id>/vote/"""
    election = get_object_or_404(Election, id=election_id)

    if not election.is_active:
        return Response({'error': f'Election is {election.status}. Voting is not open.'}, status=status.HTTP_400_BAD_REQUEST)

    identity = request.data.get("aadhaar")
    if not identity:
        return Response({'error': 'ID (aadhaar) is required.'}, status=status.HTTP_400_BAD_REQUEST)

    voter_hash = hashlib.sha256(identity.encode()).hexdigest()

    if Vote.objects.filter(election=election, voter_hash=voter_hash).exists():
        return Response({'error': 'You have already voted with this ID.'}, status=status.HTTP_400_BAD_REQUEST)

    candidate_id = request.data.get("candidate_id")
    if not candidate_id:
        return Response({'error': 'candidate_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    candidate = Candidate.objects.filter(id=candidate_id, election=election).first()
    if not candidate:
        return Response({'error': 'Invalid candidate for this election.'}, status=status.HTTP_400_BAD_REQUEST)

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    encrypted = encrypt_vote(candidate.id)

    # 💾 Save vote - The Vote model's save() method automatically handles the Blockchain math!
    vote = Vote.objects.create(
        election=election,
        encrypted_vote=encrypted,
        voter_hash=voter_hash,
        voter_ip=ip
    )

    return Response({
        'message': 'Vote cast securely on blockchain.',
        'block_hash': vote.block_hash,
        'election': election.title
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_results(request, election_id):
    """GET /api/elections/<id>/results/"""
    election = get_object_or_404(Election, id=election_id)

    if election.status != "ended":
        return Response({"message": "Results are locked until election ends"})

    # 🔗 API BLOCKCHAIN VERIFICATION
    is_valid, bc_message = verify_election_blockchain(election)
    if not is_valid:
        return Response({
            "error": "Blockchain Verification Failed",
            "details": bc_message
        }, status=status.HTTP_409_CONFLICT)

    votes = election.votes.all()
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
        "total_votes": election.total_votes,
        "results": results
    })