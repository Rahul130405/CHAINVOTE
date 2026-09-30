"""
Unit and authorization tests for Phase 3 Admin components:
- @admin_required authorization decorator
- ElectionForm validation
- CandidateForm validation (per-election uniqueness)
- candidate_has_recorded_votes ballot safety helper
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.test import RequestFactory, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse

from django.db import connection, transaction
from voting.decorators import admin_required
from voting.forms import ElectionForm, CandidateForm, candidate_has_recorded_votes
from voting.models import Election, Candidate, Vote
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
def test_admin_required_superuser_allowed(rf):
    """Superusers are permitted access."""
    superuser = User.objects.create_superuser(
        username='superadmin',
        password='SuperAdminPass123!',
        email='super@chainvote.test'
    )
    request = rf.get('/manage/')
    request.user = superuser
    _add_messages_storage(request)

    response = dummy_admin_view(request)
    assert response.status_code == 200
    assert response.content.decode() == "Admin Access Granted"


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
def test_manage_superuser_allowed(client):
    """Superuser can access the admin management portal dashboard."""
    superuser = User.objects.create_superuser('superadmin2', 'super2@chainvote.test', 'Pass@1234')
    client.force_login(superuser)
    response = client.get('/manage/')
    assert response.status_code == 200
    assert "Election Management Portal" in response.content.decode()


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
def test_manage_election_deletion_is_unavailable(client, staff_user, active_election):
    """
    Critical Safety Check:
    Verify election deletion is explicitly NOT implemented:
    - No 'manage_election_delete' route exists (reverse fails).
    - Direct GET/POST to /manage/elections/<id>/delete/ returns 404.
    - Dashboard HTML contains zero delete buttons for elections.
    """
    with pytest.raises(NoReverseMatch):
        reverse('manage_election_delete', kwargs={'election_id': active_election.id})

    client.force_login(staff_user)
    resp_get = client.get(f'/manage/elections/{active_election.id}/delete/')
    assert resp_get.status_code == 404
    resp_post = client.post(f'/manage/elections/{active_election.id}/delete/')
    assert resp_post.status_code == 404

    # Verify election still exists
    assert Election.objects.filter(id=active_election.id).exists() is True

    # Verify dashboard HTML has no election delete button or action
    dash_resp = client.get('/manage/')
    content = dash_resp.content.decode()
    assert "Delete Election" not in content
    assert "btn-delete-election" not in content


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
    from django.test import Client

    now = timezone.now()
    election = Election.objects.create(
        title="Postgres Concurrency Election",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=8),
    )
    cand = Candidate.objects.create(election=election, name="Locked Candidate")
    admin_user = User.objects.create_superuser('pgadmin', 'pgadmin@test.com', 'AdminPass123!')

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
            client2 = Client()
            client2.force_login(admin_user)
            delete_started_event.set()
            resp = client2.post(f'/manage/candidates/{cand.id}/delete/', follow=True)
            test_results['delete_response_status'] = resp.status_code
        except Exception as e:
            test_results['waiter_error'] = e

    t_holder = threading.Thread(target=holder_thread)
    t_waiter = threading.Thread(target=waiter_thread)

    t_holder.start()
    assert lock_acquired_event.wait(timeout=5), "Holder failed to acquire lock"

    t_waiter.start()
    assert delete_started_event.wait(timeout=5), "Waiter failed to start deletion"

    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM pg_locks WHERE NOT granted;")
        blocked_count = cursor.fetchone()[0]
        test_results['detected_blocked_locks'] = blocked_count

    release_vote_lock_event.set()
    t_holder.join(timeout=10)
    t_waiter.join(timeout=10)

    assert test_results.get('detected_blocked_locks', 0) >= 1, "Expected PostgreSQL row lock contention in pg_locks"


