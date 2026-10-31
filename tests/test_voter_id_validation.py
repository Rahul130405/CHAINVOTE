"""
Backend Voter ID Validation Tests.

Validates that voter ID strictly adheres to the rule:
- Exactly 10 alphanumeric characters (A-Z, a-z, 0-9).
- Must contain at least one alphabetic character (A-Z, a-z) and at least one numeric digit (0-9).
- Surrounding whitespace is trimmed, but internal whitespace is rejected.
- Rejects: numeric-only, alphabetic-only, <10 chars, >10 chars, empty, whitespace-only,
  spaces, hyphens, and special characters.
- Verifies cast_vote and api_cast_vote reject invalid IDs without creating Vote records
  or mutating the blockchain/ledger.
- Verifies legitimate 10-character IDs are processed and recorded properly.
"""

import hashlib
import pytest
from django.urls import reverse
from rest_framework import status

from voting.views import validate_voter_id
from voting.models import Vote, SecurityLog


# ─────────────────────────────────────────────────────────────
# 1. UNIT TESTS FOR validate_voter_id HELPER
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("voter_id,expected_valid,description", [
    ("ABCD123456", True, "Standard valid alphanumeric (uppercase + numbers)"),
    ("abcd123456", True, "Standard valid alphanumeric (lowercase + numbers)"),
    ("A1B2C3D4E5", True, "Alternating letters and numbers"),
    ("1234567890", False, "Numeric-only rejected"),
    ("0123456789", False, "Numeric-only with leading zero rejected"),
    ("ABCDEFGHIJ", False, "Alphabetic-only uppercase rejected"),
    ("abcdefghij", False, "Alphabetic-only lowercase rejected"),
    ("ABC123@456", False, "Special character (@) rejected"),
    ("ABC 123456", False, "Internal space rejected"),
    ("ABC-123456", False, "Hyphen rejected"),
    ("", False, "Empty string rejected"),
    ("   ", False, "Whitespace-only rejected"),
])
def test_validate_voter_id_12_required_cases(voter_id, expected_valid, description):
    """Verifies all 12 required test cases for voter ID validation."""
    assert validate_voter_id(voter_id) is expected_valid, f"Failed for {description}: {voter_id}"


def test_validate_voter_id_whitespace_trimming():
    """Surrounding whitespace is trimmed, but internal whitespace is rejected."""
    assert validate_voter_id("  ABCD123456  ") is True
    assert validate_voter_id("  1234567890  ") is False  # numeric-only even after trim
    assert validate_voter_id("  ABC 123456  ") is False  # internal space rejected
    assert validate_voter_id("  ABC-123456  ") is False  # hyphen rejected


def test_validate_voter_id_valid_10_char():
    """Valid 10-character alphanumeric IDs containing letters and digits are accepted."""
    valid_ids = [
        "AB12CD3456",
        "ABCD123456",
        "abcd123456",
        "A1B2C3D4E5",
        "x9Y8z7W6v5",
        "0A1B2C3D4E",
    ]
    for vid in valid_ids:
        assert validate_voter_id(vid) is True, f"Expected {vid} to be valid"


def test_validate_voter_id_numeric_only_rejected():
    """Numeric-only IDs are strictly rejected."""
    numeric_ids = [
        "1234567890",
        "0123456789",
        "9999999999",
        "0000000000",
    ]
    for vid in numeric_ids:
        assert validate_voter_id(vid) is False, f"Expected numeric-only {vid} to be rejected"


def test_validate_voter_id_alphabetic_only_rejected():
    """Alphabetic-only IDs are strictly rejected."""
    alpha_ids = [
        "ABCDEFGHIJ",
        "abcdefghij",
        "ZZZZZZZZZZ",
        "aaaaaaaaaa",
    ]
    for vid in alpha_ids:
        assert validate_voter_id(vid) is False, f"Expected alphabetic-only {vid} to be rejected"


def test_validate_voter_id_9_char_rejected():
    """IDs with 9 characters (too short) are rejected."""
    short_ids = [
        "AB12CD345",
        "123456789",
        "SHORT9VOT",
        "a1b2c3d4e",
    ]
    for vid in short_ids:
        assert validate_voter_id(vid) is False, f"Expected {vid} to be rejected"


def test_validate_voter_id_11_char_rejected():
    """IDs with 11 characters (too long) are rejected."""
    long_ids = [
        "AB12CD34567",
        "12345678901",
        "TOOLONG11CH",
        "AB12CD345678",  # 12 chars
    ]
    for vid in long_ids:
        assert validate_voter_id(vid) is False, f"Expected {vid} to be rejected"


def test_validate_voter_id_empty_rejected():
    """Empty strings, None, and non-string types are rejected."""
    assert validate_voter_id("") is False
    assert validate_voter_id(None) is False
    assert validate_voter_id(1234567890) is False
    assert validate_voter_id([]) is False


def test_validate_voter_id_space_rejected():
    """IDs containing internal whitespace or only spaces are rejected."""
    space_ids = [
        "AB12 CD345",  # space inside
        "          ",  # only spaces
        "AB 12CD 34",  # multiple spaces
    ]
    for vid in space_ids:
        assert validate_voter_id(vid) is False, f"Expected {vid} with space to be rejected"


def test_validate_voter_id_hyphen_rejected():
    """IDs containing hyphens are rejected."""
    hyphen_ids = [
        "AB12-CD345",
        "-AB12CD345",
        "AB12CD345-",
        "TEST-ID-01",
    ]
    for vid in hyphen_ids:
        assert validate_voter_id(vid) is False, f"Expected {vid} with hyphen to be rejected"


def test_validate_voter_id_special_char_rejected():
    """IDs containing special characters or punctuation are rejected."""
    special_ids = [
        "AB12@CD345",
        "AB12#CD345",
        "AB12$CD345",
        "AB12%CD345",
        "AB12^CD345",
        "AB12&CD345",
        "AB12*CD345",
        "AB12_CD345",  # underscore
        "AB12.CD345",  # period
        "AB12/CD345",  # slash
    ]
    for vid in special_ids:
        assert validate_voter_id(vid) is False, f"Expected {vid} with special char to be rejected"


# ─────────────────────────────────────────────────────────────
# 2. INTEGRATION TESTS FOR cast_vote VIEW
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_cast_vote_rejects_invalid_ids_no_vote_no_ledger_mutation(client, active_election, test_user):
    """
    Invalid IDs submitted to cast_vote must be rejected immediately:
    - No Vote record is created.
    - No ledger/blockchain mutation occurs.
    - No duplicate-vote threat log is created.
    - User is redirected back with an appropriate error message.
    """
    client.force_login(test_user)
    candidate = active_election.candidates.first()
    post_url = reverse('cast_vote', args=[active_election.id])

    invalid_cases = [
        ("SHORT9ID", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("TOOLONGID11", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("1234567890", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("0123456789", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("ABCDEFGHIJ", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("abcdefghij", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("ABC123@456", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("ABC 123456", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("ABC-123456", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("", "ID is required"),
        ("   ", "ID is required"),
    ]

    for inv_id, expected_msg in invalid_cases:
        initial_votes_count = Vote.objects.filter(election=active_election).count()
        initial_last_vote = Vote.objects.filter(election=active_election).order_by('-id').first()
        initial_block_hash = initial_last_vote.block_hash if initial_last_vote else None

        response = client.post(post_url, {
            'aadhaar': inv_id,
            'candidate_id': candidate.id,
        }, follow=True)

        # 1. Assert redirection to election booth
        assert response.status_code == 200
        messages = [m.message for m in response.context['messages']]
        assert any(expected_msg in m for m in messages),             f"Expected validation error message '{expected_msg}' for ID '{inv_id}', got: {messages}"

        # 2. Assert NO Vote record created
        assert Vote.objects.filter(election=active_election).count() == initial_votes_count

        # 3. Assert NO blockchain mutation
        current_last_vote = Vote.objects.filter(election=active_election).order_by('-id').first()
        current_block_hash = current_last_vote.block_hash if current_last_vote else None
        assert current_block_hash == initial_block_hash

        # 4. Assert NO spurious SOC critical threat log created
        assert SecurityLog.objects.filter(action='Duplicate Vote Blocked').count() == 0


@pytest.mark.django_db(transaction=True)
def test_cast_vote_accepts_valid_10_char_id(client, active_election, test_user):
    """
    A valid 10-character alphanumeric ID submitted to cast_vote succeeds,
    creates a Vote record, and computes a valid blockchain hash.
    Also verifies surrounding whitespace is trimmed properly.
    """
    client.force_login(test_user)
    candidate = active_election.candidates.first()
    post_url = reverse('cast_vote', args=[active_election.id])
    valid_id = "  VALID10VOT  "

    initial_votes_count = Vote.objects.filter(election=active_election).count()

    response = client.post(post_url, {
        'aadhaar': valid_id,
        'candidate_id': candidate.id,
    }, follow=True)

    assert response.status_code == 200
    messages = [m.message for m in response.context['messages']]
    assert any("recorded on the blockchain" in m for m in messages)

    # Assert Vote record created
    assert Vote.objects.filter(election=active_election).count() == initial_votes_count + 1
    new_vote = Vote.objects.filter(election=active_election).order_by('-id').first()
    assert len(new_vote.block_hash) == 64
    assert len(new_vote.voter_hash) == 64
    # Voter hash must match the trimmed ID
    expected_hash = hashlib.sha256("VALID10VOT".encode()).hexdigest()
    assert new_vote.voter_hash == expected_hash


# ─────────────────────────────────────────────────────────────
# 3. INTEGRATION TESTS FOR api_cast_vote VIEW
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_api_cast_vote_rejects_invalid_ids_no_vote_no_ledger_mutation(client, active_election):
    """
    Invalid IDs submitted to api_cast_vote must return HTTP 400 Bad Request:
    - No Vote record is created.
    - No blockchain/ledger mutation occurs.
    """
    candidate = active_election.candidates.first()
    api_url = f"/api/elections/{active_election.id}/vote/"

    invalid_cases = [
        ("SHORT9ID", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("TOOLONGID11", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("1234567890", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("0123456789", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("ABCDEFGHIJ", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("abcdefghij", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("ABC123@456", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("ABC 123456", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("ABC-123456", "Voter ID must contain both letters and numbers (alphanumeric only)."),
        ("", "ID (aadhaar) is required."),
        ("   ", "ID (aadhaar) is required."),
    ]

    for inv_id, expected_error in invalid_cases:
        initial_votes_count = Vote.objects.filter(election=active_election).count()
        initial_last_vote = Vote.objects.filter(election=active_election).order_by('-id').first()
        initial_block_hash = initial_last_vote.block_hash if initial_last_vote else None

        response = client.post(
            api_url,
            {'aadhaar': inv_id, 'candidate_id': candidate.id},
            content_type='application/json'
        )

        # 1. Assert HTTP 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST,             f"Expected 400 for ID '{inv_id}', got {response.status_code}"
        data = response.json()
        assert 'error' in data
        assert expected_error in data['error'],             f"Expected error '{expected_error}' for ID '{inv_id}', got: {data['error']}"

        # 2. Assert NO Vote record created
        assert Vote.objects.filter(election=active_election).count() == initial_votes_count

        # 3. Assert NO blockchain mutation
        current_last_vote = Vote.objects.filter(election=active_election).order_by('-id').first()
        current_block_hash = current_last_vote.block_hash if current_last_vote else None
        assert current_block_hash == initial_block_hash


@pytest.mark.django_db(transaction=True)
def test_api_cast_vote_accepts_valid_10_char_id(client, active_election):
    """
    A valid 10-character alphanumeric ID submitted to api_cast_vote returns HTTP 201 Created,
    commits the Vote, and returns the mined block_hash.
    Also verifies surrounding whitespace is trimmed.
    """
    candidate = active_election.candidates.first()
    api_url = f"/api/elections/{active_election.id}/vote/"
    valid_id = "  API10CHARV  "

    initial_votes_count = Vote.objects.filter(election=active_election).count()

    response = client.post(
        api_url,
        {'aadhaar': valid_id, 'candidate_id': candidate.id},
        content_type='application/json'
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert 'block_hash' in data
    assert len(data['block_hash']) == 64
    assert Vote.objects.filter(election=active_election).count() == initial_votes_count + 1

    new_vote = Vote.objects.filter(election=active_election).order_by('-id').first()
    expected_hash = hashlib.sha256("API10CHARV".encode()).hexdigest()
    assert new_vote.voter_hash == expected_hash


# ─────────────────────────────────────────────────────────────
# 4. FRONTEND BROWSER TESTS FOR VOTER ID VALIDATION
# ─────────────────────────────────────────────────────────────

def _login_voter(browser, live_server, test_user):
    from tests.pages.login_page import LoginPage
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(test_user.username, test_user.raw_password)
    login_page.wait_for_user_logged_in()


@pytest.mark.django_db(transaction=True)
def test_frontend_voter_id_input_attributes(browser, live_server, test_user, active_election):
    """Verify input attributes: minlength=10, maxlength=10, pattern requires letters and numbers."""
    _login_voter(browser, live_server, test_user)
    from tests.pages.voting_booth_page import VotingBoothPage
    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    assert booth_page.get_voter_id_minlength() == "10"
    assert booth_page.get_voter_id_maxlength() == "10"
    assert booth_page.get_voter_id_pattern() == "(?=.*[A-Za-z])(?=.*[0-9])[A-Za-z0-9]{10}"


@pytest.mark.django_db(transaction=True)
def test_frontend_voter_id_valid_opens_review_modal(browser, live_server, test_user, active_election):
    """Valid 10-character alphanumeric ID allows review modal to open."""
    _login_voter(browser, live_server, test_user)
    from tests.pages.voting_booth_page import VotingBoothPage
    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    candidate = active_election.candidates.first()
    booth_page.select_candidate(candidate.id)
    booth_page.enter_voter_id("VALID10VOT")
    booth_page.click_review_vote()
    booth_page.wait_for_review_modal()

    assert booth_page.is_review_modal_visible()
    assert "0VOT" in booth_page.get_review_voter_id_masked()
    assert candidate.name in booth_page.get_review_candidate_name()


@pytest.mark.django_db(transaction=True)
def test_frontend_voter_id_invalid_rejected_inline_and_modal_blocked(browser, live_server, test_user, active_election):
    """
    Invalid IDs (numeric-only, alphabetic-only, 9-char, spaces, hyphens, special chars) are rejected client-side:
    - Review modal does NOT open.
    - Inline validation warning banner is displayed.
    - Maxlength=10 prevents typing 11 characters.
    """
    _login_voter(browser, live_server, test_user)
    from tests.pages.voting_booth_page import VotingBoothPage
    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    candidate = active_election.candidates.first()
    booth_page.select_candidate(candidate.id)

    invalid_test_ids = [
        "1234567890",   # numeric-only
        "0123456789",   # numeric-only leading zero
        "ABCDEFGHIJ",   # alphabetic-only uppercase
        "abcdefghij",   # alphabetic-only lowercase
        "SHORT9VOT",    # 9-character ID
        "AB12 CD345",   # ID containing space
        "AB12-CD345",   # ID containing hyphen
        "AB12@CD345",   # ID containing special character
    ]

    for inv_id in invalid_test_ids:
        booth_page.enter_voter_id(inv_id)
        booth_page.click_review_vote()
        assert not booth_page.is_review_modal_visible(), f"Review modal should not open for invalid ID: {inv_id}"
        assert booth_page.has_validation_alert(), f"Expected validation alert for invalid ID: {inv_id}"
        assert "Voter ID must contain both letters and numbers (alphanumeric only)." in booth_page.get_validation_alert_text()
        assert booth_page.has_field_error(), f"Expected inline field error for invalid ID: {inv_id}"
        assert "Voter ID must contain both letters and numbers (alphanumeric only)." in booth_page.get_field_error_text()
        assert booth_page.get_voter_id_aria_invalid() == "true"
        assert "border-rose-500" in booth_page.get_voter_id_class()
        assert "bg-rose-50" in booth_page.get_voter_id_class()

    # Maxlength=10 prevents entry of 11th character
    booth_page.enter_voter_id("TOOLONGID11")
    assert len(booth_page.get_voter_id_value()) == 10
    assert booth_page.get_voter_id_value() == "TOOLONGID1"


@pytest.mark.django_db(transaction=True)
def test_frontend_voter_id_bilingual_validation_messages(browser, live_server, test_user, active_election):
    """Inline validation messages update between English and Hindi when language is toggled."""
    _login_voter(browser, live_server, test_user)
    from tests.pages.voting_booth_page import VotingBoothPage
    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    candidate = active_election.candidates.first()
    booth_page.select_candidate(candidate.id)
    booth_page.enter_voter_id("1234567890")  # numeric-only triggers invalid_id alert
    booth_page.click_review_vote()

    # Verify English message
    assert booth_page.has_validation_alert()
    assert "Voter ID must contain both letters and numbers (alphanumeric only)." in booth_page.get_validation_alert_text()

    # Toggle to Hindi
    booth_page.toggle_language()
    assert "मतदाता आईडी में अक्षर और संख्या दोनों होने चाहिए" in booth_page.get_validation_alert_text()

    # Toggle back to English
    booth_page.toggle_language()
    assert "Voter ID must contain both letters and numbers (alphanumeric only)." in booth_page.get_validation_alert_text()


@pytest.mark.django_db(transaction=True)
def test_frontend_voter_id_show_hide_toggle(browser, live_server, test_user, active_election):
    """Show/hide password toggle works properly on the voter ID field."""
    _login_voter(browser, live_server, test_user)
    from tests.pages.voting_booth_page import VotingBoothPage
    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    assert booth_page.get_voter_id_input_type() == "password"
    booth_page.toggle_voter_id_visibility()
    assert booth_page.get_voter_id_input_type() == "text"
    booth_page.toggle_voter_id_visibility()
    assert booth_page.get_voter_id_input_type() == "password"


@pytest.mark.django_db(transaction=True)
def test_frontend_voter_id_empty_and_valid_ui_states(browser, live_server, test_user, active_election):
    """
    Verifies Voter ID field visual states:
    1. Initially neutral without red borders or errors before interaction.
    2. Empty input shows red border, red tint, and 'Voter ID is required.' upon attempting to proceed.
    3. Valid input immediately removes red errors and applies green success state.
    4. Accessibility attributes (aria-invalid, aria-describedby) update accurately.
    """
    _login_voter(browser, live_server, test_user)
    from tests.pages.voting_booth_page import VotingBoothPage
    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    # 1. Initial State: No red errors before interaction
    assert not booth_page.has_field_error()
    assert booth_page.get_voter_id_aria_invalid() == "false"
    assert "border-rose-500" not in booth_page.get_voter_id_class()
    assert "aadhaarError" in booth_page.get_voter_id_aria_describedby()

    # 2. Empty Input: Attempt to proceed -> red border + "Voter ID is required."
    candidate = active_election.candidates.first()
    booth_page.select_candidate(candidate.id)
    booth_page.click_review_vote()
    assert not booth_page.is_review_modal_visible()
    assert booth_page.has_validation_alert()
    assert booth_page.has_field_error()
    assert "Voter ID is required." in booth_page.get_field_error_text()
    assert booth_page.get_voter_id_aria_invalid() == "true"
    assert "border-rose-500" in booth_page.get_voter_id_class()
    assert "bg-rose-50" in booth_page.get_voter_id_class()

    # 3. Valid Input: Correcting value -> immediately clears error & applies subtle green success state
    booth_page.enter_voter_id("VALID10VOT")
    assert not booth_page.has_field_error()
    assert booth_page.get_voter_id_aria_invalid() == "false"
    assert "border-rose-500" not in booth_page.get_voter_id_class()
    assert "border-emerald-500" in booth_page.get_voter_id_class()
    assert "bg-emerald-50" in booth_page.get_voter_id_class()

    # Proceed succeeds with valid input
    booth_page.click_review_vote()
    booth_page.wait_for_review_modal()
    assert booth_page.is_review_modal_visible()
