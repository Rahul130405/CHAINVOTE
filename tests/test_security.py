"""
Security Operations & Threat Prevention Tests (TC-SEC-01, TC-SEC-02).
Covers duplicate voting prevention, zero-knowledge voter hash collision detection,
and SOC dashboard incident verification.
"""

import pytest
from tests.pages.login_page import LoginPage
from tests.pages.voting_booth_page import VotingBoothPage
from tests.pages.soc_page import SOCPage


def _login_as_voter(browser, live_server, test_user):
    """Helper to authenticate a voter before entering protected areas."""
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(test_user.username, test_user.raw_password)
    login_page.wait_for_user_logged_in()


@pytest.mark.django_db(transaction=True)
def test_tc_sec_01_duplicate_vote_prevention(browser, live_server, test_user, active_election, unique_voter_id):
    """
    TC-SEC-01: Prevent duplicate voting in the same election.
    A voter casts a legitimate ballot with synthetic ID 'X'.
    When attempting to cast a second ballot in the same election with ID 'X',
    the application rejects the vote with 'SECURITY ALERT: You have already voted with this ID.'.
    """
    _login_as_voter(browser, live_server, test_user)

    booth_page = VotingBoothPage(browser, live_server.url)
    candidate = active_election.candidates.first()
    synthetic_id = unique_voter_id()

    # 1. Cast legitimate vote #1
    booth_page.navigate(active_election.id)
    booth_page.submit_ballot(synthetic_id, candidate.id)
    booth_page.wait_for_receipt_modal(timeout=15)
    assert booth_page.is_receipt_modal_visible()

    # 2. Attempt duplicate vote #2 with same synthetic ID in same election
    booth_page.navigate(active_election.id)
    booth_page.submit_ballot(synthetic_id, candidate.id)

    # Wait for the security alert banner
    booth_page.wait_for_security_alert(timeout=15)

    # Verifications
    assert not booth_page.is_receipt_modal_visible()
    assert booth_page.has_security_alert()
    assert "SECURITY ALERT: You have already voted with this ID" in booth_page.get_security_alert_text()


@pytest.mark.django_db(transaction=True)
def test_tc_sec_02_soc_dashboard_threat_logging(browser, live_server, staff_user, active_election, unique_voter_id):
    """
    TC-SEC-02: Verify SOC Dashboard logs duplicate voting threat.
    When a duplicate voting attempt is blocked, the system records a CRITICAL incident
    in SecurityLog. An authorized staff user can access the SOC dashboard to monitor
    the incremented counter and event row.
    """
    _login_as_voter(browser, live_server, staff_user)

    soc_page = SOCPage(browser, live_server.url)
    soc_page.navigate()
    initial_attacks = soc_page.get_prevented_attacks_count()

    booth_page = VotingBoothPage(browser, live_server.url)
    candidate = active_election.candidates.first()
    synthetic_id = unique_voter_id()

    # 1. First vote (legitimate)
    booth_page.navigate(active_election.id)
    booth_page.submit_ballot(synthetic_id, candidate.id)
    booth_page.wait_for_receipt_modal(timeout=15)

    # 2. Duplicate vote attempt to trigger threat logging
    booth_page.navigate(active_election.id)
    booth_page.submit_ballot(synthetic_id, candidate.id)
    booth_page.wait_for_security_alert(timeout=15)

    # 3. Check SOC Dashboard for incremented count and event details
    soc_page.navigate()
    updated_attacks = soc_page.get_prevented_attacks_count()

    # Verifications
    assert updated_attacks == initial_attacks + 1
    incident = soc_page.get_latest_incident_details()
    assert incident.get("severity") == "CRITICAL"
    assert incident.get("action") == "Duplicate Vote Blocked"


@pytest.mark.django_db(transaction=True)
def test_tc_sec_03_soc_restricted_for_regular_voter(browser, live_server, test_user):
    """
    TC-SEC-03: Verify server-side SOC access restriction.
    A regular non-staff voter attempting to access /security/threat-dashboard/ is denied server-side,
    redirected to home, and shown an access restriction message.
    """
    _login_as_voter(browser, live_server, test_user)

    # Attempt direct navigation to SOC threat dashboard
    browser.get(live_server.url + "/security/threat-dashboard/")

    # Must be redirected away from threat-dashboard to home
    assert "threat-dashboard" not in browser.current_url
    assert "Access restricted" in browser.page_source
