"""
Unit and integration tests for Voter ID-based Voting Architecture.
Verifies that:
1. Anonymous visitors can view active elections.
2. Voters can enter the voting flow and view the ballot without an account.
3. Voter ID validation (strict 10-char alphanumeric) and blockchain vote recording work without login.
4. Duplicate votes by unauthenticated voters are rejected and trigger CRITICAL SecurityLog entries.
5. Registration is no longer offered publicly on the homepage or login page.
6. Admin authentication preserves access to /manage/, while remaining admin-only.
"""

import pytest
from django.urls import reverse
from voting.models import Election, Candidate, Vote, SecurityLog
from voting.views import hash_identity


@pytest.mark.django_db
def test_anonymous_visitor_can_view_active_elections(client, active_election):
    """Anonymous visitors can view the homepage and active elections without logging in."""
    response = client.get(reverse('home'))
    assert response.status_code == 200
    content = response.content.decode()

    # Active election is displayed
    assert active_election.title in content
    assert "Active Elections" in content

    # Public Manage link is completely absent
    assert 'id="nav-manage-link"' not in content
    assert 'id="footer-manage-link"' not in content


@pytest.mark.django_db
def test_voter_enters_voting_flow_without_account(client, active_election):
    """Unauthenticated voters can access the election detail / voting booth directly without being redirected to login."""
    booth_url = reverse('election_detail', args=[active_election.id])
    response = client.get(booth_url)

    # Must NOT redirect to login
    assert response.status_code == 200
    content = response.content.decode()

    # Voting booth and candidates must be rendered
    assert active_election.title in content
    for candidate in active_election.candidates.all():
        assert candidate.name in content


@pytest.mark.django_db
def test_voter_id_validation_and_ballot_casting_without_account(client, active_election):
    """
    Unauthenticated voters can cast a vote using a valid 10-character alphanumeric Voter ID.
    The vote is encrypted and securely appended to the blockchain ledger.
    """
    candidate = active_election.candidates.first()
    vote_url = reverse('cast_vote', args=[active_election.id])

    # 1. Reject invalid Voter ID (alphabetic only)
    resp_invalid = client.post(vote_url, {
        'aadhaar': 'ABCDEFGHIJ',
        'candidate_id': candidate.id
    }, follow=True)
    assert resp_invalid.status_code == 200
    assert Vote.objects.filter(election=active_election).count() == 0

    # 2. Accept valid Voter ID (alphanumeric: letters + numbers)
    valid_id = 'VOTER12345'
    resp_valid = client.post(vote_url, {
        'aadhaar': valid_id,
        'candidate_id': candidate.id
    }, follow=True)
    assert resp_valid.status_code == 200

    # Verify Vote record created on blockchain with voter_hash
    expected_hash = hash_identity(valid_id)
    vote = Vote.objects.filter(election=active_election, voter_hash=expected_hash).first()
    assert vote is not None
    assert vote.block_hash is not None and len(vote.block_hash) == 64


@pytest.mark.django_db
def test_anonymous_duplicate_vote_is_rejected_and_logged(client, active_election):
    """
    Unauthenticated duplicate voting attempts are blocked and logged as CRITICAL in SecurityLog.
    """
    candidate = active_election.candidates.first()
    vote_url = reverse('cast_vote', args=[active_election.id])
    voter_id = 'DUPLIC890A'

    # First vote succeeds
    resp1 = client.post(vote_url, {
        'aadhaar': voter_id,
        'candidate_id': candidate.id
    }, follow=True)
    assert resp1.status_code == 200
    assert Vote.objects.filter(election=active_election).count() == 1

    # Second vote with same Voter ID is blocked
    resp2 = client.post(vote_url, {
        'aadhaar': voter_id,
        'candidate_id': candidate.id
    }, follow=True)
    assert resp2.status_code == 200
    content2 = resp2.content.decode()
    assert "You have already voted with this ID" in content2

    # Exactly 1 vote remains in ledger
    assert Vote.objects.filter(election=active_election).count() == 1

    # Threat logged in SecurityLog
    threat = SecurityLog.objects.filter(action='Duplicate Vote Blocked', level='CRITICAL').first()
    assert threat is not None
    assert f"'{active_election.title}'" in threat.details


@pytest.mark.django_db
def test_registration_is_not_offered_publicly(client):
    """Registration links ('Create one', 'Register') are no longer offered on the homepage or login page."""
    # 1. Homepage
    home_resp = client.get(reverse('home'))
    home_content = home_resp.content.decode()
    assert 'id="nav-manage-link"' not in home_content
    assert 'Create one' not in home_content
    assert 'data-i18n="link_create_account"' not in home_content

    # 2. Login page
    login_resp = client.get(reverse('login'))
    login_content = login_resp.content.decode()
    assert 'Create one' not in login_content
    assert 'data-i18n="link_create_account"' not in login_content
    assert 'data-i18n="nav_register"' not in login_content


@pytest.mark.django_db
def test_admin_authentication_and_manage_access_controls(client, test_user, staff_user):
    """
    Admin authentication is preserved and separate:
    - /manage/ redirects unauthenticated users to /login/?next=/manage/
    - Regular voters cannot access /manage/ (blocked with 302 to home)
    - Staff users can access /manage/ and view the Election Management Portal
    """
    manage_url = reverse('manage_dashboard')

    # 1. Anonymous user redirected to login
    resp_anon = client.get(manage_url)
    assert resp_anon.status_code == 302
    assert resp_anon.url.startswith('/login/?next=/manage/')

    # 2. Regular voter blocked
    client.force_login(test_user)
    resp_voter = client.get(manage_url, follow=True)
    assert resp_voter.status_code == 200
    assert resp_voter.redirect_chain[0][0] == '/'

    # 3. Staff user granted access
    client.force_login(staff_user)
    resp_staff = client.get(manage_url)
    assert resp_staff.status_code == 200
    assert "Election Management Portal" in resp_staff.content.decode()


@pytest.mark.django_db
def test_public_pages_do_not_expose_ledger_links(client, active_election):
    """
    Public voter pages (booth, results, home) do not display active ledger links to regular users.
    """
    # 1. Voting booth navbar
    booth_resp = client.get(reverse('election_detail', args=[active_election.id]))
    assert booth_resp.status_code == 200
    booth_content = booth_resp.content.decode()
    assert reverse('blockchain_explorer', args=[active_election.id]) not in booth_content
    assert 'data-i18n="nav_ledger"' not in booth_content

    # 2. Election results
    results_resp = client.get(reverse('results', args=[active_election.id]))
    assert results_resp.status_code == 200
    results_content = results_resp.content.decode()
    assert reverse('blockchain_explorer', args=[active_election.id]) not in results_content
    assert "Audit Live Ledger Instead" not in results_content
    assert "Immutable Ledger Sealed" in results_content

    # 3. Homepage for anonymous users has no active blockchain_explorer link
    home_resp = client.get(reverse('home'))
    assert home_resp.status_code == 200
    home_content = home_resp.content.decode()
    assert f'href="/election/{active_election.id}/blockchain/"' not in home_content


@pytest.mark.django_db
def test_blockchain_explorer_is_restricted_to_admin(client, active_election, test_user, staff_user):
    """
    Standalone /election/<id>/blockchain/ route enforces fail-closed administrator authorization:
    - Anonymous users are redirected to /login/?next=...
    - Regular voters are blocked and redirected to /
    - Staff users can access and view the blockchain explorer
    """
    explorer_url = reverse('blockchain_explorer', args=[active_election.id])

    # 1. Anonymous user redirected to login
    resp_anon = client.get(explorer_url)
    assert resp_anon.status_code == 302
    assert resp_anon.url.startswith(f'/login/?next={explorer_url}')

    # 2. Regular voter redirected to home with restriction
    client.force_login(test_user)
    resp_voter = client.get(explorer_url, follow=True)
    assert resp_voter.status_code == 200
    assert resp_voter.redirect_chain[0][0] == '/'

    # 3. Staff user granted access
    client.force_login(staff_user)
    resp_staff = client.get(explorer_url)
    assert resp_staff.status_code == 200
    assert "Ledger Explorer" in resp_staff.content.decode()


@pytest.mark.django_db
def test_manage_dashboard_excludes_embedded_ledger_table(client, staff_user, active_election):
    """
    Manage Dashboard is focused on election management; the embedded ledger table
    has been removed and replaced with a link to the dedicated /manage/ledger/ route.
    """
    client.force_login(staff_user)
    resp = client.get(reverse('manage_dashboard'))
    assert resp.status_code == 200
    content = resp.content.decode()

    # Embedded table and its section must NOT exist on manage dashboard
    assert 'id="blockchain-ledger-section"' not in content
    assert 'id="ledger-blocks-table"' not in content
    assert "Blockchain Ledger Operations" not in content

    # Header jump link points to dedicated /manage/ledger/
    ledger_url = reverse('manage_ledger')
    assert f'href="{ledger_url}"' in content
    assert 'id="btn-jump-ledger"' in content

    # Top navigation contains Ledger link for authorized admin
    assert 'id="nav-ledger-link"' in content


@pytest.mark.django_db
def test_dedicated_manage_ledger_page_access_and_security(client, active_election, test_user, staff_user):
    """
    Dedicated /manage/ledger/ enforces fail-closed administrator authorization:
    - Anonymous users are redirected to login with ?next=...
    - Regular voters are blocked and redirected to /
    - Staff/authorized admins are granted access (200 OK)
    """
    ledger_url = reverse('manage_ledger')

    # 1. Anonymous user redirected to login
    resp_anon = client.get(ledger_url)
    assert resp_anon.status_code == 302
    assert resp_anon.url.startswith(f'/login/?next={ledger_url}')

    # 2. Regular voter redirected to home
    client.force_login(test_user)
    resp_voter = client.get(ledger_url, follow=True)
    assert resp_voter.status_code == 200
    assert resp_voter.redirect_chain[0][0] == '/'
    assert "Access restricted" in resp_voter.content.decode()

    # 3. Staff user granted access
    client.force_login(staff_user)
    resp_staff = client.get(ledger_url)
    assert resp_staff.status_code == 200
    content = resp_staff.content.decode()
    assert "Blockchain Ledger" in content
    assert 'id="ledger-heading"' in content


@pytest.mark.django_db
def test_dedicated_manage_ledger_visual_blocks_and_integrity(client, staff_user, active_election):
    """
    Dedicated /manage/ledger/ renders sequentially connected visual block cards,
    real database hashes, chain integrity indicators, search controls, and election filters.
    """
    client.force_login(staff_user)
    ledger_url = reverse('manage_ledger')

    # 1. Empty state when 0 votes exist
    resp_empty = client.get(ledger_url)
    assert resp_empty.status_code == 200
    content_empty = resp_empty.content.decode()

    assert 'id="ledger-total-blocks">0<' in content_empty
    assert 'id="ledger-chain-status"' in content_empty
    assert "Chains Valid" in content_empty
    assert 'id="ledger-empty-state"' in content_empty
    assert "Ledger is Empty" in content_empty

    # 2. Cast 1st vote
    candidate = active_election.candidates.first()
    vote_url = reverse('cast_vote', args=[active_election.id])
    client.post(vote_url, {'aadhaar': 'BLOCK12345', 'candidate_id': candidate.id})

    # 3. Cast 2nd vote to verify sequential connection
    client.post(vote_url, {'aadhaar': 'BLOCK67890', 'candidate_id': candidate.id})

    # 4. Ledger renders connected blocks
    resp_blocks = client.get(ledger_url)
    assert resp_blocks.status_code == 200
    content_blocks = resp_blocks.content.decode()

    assert 'id="ledger-total-blocks">2<' in content_blocks
    assert 'id="ledger-empty-state"' not in content_blocks

    votes = list(Vote.objects.filter(election=active_election).order_by('id'))
    assert len(votes) == 2

    # Block cards rendered with real hashes
    for v in votes:
        assert f'id="block-item-{v.id}"' in content_blocks
        assert f"Block #{v.id}" in content_blocks
        assert v.previous_hash in content_blocks
        assert v.block_hash in content_blocks
        assert v.encrypted_vote in content_blocks

    # Sequential connection elements present
    assert "SHA-256 Link" in content_blocks
    assert "flowDown" in content_blocks
    assert 'id="verifyBtn"' in content_blocks
    assert 'id="ledgerSearch"' in content_blocks

    # 5. Election filtering works
    filter_url = f"{ledger_url}?election={active_election.id}"
    resp_filter = client.get(filter_url)
    assert resp_filter.status_code == 200
    assert active_election.title in resp_filter.content.decode()
