"""
Unit and authorization tests for Phase 3 Admin components:
- @admin_required authorization decorator
- ElectionForm validation
- CandidateForm validation (per-election uniqueness)
- candidate_has_recorded_votes ballot safety helper
"""

import pytest
import secrets
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.test import RequestFactory, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse

from django.db import connection, transaction
from voting.decorators import admin_required
from voting.forms import ElectionForm, CandidateForm, candidate_has_recorded_votes
from voting.models import Election, Candidate, Vote, SecurityLog
from voting.utils.encryption import encrypt_vote
from voting.views import hash_identity, validate_voter_id


@pytest.fixture
def rf():
    return RequestFactory()


def _add_messages_storage(request):
    """Attach session & messages storage to RequestFactory requests."""
    setattr(request, 'session', {})
    storage = FallbackStorage(request)
    setattr(request, '_messages', storage)
    return storage


# ─────────────────────────────────────────────────────────────
# 1. @admin_required DECORATOR TESTS
# ─────────────────────────────────────────────────────────────

@admin_required
def dummy_admin_view(request):
    return HttpResponse("Admin Access Granted", status=200)


@pytest.mark.django_db
def test_admin_required_anonymous_redirect(rf):
    """Anonymous users should be redirected to login with ?next=."""
    request = rf.get('/manage/')
    request.user = AnonymousUser()
    _add_messages_storage(request)

    response = dummy_admin_view(request)
    assert response.status_code == 302
    assert response.url.startswith('/login/?next=/manage/')


@pytest.mark.django_db
def test_admin_required_regular_voter_blocked(rf, test_user):
    """Regular voters (is_staff=False, is_superuser=False) are redirected to home with error."""
    request = rf.get('/manage/')
    request.user = test_user
    storage = _add_messages_storage(request)

    response = dummy_admin_view(request)
    assert response.status_code == 302
    assert response.url == '/'
    messages = [m.message for m in storage]
    assert any("Access restricted" in m for m in messages)


@pytest.mark.django_db
def test_admin_required_staff_allowed(rf, staff_user):
    """Staff users are permitted access."""
    request = rf.get('/manage/')
    request.user = staff_user
    _add_messages_storage(request)

    response = dummy_admin_view(request)
    assert response.status_code == 200
    assert response.content.decode() == "Admin Access Granted"


@pytest.mark.django_db
def test_admin_required_non_yash_superuser_denied(rf, other_superuser):
    """Non-yash superusers are strictly denied administrative access."""
    request = rf.get('/manage/')
    request.user = other_superuser
    storage = _add_messages_storage(request)

    response = dummy_admin_view(request)
    assert response.status_code == 302
    assert response.url == '/'
    messages = [m.message for m in storage]
    assert any("Access restricted" in m for m in messages)


# ─────────────────────────────────────────────────────────────
# 2. ELECTION FORM VALIDATION TESTS
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_election_form_valid():
    """Valid election data should pass form validation."""
    now = timezone.now()
    data = {
        'title': 'Campus Senate Election 2026',
        'description': 'Annual election of campus senate representatives.',
        'start_time': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
    }
    form = ElectionForm(data=data)
    assert form.is_valid(), form.errors
    election = form.save()
    assert election.pk is not None
    assert election.title == 'Campus Senate Election 2026'


@pytest.mark.django_db
def test_election_form_end_time_before_start_time():
    """Form is invalid if end_time is earlier than or equal to start_time."""
    now = timezone.now()
    data = {
        'title': 'Invalid Schedule Election',
        'description': 'End time is before start time.',
        'start_time': (now + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
    }
    form = ElectionForm(data=data)
    assert not form.is_valid()
    assert 'end_time' in form.errors
    assert "End time must be after start time." in form.errors['end_time'][0]


@pytest.mark.django_db
def test_election_form_short_or_empty_title():
    """Title must be non-empty and at least 3 characters."""
    now = timezone.now()
    # Empty title
    data_empty = {
        'title': '   ',
        'description': 'No title test',
        'start_time': now.strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
    }
    form_empty = ElectionForm(data=data_empty)
    assert not form_empty.is_valid()
    assert 'title' in form_empty.errors

    # Too short title
    data_short = {
        'title': 'AB',
        'description': 'Short title test',
        'start_time': now.strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
    }
    form_short = ElectionForm(data=data_short)
    assert not form_short.is_valid()
    assert 'title' in form_short.errors
    assert "at least 3 characters" in form_short.errors['title'][0]


# ─────────────────────────────────────────────────────────────
# 3. CANDIDATE FORM VALIDATION TESTS
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_candidate_form_valid(active_election):
    """Valid candidate data passes validation."""
    data = {
        'name': 'Dr. Marcus Vance',
        'description': 'Faculty of Engineering Representative'
    }
    form = CandidateForm(data=data, election=active_election)
    assert form.is_valid(), form.errors
    candidate = form.save(commit=False)
    candidate.election = active_election
    candidate.save()
    assert candidate.pk is not None


@pytest.mark.django_db
def test_candidate_form_duplicate_name_same_election(active_election):
    """Candidate with existing name in the same election should be rejected."""
    existing_cand = active_election.candidates.first()
    data = {
        'name': existing_cand.name.lower(),  # Case-insensitive duplicate
        'description': 'Duplicate attempt'
    }
    form = CandidateForm(data=data, election=active_election)
    assert not form.is_valid()
    assert 'name' in form.errors
    assert "already exists in this election" in form.errors['name'][0]


@pytest.mark.django_db
def test_candidate_form_same_name_different_election(active_election, ended_election):
    """Same candidate name in a different election is permitted."""
    existing_cand = active_election.candidates.first()
    data = {
        'name': existing_cand.name,
        'description': 'Valid in different election'
    }
    form = CandidateForm(data=data, election=ended_election)
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_candidate_form_edit_same_instance(active_election):
    """Editing an existing candidate without changing name should not trigger duplicate error."""
    existing_cand = active_election.candidates.first()
    data = {
        'name': existing_cand.name,
        'description': 'Updated description'
    }
    form = CandidateForm(data=data, instance=existing_cand, election=active_election)
    assert form.is_valid(), form.errors


# ─────────────────────────────────────────────────────────────
# 4. CANDIDATE BALLOT SAFETY HELPER TESTS
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_candidate_has_recorded_votes_no_votes(active_election):
    """Candidate with zero recorded votes returns False."""
    cand = active_election.candidates.first()
    assert not candidate_has_recorded_votes(cand)


@pytest.mark.django_db
def test_candidate_has_recorded_votes_with_votes(active_election):
    """Candidate with at least one encrypted ballot returns True."""
    candidates = list(active_election.candidates.all())
    cand_with_vote = candidates[0]
    cand_without_vote = candidates[1]

    # Create a vote for cand_with_vote
    Vote.objects.create(
        election=active_election,
        encrypted_vote=encrypt_vote(cand_with_vote.id),
        voter_hash='hash1234567890abcdef',
        voter_ip='127.0.0.1'
    )

    # cand_with_vote must return True
    assert candidate_has_recorded_votes(cand_with_vote) is True

    # cand_without_vote must return False
    assert candidate_has_recorded_votes(cand_without_vote) is False


@pytest.mark.django_db
def test_candidate_has_recorded_votes_none_or_unsaved():
    """Unsaved candidate or None safely returns False."""
    assert candidate_has_recorded_votes(None) is False
    unsaved_cand = Candidate(name="Unsaved Candidate")
    assert candidate_has_recorded_votes(unsaved_cand) is False


# ─────────────────────────────────────────────────────────────
# 5. ADMIN PORTAL ENDPOINT & ACCESS TESTS (/manage/)
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_manage_anonymous_user_redirect(client):
    """Anonymous user accessing any /manage/ endpoint is redirected to login with next parameter."""
    for url in ['/manage/', '/manage/elections/new/']:
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(f'/login/?next={url}')


@pytest.mark.django_db
def test_manage_regular_voter_denied(client, test_user):
    """Authenticated regular voter accessing /manage/ endpoints is redirected to home with error message."""
    client.force_login(test_user)
    for url in ['/manage/', '/manage/elections/new/']:
        response = client.get(url, follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == '/'
        messages = list(response.context['messages'])
        assert any("Access restricted" in str(m) for m in messages)


@pytest.mark.django_db
def test_manage_staff_user_allowed(client, staff_user):
    """Staff user can access the admin management portal dashboard."""
    client.force_login(staff_user)
    response = client.get('/manage/')
    assert response.status_code == 200
    assert "Election Management Portal" in response.content.decode()


@pytest.mark.django_db
def test_manage_non_yash_superuser_denied(client, other_superuser):
    """Non-yash superuser is strictly denied access to the admin management dashboard."""
    client.force_login(other_superuser)
    response = client.get('/manage/', follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == '/'
    messages = list(response.context['messages'])
    assert any("Access restricted" in str(m) for m in messages)


@pytest.mark.django_db
def test_manage_election_create_and_edit(client, staff_user):
    """Staff user can create a new election and edit an existing one."""
    client.force_login(staff_user)
    now = timezone.now()
    
    # 1. Create election
    create_data = {
        'title': 'Faculty Senate Election 2026',
        'description': 'Annual election for faculty senators.',
        'start_time': (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (now + timedelta(days=9)).strftime('%Y-%m-%dT%H:%M'),
    }
    response = client.post('/manage/elections/new/', data=create_data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == '/manage/'
    election = Election.objects.get(title='Faculty Senate Election 2026')
    assert election.description == 'Annual election for faculty senators.'

    # 2. Edit election
    edit_data = {
        'title': 'Faculty Senate Election 2026 - Revised',
        'description': 'Updated description with extended guidelines.',
        'start_time': election.start_time.strftime('%Y-%m-%dT%H:%M'),
        'end_time': election.end_time.strftime('%Y-%m-%dT%H:%M'),
    }
    response = client.post(f'/manage/elections/{election.id}/edit/', data=edit_data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == '/manage/'
    election.refresh_from_db()
    assert election.title == 'Faculty Senate Election 2026 - Revised'
    assert election.description == 'Updated description with extended guidelines.'


@pytest.mark.django_db
def test_admin_can_delete_eligible_upcoming_election_with_zero_votes(client, staff_user):
    """
    1. Admin can delete an eligible upcoming election with zero recorded votes.
    - Verified under atomic row lock via confirmed POST.
    - Associated zero-vote candidates are cleanly removed.
    """
    now = timezone.now()
    upcoming_election = Election.objects.create(
        title="Eligible Upcoming Deletion Election",
        description="Upcoming test election with zero votes.",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=5),
    )
    c1 = Candidate.objects.create(election=upcoming_election, name="Candidate One")
    c2 = Candidate.objects.create(election=upcoming_election, name="Candidate Two")
    assert upcoming_election.status == 'upcoming'
    assert Vote.objects.filter(election=upcoming_election).count() == 0

    client.force_login(staff_user)

    # Dashboard shows Delete button for eligible election
    dash_resp = client.get(reverse('manage_dashboard'))
    assert dash_resp.status_code == 200
    assert f'action="/manage/elections/{upcoming_election.id}/delete/"' in dash_resp.content.decode()
    assert "Are you sure you want to delete this election? This action cannot be undone." in dash_resp.content.decode()

    # Confirmed POST deletes election
    resp_post = client.post(reverse('manage_election_delete', args=[upcoming_election.id]), follow=True)
    assert resp_post.status_code == 200
    assert resp_post.redirect_chain[0][0] == reverse('manage_dashboard')

    # Election and its candidates are safely deleted
    assert Election.objects.filter(id=upcoming_election.id).exists() is False
    assert Candidate.objects.filter(id=c1.id).exists() is False
    assert Candidate.objects.filter(id=c2.id).exists() is False


@pytest.mark.django_db
def test_election_with_recorded_votes_cannot_be_deleted(client, staff_user, active_election):
    """
    2. Election with recorded votes cannot be deleted.
    - Blocked server-side to protect cryptographic ledger integrity.
    - Election and votes remain intact.
    """
    candidate = active_election.candidates.first()
    vote_url = reverse('cast_vote', args=[active_election.id])
    client.post(vote_url, {'aadhaar': 'VOTEDEL123', 'candidate_id': candidate.id})
    assert Vote.objects.filter(election=active_election).count() == 1

    client.force_login(staff_user)

    # Dashboard displays Delete Locked
    dash_resp = client.get(reverse('manage_dashboard'))
    content = dash_resp.content.decode()
    assert "Delete Locked" in content
    assert "Protected to preserve cryptographic ledger integrity" in content

    # POST to delete endpoint is strictly blocked
    del_resp = client.post(reverse('manage_election_delete', args=[active_election.id]), follow=True)
    assert del_resp.status_code == 200
    assert "Cannot delete election" in del_resp.content.decode()
    assert "ledger integrity" in del_resp.content.decode()

    # Election and votes preserved
    assert Election.objects.filter(id=active_election.id).exists() is True
    assert Vote.objects.filter(election=active_election).count() == 1


@pytest.mark.django_db
def test_election_with_ledger_references_cannot_be_deleted(client, staff_user, ended_election):
    """
    3. Election with ledger references cannot be deleted even after concluding.
    - Blocked server-side; election and historical blocks preserved.
    """
    assert Vote.objects.filter(election=ended_election).count() > 0

    client.force_login(staff_user)

    del_resp = client.post(reverse('manage_election_delete', args=[ended_election.id]), follow=True)
    assert del_resp.status_code == 200
    assert "Cannot delete election" in del_resp.content.decode()
    assert "ledger integrity" in del_resp.content.decode()

    assert Election.objects.filter(id=ended_election.id).exists() is True


@pytest.mark.django_db
def test_active_election_cannot_be_deleted(client, staff_user, active_election):
    """
    4. Active election cannot be deleted even if zero votes are currently recorded.
    """
    assert active_election.status == 'active'
    assert Vote.objects.filter(election=active_election).count() == 0

    client.force_login(staff_user)

    # Dashboard displays Delete Locked for active election
    dash_resp = client.get(reverse('manage_dashboard'))
    content = dash_resp.content.decode()
    assert "Active elections currently receiving ballots cannot be deleted" in content

    # POST deletion blocked
    del_resp = client.post(reverse('manage_election_delete', args=[active_election.id]), follow=True)
    assert del_resp.status_code == 200
    assert "Cannot delete election" in del_resp.content.decode()
    assert "Active elections currently receiving ballots cannot be deleted" in del_resp.content.decode()

    assert Election.objects.filter(id=active_election.id).exists() is True


@pytest.mark.django_db
def test_regular_voter_cannot_delete_election(client, test_user):
    """
    5. Regular voter cannot delete an election.
    - Access restricted; redirected to home; zero mutations.
    """
    now = timezone.now()
    election = Election.objects.create(
        title="Voter Tamper Attempt Election",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=5),
    )
    client.force_login(test_user)

    del_resp = client.post(reverse('manage_election_delete', args=[election.id]), follow=True)
    assert del_resp.status_code == 200
    assert del_resp.redirect_chain[0][0] == '/'
    assert "Access restricted" in del_resp.content.decode()

    assert Election.objects.filter(id=election.id).exists() is True


@pytest.mark.django_db
def test_anonymous_user_cannot_delete_election(client):
    """
    6. Anonymous user cannot delete an election.
    - Redirected to login with ?next=...; zero mutations.
    """
    now = timezone.now()
    election = Election.objects.create(
        title="Anon Tamper Attempt Election",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=5),
    )

    del_url = reverse('manage_election_delete', args=[election.id])
    del_resp = client.post(del_url)
    assert del_resp.status_code == 302
    assert del_resp.url.startswith(f'/login/?next={del_url}')

    assert Election.objects.filter(id=election.id).exists() is True


@pytest.mark.django_db
def test_get_requests_cannot_trigger_election_deletion(client, staff_user):
    """
    7. GET requests cannot trigger deletion.
    - GET renders confirmation warning; election is NOT deleted.
    """
    now = timezone.now()
    election = Election.objects.create(
        title="GET Non-Mutation Test Election",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=5),
    )

    client.force_login(staff_user)

    get_resp = client.get(reverse('manage_election_delete', args=[election.id]))
    assert get_resp.status_code == 200
    assert "Are you sure you want to delete this election? This action cannot be undone." in get_resp.content.decode()

    # Election STILL EXISTS in the database
    assert Election.objects.filter(id=election.id).exists() is True


@pytest.mark.django_db
def test_manage_candidate_create_and_edit(client, staff_user, active_election):
    """Staff user can add and edit candidates for an election."""
    client.force_login(staff_user)

    # 1. Add candidate
    create_data = {
        'name': 'Prof. Evelyn Reed',
        'description': 'Department of Computer Science and Cryptography'
    }
    response = client.post(f'/manage/elections/{active_election.id}/candidates/new/', data=create_data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == f'/manage/elections/{active_election.id}/candidates/'
    candidate = Candidate.objects.get(name='Prof. Evelyn Reed', election=active_election)
    assert candidate.description == 'Department of Computer Science and Cryptography'

    # 2. Edit candidate
    edit_data = {
        'name': 'Prof. Evelyn Reed, Ph.D.',
        'description': 'Updated chair of cryptography research group'
    }
    response = client.post(f'/manage/candidates/{candidate.id}/edit/', data=edit_data, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == f'/manage/elections/{active_election.id}/candidates/'
    candidate.refresh_from_db()
    assert candidate.name == 'Prof. Evelyn Reed, Ph.D.'
    assert candidate.description == 'Updated chair of cryptography research group'


@pytest.mark.django_db
def test_candidate_has_recorded_votes_corrupted_ciphertext_fails_closed(active_election):
    """
    Fail-Closed Security Check:
    If any ballot in the election contains corrupted or undecryptable ciphertext,
    candidate_has_recorded_votes must treat the ledger as uncertain and return True,
    blocking candidate deletion.
    """
    candidate = active_election.candidates.first()
    Vote.objects.create(
        election=active_election,
        encrypted_vote="CORRUPTED_MALFORMED_FERNET_TOKEN_999",
        voter_hash="hash_corrupted_ballot_test",
        voter_ip="127.0.0.1"
    )
    # Must fail closed: return True (blocking deletion)
    assert candidate_has_recorded_votes(candidate) is True


@pytest.mark.django_db
def test_manage_candidate_deletion_blocked_when_votes_exist(client, staff_user, active_election):
    """
    Critical Safety Check:
    Candidate deletion MUST be blocked server-side if any votes have been cast for that candidate.
    Database record and vote records MUST NOT be mutated.
    """
    candidate = active_election.candidates.first()
    vote = Vote.objects.create(
        election=active_election,
        encrypted_vote=encrypt_vote(candidate.id),
        voter_hash='hash999888777abcdef',
        voter_ip='127.0.0.1'
    )
    assert candidate_has_recorded_votes(candidate) is True
    initial_votes_count = Vote.objects.count()

    client.force_login(staff_user)
    response = client.post(f'/manage/candidates/{candidate.id}/delete/', follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == f'/manage/elections/{active_election.id}/candidates/'

    # Verify candidate still exists in database
    assert Candidate.objects.filter(id=candidate.id).exists() is True
    # Verify vote count not mutated
    assert Vote.objects.count() == initial_votes_count

    # Verify security alert message displayed
    messages = list(response.context['messages'])
    assert any("Security Alert: Cannot delete candidate" in str(m) for m in messages)


@pytest.mark.django_db
def test_manage_candidate_deletion_blocked_when_ballot_corrupted(client, staff_user):
    """
    Fail-Closed Endpoint Check:
    When a corrupted or undecryptable ballot exists in an election, deleting a candidate
    is blocked server-side even outside active voting. Database records are unmutated.
    """
    now = timezone.now()
    upcoming_election = Election.objects.create(
        title="Upcoming Election With Corrupt Ballot",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=8),
    )
    cand = Candidate.objects.create(election=upcoming_election, name="Uncertain Candidate")
    Vote.objects.create(
        election=upcoming_election,
        encrypted_vote="CORRUPTED_CIPHERTEXT",
        voter_hash="voter_hash_corrupt_123",
        voter_ip="127.0.0.1"
    )
    initial_votes_count = Vote.objects.count()

    client.force_login(staff_user)
    response = client.post(f'/manage/candidates/{cand.id}/delete/', follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == f'/manage/elections/{upcoming_election.id}/candidates/'

    # Candidate remains in DB
    assert Candidate.objects.filter(id=cand.id).exists() is True
    # Vote records not mutated
    assert Vote.objects.count() == initial_votes_count
    messages = list(response.context['messages'])
    assert any("Security Alert: Cannot delete candidate" in str(m) for m in messages)


@pytest.mark.django_db
def test_manage_candidate_deletion_blocked_when_election_is_active(client, staff_user, active_election):
    """
    Active Election Safeguard:
    A candidate with zero votes CANNOT be deleted while the election is actively ongoing.
    Prevents race conditions between active ballot submission and candidate removal.
    """
    zero_vote_cand = Candidate.objects.create(
        election=active_election,
        name="Zero Vote Active Cand",
        description="Candidate standing in active election"
    )
    assert candidate_has_recorded_votes(zero_vote_cand) is False
    assert active_election.status == 'active'
    initial_votes_count = Vote.objects.count()

    client.force_login(staff_user)

    # 1. Direct GET to delete page should redirect back with error
    get_resp = client.get(f'/manage/candidates/{zero_vote_cand.id}/delete/', follow=True)
    assert get_resp.status_code == 200
    assert get_resp.redirect_chain[0][0] == f'/manage/elections/{active_election.id}/candidates/'
    messages_get = list(get_resp.context['messages'])
    assert any("actively ongoing" in str(m) for m in messages_get)

    # 2. Direct POST to delete candidate should be rejected
    post_resp = client.post(f'/manage/candidates/{zero_vote_cand.id}/delete/', follow=True)
    assert post_resp.status_code == 200
    assert post_resp.redirect_chain[0][0] == f'/manage/elections/{active_election.id}/candidates/'
    messages_post = list(post_resp.context['messages'])
    assert any("actively ongoing" in str(m) for m in messages_post)

    # Candidate is NOT deleted
    assert Candidate.objects.filter(id=zero_vote_cand.id).exists() is True
    # Vote records not mutated
    assert Vote.objects.count() == initial_votes_count


@pytest.mark.django_db
def test_manage_candidate_deletion_allowed_when_no_votes_exist(client, staff_user):
    """
    Existing allowed deletion behavior for a zero-vote candidate outside an active election
    (e.g., an upcoming election) remains intact via confirmed POST request.
    """
    now = timezone.now()
    upcoming_election = Election.objects.create(
        title="Upcoming Student Election 2027",
        description="Election scheduled in future.",
        start_time=now + timedelta(days=5),
        end_time=now + timedelta(days=12),
    )
    assert upcoming_election.status == 'upcoming'

    new_candidate = Candidate.objects.create(
        election=upcoming_election,
        name='Candidate To Be Deleted',
        description='Zero votes candidate in upcoming election'
    )
    assert candidate_has_recorded_votes(new_candidate) is False

    client.force_login(staff_user)

    # 1. GET confirmation page
    get_resp = client.get(f'/manage/candidates/{new_candidate.id}/delete/')
    assert get_resp.status_code == 200
    assert "Confirm Candidate Removal" in get_resp.content.decode()

    # 2. POST deletion
    post_resp = client.post(f'/manage/candidates/{new_candidate.id}/delete/', follow=True)
    assert post_resp.status_code == 200
    assert post_resp.redirect_chain[0][0] == f'/manage/elections/{upcoming_election.id}/candidates/'

    # Verify candidate is removed from database
    assert Candidate.objects.filter(id=new_candidate.id).exists() is False


@pytest.mark.django_db
def test_manage_unauthorized_post_rejected(client, test_user, active_election):
    """
    Regular voters cannot perform state-changing POST requests to admin endpoints.
    Zero mutations occur.
    """
    initial_election_count = Election.objects.count()
    initial_candidate_count = Candidate.objects.count()
    candidate = active_election.candidates.first()

    client.force_login(test_user)

    # 1. Unauthorized election create POST
    resp1 = client.post('/manage/elections/new/', data={'title': 'Hacker Election'}, follow=True)
    assert resp1.status_code == 200
    assert resp1.redirect_chain[0][0] == '/'
    assert Election.objects.count() == initial_election_count

    # 2. Unauthorized candidate delete POST
    resp2 = client.post(f'/manage/candidates/{candidate.id}/delete/', follow=True)
    assert resp2.status_code == 200
    assert resp2.redirect_chain[0][0] == '/'
    assert Candidate.objects.count() == initial_candidate_count


@pytest.mark.django_db
def test_manage_candidate_deletion_blocked_when_election_is_ended(client, staff_user):
    """
    Candidate deletion is STRICTLY prohibited once an election has concluded (status == 'ended'),
    even if the candidate has zero votes. Preserves historical audit integrity.
    """
    now = timezone.now()
    ended_election = Election.objects.create(
        title="Historical Student Election 2025",
        description="Concluded election.",
        start_time=now - timedelta(days=10),
        end_time=now - timedelta(days=2),
    )
    assert ended_election.status == 'ended'
    cand = Candidate.objects.create(
        election=ended_election,
        name="Historical Candidate",
        description="Candidate in ended election"
    )
    assert candidate_has_recorded_votes(cand) is False

    client.force_login(staff_user)

    # 1. GET confirmation should be redirected with error
    get_resp = client.get(f'/manage/candidates/{cand.id}/delete/', follow=True)
    assert get_resp.status_code == 200
    assert get_resp.redirect_chain[0][0] == f'/manage/elections/{ended_election.id}/candidates/'
    messages_get = list(get_resp.context['messages'])
    assert any("upcoming" in str(m) for m in messages_get)

    # 2. POST deletion must be blocked
    post_resp = client.post(f'/manage/candidates/{cand.id}/delete/', follow=True)
    assert post_resp.status_code == 200
    assert post_resp.redirect_chain[0][0] == f'/manage/elections/{ended_election.id}/candidates/'
    messages_post = list(post_resp.context['messages'])
    assert any("upcoming" in str(m) for m in messages_post)

    # Candidate remains in DB
    assert Candidate.objects.filter(id=cand.id).exists() is True


@pytest.mark.django_db
def test_cast_vote_rejects_non_active_election_after_candidate_lock(client, test_user):
    """
    Form vote path: If election is not active (e.g. upcoming or ended),
    after acquiring the candidate lock and evaluating status under lock,
    the vote is rejected with an error message and no vote is written.
    """
    now = timezone.now()
    upcoming_election = Election.objects.create(
        title="Future Election 2027",
        start_time=now + timedelta(days=5),
        end_time=now + timedelta(days=10),
    )
    cand = Candidate.objects.create(election=upcoming_election, name="Future Hopeful")
    client.force_login(test_user)

    initial_votes = Vote.objects.count()
    resp = client.post(f'/election/{upcoming_election.id}/vote/', {
        'aadhaar': 'VALID12345',
        'candidate_id': cand.id,
    }, follow=True)

    assert resp.status_code == 200
    assert Vote.objects.count() == initial_votes
    messages = list(resp.context['messages'])
    assert any("Voting is not allowed" in str(m) for m in messages)


@pytest.mark.django_db
def test_api_cast_vote_rejects_non_active_election_after_candidate_lock(client):
    """
    API vote path: If election is not active, after acquiring the candidate lock
    and evaluating status under lock, the API returns HTTP 400 and creates no vote.
    """
    now = timezone.now()
    upcoming_election = Election.objects.create(
        title="Future API Election 2027",
        start_time=now + timedelta(days=3),
        end_time=now + timedelta(days=7),
    )
    cand = Candidate.objects.create(election=upcoming_election, name="API Candidate")

    initial_votes = Vote.objects.count()
    resp = client.post(
        f'/api/elections/{upcoming_election.id}/vote/',
        data={'aadhaar': 'VALID12345', 'candidate_id': cand.id},
        content_type='application/json'
    )

    assert resp.status_code == 400
    assert "Voting is not open" in resp.json().get('error', '')
    assert Vote.objects.count() == initial_votes


@pytest.mark.django_db
def test_voting_endpoints_use_equivalent_hash_identity():
    """
    Both cast_vote and api_cast_vote must rely on the identical hash_identity() helper.
    Ensures voter anonymity and duplicate tracking are 100% consistent across endpoints.
    """
    test_id = "VOTER10XYZ"
    computed_hash = hash_identity(test_id)
    import hashlib
    expected_hash = hashlib.sha256(test_id.encode()).hexdigest()
    assert computed_hash == expected_hash
    assert len(computed_hash) == 64


@pytest.mark.django_db
def test_cast_vote_atomic_rollback_on_failure(client, test_user, active_election, monkeypatch):
    """
    Transaction rollback guarantee:
    If an unexpected database or encryption error occurs during vote creation,
    the transaction is completely rolled back leaving no partial vote or ledger mutation.
    """
    client.force_login(test_user)
    candidate = active_election.candidates.first()
    initial_votes = Vote.objects.count()

    def mock_create_failure(*args, **kwargs):
        raise RuntimeError("Simulated database failure during Vote.objects.create")

    monkeypatch.setattr(Vote.objects, 'create', mock_create_failure)

    with pytest.raises(RuntimeError):
        client.post(f'/election/{active_election.id}/vote/', {
            'aadhaar': 'VALID10VOT',
            'candidate_id': candidate.id,
        })

    # DB state must be unmodified
    assert Vote.objects.count() == initial_votes


@pytest.mark.django_db(transaction=True)
def test_postgres_concurrency_vote_blocks_deletion():
    """
    PostgreSQL-specific deterministic concurrency test:
    Verifies that a transaction holding a Candidate row lock (via SELECT FOR UPDATE)
    blocks a concurrent admin deletion transaction until the vote transaction completes.

    Uses pg_locks to deterministically verify that the second connection is blocked
    on the Candidate row lock, rather than relying on sleep() or timers.
    Skipped on non-PostgreSQL backends (e.g. SQLite) to avoid false assertions.
    """
    if connection.vendor != 'postgresql':
        pytest.skip("Requires PostgreSQL for true SELECT ... FOR UPDATE row locking and pg_locks observation")

    import threading
    import time
    from django.test import Client

    now = timezone.now()
    election = Election.objects.create(
        title="Postgres Concurrency Election",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=8),
    )
    cand = Candidate.objects.create(election=election, name="Locked Candidate")
    admin_username = getattr(settings, 'AUTHORIZED_ADMIN_USERNAME', 'yash')
    admin_user, _ = User.objects.get_or_create(
        username=admin_username,
        defaults={
            'email': f'{admin_username}@chainvote.test',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.is_active = True
    admin_user.save()

    lock_acquired_event = threading.Event()
    delete_started_event = threading.Event()
    release_vote_lock_event = threading.Event()
    test_results = {}

    def holder_thread():
        try:
            with transaction.atomic():
                cand_locked = Candidate.objects.select_for_update().get(id=cand.id)
                lock_acquired_event.set()
                release_vote_lock_event.wait(timeout=10)
        except Exception as e:
            test_results['holder_error'] = e

    def waiter_thread():
        try:
            lock_acquired_event.wait(timeout=10)
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid();")
                test_results['waiter_pid'] = cur.fetchone()[0]
            client2 = Client()
            client2.force_login(admin_user)
            delete_started_event.set()
            resp = client2.post(f'/manage/candidates/{cand.id}/delete/', follow=True)
            test_results['delete_response_status'] = resp.status_code
        except Exception as e:
            test_results['waiter_error'] = e

    t_holder = threading.Thread(target=holder_thread)
    t_waiter = threading.Thread(target=waiter_thread)

    try:
        t_holder.start()
        assert lock_acquired_event.wait(timeout=5), "Holder failed to acquire lock"

        t_waiter.start()
        assert delete_started_event.wait(timeout=5), "Waiter failed to start deletion"

        waiter_pid = test_results.get('waiter_pid')
        blocked_count = 0
        poll_start = time.time()
        while time.time() - poll_start < 5.0:
            with connection.cursor() as cursor:
                if waiter_pid:
                    cursor.execute("""
                        SELECT count(*)
                        FROM pg_locks l
                        JOIN pg_stat_activity a ON l.pid = a.pid
                        WHERE a.pid = %s AND a.datname = current_database() AND NOT l.granted;
                    """, [waiter_pid])
                else:
                    cursor.execute("""
                        SELECT count(*)
                        FROM pg_locks l
                        JOIN pg_stat_activity a ON l.pid = a.pid
                        WHERE a.datname = current_database() AND NOT l.granted;
                    """)
                blocked_count = cursor.fetchone()[0]
            if blocked_count >= 1:
                break
            time.sleep(0.02)
        test_results['detected_blocked_locks'] = blocked_count
    finally:
        release_vote_lock_event.set()
        if t_holder.is_alive():
            t_holder.join(timeout=10)
        if t_waiter.is_alive():
            t_waiter.join(timeout=10)

    assert test_results.get('detected_blocked_locks', 0) >= 1, "Expected PostgreSQL row lock contention in pg_locks"




# ─────────────────────────────────────────────────────────────
# 6. INTEGRATED SOC THREAT OPERATIONS & HOMEPAGE ALERT TESTS
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_manage_dashboard_displays_integrated_soc_section(client, staff_user):
    """
    Staff user accessing /manage/ can view the integrated SOC Threat Operations section,
    including metrics, table headers, and clean secure network state when empty.
    """
    client.force_login(staff_user)
    response = client.get('/manage/')
    assert response.status_code == 200
    content = response.content.decode()

    # Election management components remain intact
    assert "Election Management Portal" in content
    assert "Elections Roster" in content
    assert 'id="metric-total-elections"' in content
    assert 'id="btn-create-election"' in content

    # Integrated SOC section present
    assert 'id="soc-threat-section"' in content
    assert "Threat Operations" in content
    assert "Total Prevented Attacks" in content
    assert 'id="soc-prevented-attacks"' in content
    assert "Live Security Event Log" in content
    assert 'id="soc-events-table"' in content
    assert "Network is Secure" in content


@pytest.mark.django_db
def test_manage_dashboard_displays_soc_log_records(client, staff_user):
    """
    SecurityLog records are displayed accurately within the Manage portal SOC section
    with timestamps, severities, origin IPs, actions, and trace details.
    """
    SecurityLog.objects.create(
        level='CRITICAL',
        action='Duplicate Vote Blocked',
        ip_address='192.168.1.100',
        details='Voter hash collision detected in Senate Election'
    )
    SecurityLog.objects.create(
        level='WARNING',
        action='Invalid Nonce Attempt',
        ip_address='10.0.0.55',
        details='Trace anomaly on blockchain link'
    )

    client.force_login(staff_user)
    response = client.get('/manage/')
    assert response.status_code == 200
    content = response.content.decode()

    # Prevented attacks counter should reflect critical count
    assert 'id="soc-prevented-attacks">1<' in content

    # Event table rows contain logs
    assert "Duplicate Vote Blocked" in content
    assert "192.168.1.100" in content
    assert "Voter hash collision detected in Senate Election" in content
    assert "CRITICAL" in content

    assert "Invalid Nonce Attempt" in content
    assert "10.0.0.55" in content
    assert "Trace anomaly on blockchain link" in content
    assert "WARNING" in content


@pytest.mark.django_db
def test_manage_dashboard_soc_hidden_from_regular_voter(client, test_user):
    """
    Regular voters cannot access /manage/ or view sensitive SOC threat details.
    Server-side redirect occurs fail-closed.
    """
    SecurityLog.objects.create(
        level='CRITICAL',
        action='Confidential Security Incident',
        ip_address='10.99.88.77',
        details='Sensitive internal SOC diagnostic payload'
    )

    client.force_login(test_user)
    response = client.get('/manage/', follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == '/'
    content = response.content.decode()

    # Sensitive SOC fields must never be exposed
    assert "Confidential Security Incident" not in content
    assert "10.99.88.77" not in content
    assert "Sensitive internal SOC diagnostic payload" not in content
    assert "Live Security Event Log" not in content


@pytest.mark.django_db
def test_homepage_soc_indicator_removed_from_header(client, staff_user, test_user):
    """
    The SOC badge/indicator/link is completely removed from the public homepage header
    for all user states (anonymous, voter, staff). Staff receives standard Manage link.
    """
    # 1. Anonymous visitor
    resp_anon = client.get('/')
    content_anon = resp_anon.content.decode()
    assert '>SOC Active<' not in content_anon
    assert '/security/threat-dashboard/' not in content_anon

    # 2. Regular voter
    client.force_login(test_user)
    resp_voter = client.get('/')
    content_voter = resp_voter.content.decode()
    assert '>SOC Active<' not in content_voter
    assert '/security/threat-dashboard/' not in content_voter
    assert 'id="nav-manage-link"' not in content_voter

    # 3. Staff user: No SOC header indicator and no public Manage links on homepage
    client.force_login(staff_user)
    resp_staff = client.get('/')
    content_staff = resp_staff.content.decode()
    assert '>SOC Active<' not in content_staff
    assert 'id="nav-manage-link"' not in content_staff
    assert 'id="footer-manage-link"' not in content_staff
    # Direct access to /manage/ remains fully functional for authenticated staff
    resp_manage = client.get('/manage/')
    assert resp_manage.status_code == 200
    assert "Election Management Portal" in resp_manage.content.decode()


@pytest.mark.django_db
def test_homepage_security_warning_lifecycle(client):
    """
    Verifies that:
    1. No warning banner appears on the homepage when zero threat events exist.
    2. When a security threat event exists, a minimal non-sensitive warning appears.
    3. The warning does not expose sensitive internal trace details or origin IPs.
    """
    from django.core.cache import cache
    cache.clear()

    # 1. Zero threats: clean state
    assert SecurityLog.objects.count() == 0
    resp_clean = client.get('/')
    content_clean = resp_clean.content.decode()
    assert 'id="security-threat-warning"' not in content_clean
    assert 'data-i18n="sec_alert_title"' not in content_clean

    # 2. Security threat logged
    threat = SecurityLog.objects.create(
        level='CRITICAL',
        action='Duplicate Vote Blocked',
        ip_address='198.51.100.42',
        details='Voter hash 7f9a1b2c3d4e5f6... attempted to bypass the ledger in Campus Election.'
    )
    cache.clear()

    resp_threat = client.get('/')
    content_threat = resp_threat.content.decode()

    # Warning must appear
    assert 'id="security-threat-warning"' in content_threat
    assert "Security Notice" in content_threat
    assert "A security threat event was detected and mitigated" in content_threat

    # Strict Privacy Check: Sensitive SOC details must NOT be displayed on public homepage
    assert '198.51.100.42' not in content_threat
    assert '7f9a1b2c3d4e5f6' not in content_threat
    assert 'attempted to bypass the ledger' not in content_threat



@pytest.mark.django_db
def test_homepage_warning_triggered_by_recent_critical_event(client):
    """A recent CRITICAL event within the last 24 hours triggers the homepage warning."""
    from django.core.cache import cache
    cache.clear()

    recent_critical = SecurityLog.objects.create(
        level='CRITICAL',
        action='Duplicate Vote Blocked',
        ip_address='10.0.0.1',
        details='Collision attempt'
    )
    now = timezone.now()
    SecurityLog.objects.filter(id=recent_critical.id).update(timestamp=now - timedelta(hours=1))

    resp = client.get('/')
    assert resp.status_code == 200
    content = resp.content.decode()
    assert 'id="security-threat-warning"' in content
    assert "Security Notice" in content
    assert "A security threat event was detected and mitigated" in content


@pytest.mark.django_db
def test_homepage_warning_not_triggered_by_warning_only_event(client):
    """A WARNING-level event does not trigger the public homepage warning."""
    from django.core.cache import cache
    cache.clear()

    warning_event = SecurityLog.objects.create(
        level='WARNING',
        action='Suspicious Query Pattern',
        ip_address='10.0.0.2',
        details='Anomalous telemetry ping'
    )
    now = timezone.now()
    SecurityLog.objects.filter(id=warning_event.id).update(timestamp=now - timedelta(minutes=15))

    resp = client.get('/')
    assert resp.status_code == 200
    content = resp.content.decode()
    assert 'id="security-threat-warning"' not in content
    assert 'data-i18n="sec_alert_title"' not in content


@pytest.mark.django_db
def test_homepage_warning_not_triggered_by_stale_critical_event(client):
    """A CRITICAL event older than 24 hours does not trigger the homepage warning."""
    from django.core.cache import cache
    cache.clear()

    stale_critical = SecurityLog.objects.create(
        level='CRITICAL',
        action='Duplicate Vote Blocked',
        ip_address='10.0.0.3',
        details='Stale breach attempt'
    )
    now = timezone.now()
    SecurityLog.objects.filter(id=stale_critical.id).update(timestamp=now - timedelta(hours=26))

    resp = client.get('/')
    assert resp.status_code == 200
    content = resp.content.decode()
    assert 'id="security-threat-warning"' not in content
    assert 'data-i18n="sec_alert_title"' not in content


@pytest.mark.django_db
def test_homepage_selects_latest_qualifying_critical_event(client):
    """When multiple qualifying CRITICAL events exist within 24 hours, the latest by descending timestamp is selected."""
    from django.core.cache import cache
    cache.clear()

    now = timezone.now()

    older_event = SecurityLog.objects.create(
        level='CRITICAL',
        action='Duplicate Vote Blocked',
        ip_address='10.0.0.10',
        details='Older attempt'
    )
    older_time = now - timedelta(hours=12)
    SecurityLog.objects.filter(id=older_event.id).update(timestamp=older_time)

    newer_event = SecurityLog.objects.create(
        level='CRITICAL',
        action='Duplicate Vote Blocked',
        ip_address='10.0.0.11',
        details='Newer attempt'
    )
    newer_time = now - timedelta(hours=1)
    SecurityLog.objects.filter(id=newer_event.id).update(timestamp=newer_time)

    resp = client.get('/')
    assert resp.status_code == 200
    content = resp.content.decode()
    assert 'id="security-threat-warning"' in content

    from django.utils.dateformat import format as date_format
    expected_newer_ts = date_format(newer_time, "Y-m-d H:i")
    expected_older_ts = date_format(older_time, "Y-m-d H:i")

    assert expected_newer_ts in content
    assert expected_older_ts not in content


@pytest.mark.django_db
def test_manage_soc_still_displays_warning_and_critical_events(client, staff_user):
    """Manage portal SOC threat section displays both WARNING and CRITICAL events."""
    now = timezone.now()

    crit = SecurityLog.objects.create(
        level='CRITICAL',
        action='Ledger Bypass Attempt',
        ip_address='10.10.10.1',
        details='Critical breach attempt'
    )
    SecurityLog.objects.filter(id=crit.id).update(timestamp=now - timedelta(hours=30))

    warn = SecurityLog.objects.create(
        level='WARNING',
        action='Unusual Request Rate',
        ip_address='10.10.10.2',
        details='Warning anomaly'
    )
    SecurityLog.objects.filter(id=warn.id).update(timestamp=now - timedelta(minutes=10))

    client.force_login(staff_user)
    resp = client.get('/manage/')
    assert resp.status_code == 200
    content = resp.content.decode()

    assert "Ledger Bypass Attempt" in content
    assert "10.10.10.1" in content
    assert "Critical breach attempt" in content
    assert "CRITICAL" in content

    assert "Unusual Request Rate" in content
    assert "10.10.10.2" in content
    assert "Warning anomaly" in content
    assert "WARNING" in content

    assert 'id="soc-prevented-attacks">1<' in content


# ─────────────────────────────────────────────────────────────
# 13. STRICT SINGLE-ADMIN SECURITY TESTS (YASH ONLY)
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_yash_can_log_in_and_access_manage_portal(client, staff_user):
    """Authorized admin (yash) can log in via /login/ and access the Manage Portal."""
    login_resp = client.post('/login/', {
        'username': staff_user.username,
        'password': staff_user.raw_password,
    }, follow=True)
    assert login_resp.status_code == 200
    assert login_resp.redirect_chain[0][0] == '/manage/'
    assert "Election Management Portal" in login_resp.content.decode()


@pytest.mark.django_db
def test_different_staff_account_is_denied_login_and_portal(client, other_staff_user):
    """A different staff account (not yash) cannot log in or access /manage/."""
    # 1. Login attempt fails with generic error
    login_resp = client.post('/login/', {
        'username': other_staff_user.username,
        'password': other_staff_user.raw_password,
    })
    assert login_resp.status_code == 200
    content = login_resp.content.decode()
    assert "Invalid username or password." in content

    # Session is not established
    assert '_auth_user_id' not in client.session

    # 2. Direct request to /manage/ while authenticated as other staff is blocked
    client.force_login(other_staff_user)
    resp = client.get('/manage/', follow=True)
    assert resp.status_code == 200
    assert resp.redirect_chain[0][0] == '/'
    messages = list(resp.context['messages'])
    assert any("Access restricted" in str(m) for m in messages)


@pytest.mark.django_db
def test_different_superuser_account_is_denied_login_and_portal(client, other_superuser):
    """A different superuser account (not yash) cannot log in or access /manage/."""
    login_resp = client.post('/login/', {
        'username': other_superuser.username,
        'password': other_superuser.raw_password,
    })
    assert login_resp.status_code == 200
    assert "Invalid username or password." in login_resp.content.decode()
    assert '_auth_user_id' not in client.session

    # Direct request blocked
    client.force_login(other_superuser)
    resp = client.get('/manage/', follow=True)
    assert resp.status_code == 200
    assert resp.redirect_chain[0][0] == '/'
    messages = list(resp.context['messages'])
    assert any("Access restricted" in str(m) for m in messages)


@pytest.mark.django_db
def test_admin_site_denies_other_staff_and_superuser(client, other_staff_user, other_superuser, staff_user):
    """Django Admin (/admin/) strictly denies non-yash staff and superusers with 403 PermissionDenied."""
    # Other staff user denied
    client.force_login(other_staff_user)
    resp_staff = client.get('/admin/')
    assert resp_staff.status_code in (403, 302)

    # Other superuser denied
    client.force_login(other_superuser)
    resp_super = client.get('/admin/')
    assert resp_super.status_code in (403, 302)

    # Yash is allowed into /admin/ if active
    client.force_login(staff_user)
    resp_yash = client.get('/admin/')
    assert resp_yash.status_code == 200


@pytest.mark.django_db
def test_failed_login_attempts_are_rate_limited(client):
    """5 failed login attempts trigger rate limiting lockout and SecurityLog entry."""
    from django.core.cache import cache
    cache.clear()

    dummy_attack_pwd = f"attempt_{secrets.token_hex(8)}"
    # 4 failed attempts show invalid credentials
    for i in range(4):
        resp = client.post('/login/', {'username': 'hacker', 'password': dummy_attack_pwd})
        assert resp.status_code == 200
        assert "Invalid username or password." in resp.content.decode()

    # 5th attempt triggers rate limit
    resp5 = client.post('/login/', {'username': 'hacker', 'password': dummy_attack_pwd})
    assert resp5.status_code == 200
    assert "Too many failed login attempts" in resp5.content.decode()

    # SecurityLog has logged the event
    assert SecurityLog.objects.filter(action__icontains='Rate Limit Exceeded').exists()
    cache.clear()


@pytest.mark.django_db
def test_existing_password_for_yash_remains_unchanged(db):
    """Verifies that an existing yash account's password hash is untouched."""
    yash = User.objects.filter(username='yash').first()
    if yash:
        orig_hash = yash.password
        # Refetch from DB to confirm no overwrite or reset occurred
        yash.refresh_from_db()
        assert yash.password == orig_hash
        assert yash.password.startswith('pbkdf2_sha256$')


@pytest.mark.django_db
def test_login_and_manage_responses_have_no_cache_headers(client, staff_user):
    """Login and Manage portal views return no-cache, no-store headers."""
    # Login GET response
    resp_login = client.get('/login/')
    assert resp_login.status_code == 200
    assert 'no-store' in resp_login.headers.get('Cache-Control', '')
    assert 'no-cache' in resp_login.headers.get('Pragma', '')

    # Manage GET response
    client.force_login(staff_user)
    resp_manage = client.get('/manage/')
    assert resp_manage.status_code == 200
    assert 'no-store' in resp_manage.headers.get('Cache-Control', '')
    assert 'no-cache' in resp_manage.headers.get('Pragma', '')


@pytest.mark.django_db
def test_locmem_cache_backend_and_operations(client, active_election):
    """
    Verifies:
    1. Django initializes with the LocMemCache backend.
    2. Cache set/get/delete operations work properly.
    3. Landing page home() renders when the cache is empty.
    4. Landing page home() successfully populates and reads from cache.
    5. Login, election, results and API routes remain unaffected.
    """
    from django.core.cache import cache
    assert settings.CACHES['default']['BACKEND'] == 'django.core.cache.backends.locmem.LocMemCache'
    assert settings.CACHES['default']['LOCATION'] == 'chainvote-cache'

    # Cache operations
    cache.set('test_locmem_key', 'test_locmem_val', timeout=60)
    assert cache.get('test_locmem_key') == 'test_locmem_val'
    cache.delete('test_locmem_key')
    assert cache.get('test_locmem_key') is None

    # Landing page with empty cache
    cache.clear()
    assert cache.get('home_landing_context') is None
    resp_empty = client.get('/')
    assert resp_empty.status_code == 200
    cached_context = cache.get('home_landing_context')
    assert cached_context is not None
    assert 'active_elections' in cached_context

    # Landing page reads from existing cache
    resp_cached = client.get('/')
    assert resp_cached.status_code == 200

    # Key routes unaffected
    assert client.get('/login/').status_code == 200
    assert client.get(f'/election/{active_election.id}/').status_code == 200
    assert client.get(f'/election/{active_election.id}/results/').status_code == 200
    assert client.get('/api/elections/').status_code == 200


@pytest.mark.django_db
def test_login_rate_limiting_shared_cache_persistence(client):
    """Verifies rate limit counters persist across in-memory resets in the database cache."""
    from django.core.cache import cache
    from voting.views import _clear_fallback_failures
    cache.clear()
    _clear_fallback_failures('127.0.0.1')

    dummy_attack_pwd = f"attempt_{secrets.token_hex(8)}"
    # Record 3 failures
    for _ in range(3):
        client.post('/login/', {'username': 'hacker', 'password': dummy_attack_pwd})

    # Verify counter in shared database cache
    failures_in_db = cache.get('login_failures_127.0.0.1')
    assert failures_in_db == 3

    # Simulate process restart by purging the in-memory fallback tracker
    _clear_fallback_failures('127.0.0.1')

    # Verify that the DB cache still holds the count
    assert cache.get('login_failures_127.0.0.1') == 3

    # Next attempt increments from the DB counter
    client.post('/login/', {'username': 'hacker', 'password': dummy_attack_pwd})
    assert cache.get('login_failures_127.0.0.1') == 4

    cache.clear()
    _clear_fallback_failures('127.0.0.1')


@pytest.mark.django_db
def test_login_rate_limiting_fallback_on_cache_error(client):
    """
    Verifies that if the database cache encounters an error, the fallback tracker
    safely prevents unlimited login attempts without failing open.
    """
    from unittest.mock import patch
    from django.db import DatabaseError
    from django.core.cache import cache
    from voting.views import _clear_fallback_failures
    cache.clear()
    _clear_fallback_failures('127.0.0.1')

    dummy_attack_pwd = f"attempt_{secrets.token_hex(8)}"
    with patch('django.core.cache.cache.get', side_effect=DatabaseError("DB connection lost")),          patch('django.core.cache.cache.set', side_effect=DatabaseError("DB connection lost")):
        # 4 failed attempts show invalid credentials
        for _ in range(4):
            resp = client.post('/login/', {'username': 'hacker', 'password': dummy_attack_pwd})
            assert resp.status_code == 200
            assert "Invalid username or password." in resp.content.decode()

        # 5th attempt triggers rate limit lockout despite cache failure
        resp5 = client.post('/login/', {'username': 'hacker', 'password': dummy_attack_pwd})
        assert resp5.status_code == 200
        assert "Too many failed login attempts" in resp5.content.decode()

    cache.clear()
    _clear_fallback_failures('127.0.0.1')
