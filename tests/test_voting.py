"""
Digital Voting Booth Tests (TC-VOTE-01, TC-VOTE-02).
Covers ballot submission, client-side mining delay handling, receipt modal rendering,
and empty field validation.
"""

import pytest
from tests.pages.login_page import LoginPage
from tests.pages.voting_booth_page import VotingBoothPage


def _login_as_voter(browser, live_server, test_user):
    """Helper to authenticate a voter before entering protected booth."""
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(test_user.username, test_user.raw_password)
    login_page.wait_for_user_logged_in()


@pytest.mark.django_db(transaction=True)
def test_tc_vote_01_legitimate_ballot_casting(browser, live_server, test_user, active_election, unique_voter_id):
    """
    TC-VOTE-01: Legitimate ballot casting in an active election.
    Voter enters an active booth, selects a candidate, enters a synthetic ID,
    reviews ballot in review modal, and confirms. Accommodates the 1.5s client-side mining delay.
    Verifies the receipt modal renders with 'Block Mined Successfully' and valid timestamp.
    """
    _login_as_voter(browser, live_server, test_user)

    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    # Select the first candidate via visible label
    candidate = active_election.candidates.first()
    booth_page.select_candidate(candidate.id)
    assert booth_page.is_candidate_selected(candidate.id)

    # Enter synthetic ID and review ballot
    voter_id = unique_voter_id()
    booth_page.enter_voter_id(voter_id)
    booth_page.click_review_vote()
    booth_page.wait_for_review_modal()
    assert booth_page.is_review_modal_visible()
    assert candidate.name in booth_page.get_review_candidate_name()

    # Confirm and submit
    booth_page.click_confirm_and_submit()

    # Explicit wait for receipt modal (handles 1.5s client-side mining delay)
    booth_page.wait_for_receipt_modal(timeout=15)

    # Verifications
    assert booth_page.is_receipt_modal_visible()
    assert "Block Mined Successfully" in booth_page.get_receipt_status_message()
    assert len(booth_page.get_receipt_timestamp()) > 0


@pytest.mark.django_db(transaction=True)
def test_tc_vote_02_empty_voter_id_validation(browser, live_server, test_user, active_election):
    """
    TC-VOTE-02: Form validation on empty voter ID.
    Selecting a candidate but leaving the Aadhaar/Roll No field empty
    triggers client-side validation and prevents opening review modal or submitting.
    """
    _login_as_voter(browser, live_server, test_user)

    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    # Select candidate but leave ID empty
    candidate = active_election.candidates.first()
    booth_page.select_candidate(candidate.id)
    assert booth_page.is_candidate_selected(candidate.id)

    booth_page.click_submit_vote()

    # Verifications: receipt modal and review modal must not appear, validation alert shown
    assert not booth_page.is_receipt_modal_visible()
    assert not booth_page.is_review_modal_visible()
    assert booth_page.has_validation_alert()
    assert f"/election/{active_election.id}/" in booth_page.get_current_url()
