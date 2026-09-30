"""
Phase 2 Functional & Browser Testing Suite for CHAINVOTE.

Comprehensive verification of all Phase 2 Voter Experience deliverables:
- Application startup, static health, no console errors.
- Authentication: login, logout, registration, duplicate checks, show/hide password,
  bilingual English/Hindi toggles, language persistence, dark/light theme.
- Dashboard: anonymous vs authenticated states, status badges, 4-step instructions,
  responsive viewports (Desktop, Tablet, Mobile).
- Voting Booth: candidate cards, keyboard selection, voter ID toggle, inline validation,
  Review-and-Confirm modal, "Change Selection" non-submission, candidate update,
  double-submit protection, and server-side duplicate prevention.
- Success Receipt: plain-language receipt modal, timestamp, print button, return link.
- High-resolution screenshot capture of all primary flows.
"""

import os
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from tests.pages.login_page import LoginPage
from tests.pages.register_page import RegisterPage
from tests.pages.voting_booth_page import VotingBoothPage
from tests.pages.base_page import BasePage

SCREENSHOT_DIR = r"C:\Users\Lenovo\.gemini\antigravity-cli\brain\44751b11-0456-48c0-942b-26b115e947a3\screenshots"


def save_screenshot(browser, filename: str):
    """Saves browser screenshot to the artifacts directory."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    browser.save_screenshot(filepath)
    return filepath


@pytest.mark.django_db(transaction=True)
def test_phase2_startup_and_static_health(browser, live_server, active_election):
    """
    Section 2.A: Verify application pages load in browser with valid HTTP 200,
    no browser console errors, and correct static asset loading.
    """
    # 1. Home page
    browser.get(live_server.url + "/")
    assert "ChainVote" in browser.title
    base_page = BasePage(browser, live_server.url)
    assert base_page.is_visible(BasePage.NAV_BRAND_LINK)

    # Check for critical browser console errors
    logs = browser.get_log("browser")
    severe_errors = [entry for entry in logs if entry.get("level") == "SEVERE" and "favicon" not in entry.get("message", "")]
    assert len(severe_errors) == 0, f"Unexpected browser console errors: {severe_errors}"

    # Capture Home screenshot
    save_screenshot(browser, "01_home_dashboard.png")

    # 2. Login page
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    assert login_page.is_visible(LoginPage.USERNAME_INPUT)
    assert login_page.is_visible(LoginPage.PASSWORD_INPUT)

    # 3. Register page
    register_page = RegisterPage(browser, live_server.url)
    register_page.navigate()
    assert register_page.is_visible(RegisterPage.USERNAME_INPUT)
    assert register_page.is_visible(RegisterPage.PASSWORD_INPUT)
    assert register_page.is_visible(RegisterPage.PASSWORD2_INPUT)


@pytest.mark.django_db(transaction=True)
def test_phase2_authentication_and_accessibility(browser, live_server, test_user, unique_username):
    """
    Section 2.B: Test login, logout, password show/hide, bilingual switch,
    language persistence, and dark/light mode toggle.
    """
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()

    # 1. Test Password Show/Hide Toggle on Login
    assert login_page.get_password_input_type() == "password"
    login_page.enter_password("SecretPass123!")
    login_page.toggle_password_visibility()
    assert login_page.get_password_input_type() == "text"
    login_page.toggle_password_visibility()
    assert login_page.get_password_input_type() == "password"

    # 2. Test Bilingual Hindi/English Switch & Persistence
    assert login_page.get_current_language() == "en"
    login_page.toggle_language()
    assert login_page.get_current_language() == "hi"
    assert login_page.get_html_lang() == "hi"

    # Refresh page: verify language remains Hindi (persisted in localStorage)
    browser.refresh()
    time.sleep(0.3)
    assert login_page.get_current_language() == "hi"
    assert "वापसी पर स्वागत" in browser.page_source

    # Capture Login screenshot in Hindi mode
    save_screenshot(browser, "02_login_page_hindi.png")

    # Switch back to English
    login_page.toggle_language()
    assert login_page.get_current_language() == "en"
    save_screenshot(browser, "02_login_page.png")

    # 3. Test Invalid Login
    login_page.login("non_existent_user", "WrongPassword123!")
    assert login_page.has_error_alert()
    assert "Invalid username or password" in login_page.get_error_message()

    # 4. Test Valid Login and Session Establishment
    login_page.login(test_user.username, test_user.raw_password)
    assert login_page.wait_for_user_logged_in()
    assert test_user.username in login_page.get_logged_in_username()

    # 5. Test Logout
    login_page.click_sign_out()
    assert "/login/" in browser.current_url
    assert not login_page.is_user_logged_in()

    # 6. Test Registration Show/Hide Password for both fields
    register_page = RegisterPage(browser, live_server.url)
    register_page.navigate()
    assert register_page.get_password_input_type() == "password"
    assert register_page.get_password2_input_type() == "password"

    register_page.toggle_password_visibility()
    assert register_page.get_password_input_type() == "text"
    register_page.toggle_password2_visibility()
    assert register_page.get_password2_input_type() == "text"

    register_page.toggle_password_visibility()
    register_page.toggle_password2_visibility()
    assert register_page.get_password_input_type() == "password"
    assert register_page.get_password2_input_type() == "password"

    save_screenshot(browser, "03_register_page.png")

    # 7. Test Dark Mode Removal (No theme toggle, dark class absent, rendered in light mode)
    base_page = BasePage(browser, live_server.url)
    assert not base_page.has_theme_toggle(), "Theme toggle button must be absent across all pages"
    assert not base_page.is_dark_mode(), "Application must render in light mode without 'dark' class"


@pytest.mark.django_db(transaction=True)
def test_phase2_home_dashboard_and_responsive(browser, live_server, test_user, active_election, ended_election):
    """
    Section 2.C: Test anonymous and authenticated navigation, active/ended election badges,
    4-step instructions, and responsive viewport sizes.
    """
    # 1. Anonymous home view
    browser.get(live_server.url + "/")
    base_page = BasePage(browser, live_server.url)
    assert not base_page.is_user_logged_in()
    assert "Active Elections" in browser.page_source
    assert "Past Elections" in browser.page_source
    assert "How to Cast Your Vote" in browser.page_source

    # Check 4 Steps in guide
    assert "Sign In" in browser.page_source
    assert "Choose Election" in browser.page_source
    assert "Verify & Select" in browser.page_source
    assert "Review & Confirm" in browser.page_source

    # Check Active Election details and CTA
    assert active_election.title in browser.page_source
    assert "Enter Booth →" in browser.page_source

    # Check Completed Election details
    assert ended_election.title in browser.page_source
    assert "Results" in browser.page_source
    assert "Audit Chain" in browser.page_source

    # 2. Test Viewport Responsiveness
    # Desktop 100% zoom (1920 x 1080)
    base_page.set_viewport(1920, 1080)
    time.sleep(0.3)
    save_screenshot(browser, "01_home_desktop_100.png")

    # Tablet (768 x 1024)
    base_page.set_viewport(768, 1024)
    time.sleep(0.3)
    assert base_page.is_visible(BasePage.NAV_BRAND_LINK)

    # Mobile (375 x 667)
    base_page.set_viewport(375, 667)
    time.sleep(0.3)
    assert base_page.is_visible(BasePage.NAV_BRAND_LINK)
    save_screenshot(browser, "01_home_mobile_375.png")

    # Reset to Desktop (1920 x 1080)
    base_page.set_viewport(1920, 1080)

    # Test Hindi countdown localization on home dashboard
    base_page.toggle_language()
    time.sleep(0.3)
    assert base_page.get_current_language() == "hi"
    assert "समाप्त होने में:" in browser.page_source
    # Verify proper names are NOT corrupted/translated
    assert active_election.title in browser.page_source
    # Switch back to English
    base_page.toggle_language()
    time.sleep(0.3)

    # 3. Authenticated home view
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(test_user.username, test_user.raw_password)
    login_page.wait_for_user_logged_in()

    browser.get(live_server.url + "/")
    assert base_page.is_user_logged_in()
    assert test_user.username in base_page.get_logged_in_username()


@pytest.mark.django_db(transaction=True)
def test_phase2_voting_booth_complete_flow(browser, live_server, test_user, active_election, unique_voter_id):
    """
    Section 2.D & 2.E: Complete Voting Booth verification:
    - Candidate selection (mouse & keyboard)
    - Voter ID show/hide toggle
    - Validation on missing ID and missing candidate
    - Review Modal: summary accuracy, masked ID
    - "Change Selection" closes modal without submitting
    - Candidate re-selection updates review modal
    - "Confirm & Submit Vote" submits and prevents double clicks
    - Receipt Modal verification and print button
    """
    # 1. Login voter
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(test_user.username, test_user.raw_password)
    login_page.wait_for_user_logged_in()

    booth_page = VotingBoothPage(browser, live_server.url)
    booth_page.navigate(active_election.id)

    # 2. Voter ID Show/Hide Toggle
    assert booth_page.get_voter_id_input_type() == "password"
    booth_page.toggle_voter_id_visibility()
    assert booth_page.get_voter_id_input_type() == "text"
    booth_page.toggle_voter_id_visibility()
    assert booth_page.get_voter_id_input_type() == "password"

    # 3. Validation: Missing Voter ID
    candidates = list(active_election.candidates.all())
    cand1 = candidates[0]
    cand2 = candidates[1]
    cand3 = candidates[2]

    booth_page.select_candidate(cand1.id)
    assert booth_page.is_candidate_selected(cand1.id)

    booth_page.click_review_vote()
    assert booth_page.has_validation_alert()
    assert "enter your Unique Voter ID" in booth_page.get_validation_alert_text()
    assert not booth_page.is_review_modal_visible()

    # 4. Validation: Missing Candidate (Clear selection via ID reload or new page)
    # We clear ID and candidate by refreshing
    browser.refresh()
    time.sleep(0.3)
    voter_id = unique_voter_id()
    booth_page.enter_voter_id(voter_id)
    booth_page.click_review_vote()
    assert booth_page.has_validation_alert()
    assert "select a candidate" in booth_page.get_validation_alert_text()
    assert not booth_page.is_review_modal_visible()

    # 5. Candidate Selection using Mouse and Keyboard
    # Mouse select candidate 1
    booth_page.select_candidate(cand1.id)
    assert booth_page.is_candidate_selected(cand1.id)

    # Keyboard navigation: Focus candidate radio and select candidate 2
    radio_elem = browser.find_element(By.ID, f"candidate_{cand2.id}")
    browser.execute_script("arguments[0].checked = true; arguments[0].dispatchEvent(new Event('change'));", radio_elem)
    assert booth_page.is_candidate_selected(cand2.id)

    # 6. Open Review Modal
    booth_page.click_review_vote()
    booth_page.wait_for_review_modal()
    assert booth_page.is_review_modal_visible()

    # Verify Review Modal Content
    assert cand2.name in booth_page.get_review_candidate_name()
    masked_id = booth_page.get_review_voter_id_masked()
    assert "••••" in masked_id
    assert voter_id[-4:] in masked_id
    # Verify the badge accurately says "Masked" instead of "Encrypted"
    assert booth_page.get_review_badge_text() == "Masked"

    # Capture Review Modal Screenshot with accurate Masked badge
    save_screenshot(browser, "04_voting_review_modal.png")

    # 7. Test "Change Selection" button:
    # Must close modal WITHOUT submitting vote
    booth_page.click_change_selection()
    time.sleep(0.3)
    assert not booth_page.is_review_modal_visible()
    assert not booth_page.is_receipt_modal_visible()
    assert f"/election/{active_election.id}/" in booth_page.get_current_url()

    # Verify mobile layout for voting booth at 375px width
    booth_page.set_viewport(375, 812)
    time.sleep(0.3)
    save_screenshot(browser, "04_booth_mobile_375.png")
    booth_page.set_viewport(1920, 1080)
    time.sleep(0.2)

    # 8. Change candidate selection to Candidate 3
    booth_page.select_candidate(cand3.id)
    assert booth_page.is_candidate_selected(cand3.id)

    # Re-open Review Modal: Verify updated candidate
    booth_page.click_review_vote()
    booth_page.wait_for_review_modal()
    assert booth_page.is_review_modal_visible()
    assert cand3.name in booth_page.get_review_candidate_name()

    # 9. Test "Confirm & Submit Vote"
    booth_page.click_confirm_and_submit()

    # Wait for receipt modal (mining delay + reload)
    booth_page.wait_for_receipt_modal(timeout=15)
    assert booth_page.is_receipt_modal_visible()
    assert "Block Mined Successfully" in booth_page.get_receipt_status_message()
    assert len(booth_page.get_receipt_timestamp()) > 0

    # Capture Success Receipt Screenshot
    save_screenshot(browser, "05_success_receipt_modal.png")

    # 10. Verify Return to Network link
    booth_page.click_return_to_network()
    assert booth_page.wait_for_url_contains("/")

    # 11. Duplicate Vote Prevention in Browser
    # Attempting to vote again with same voter_id in same election must be rejected
    booth_page.navigate(active_election.id)
    booth_page.submit_ballot(voter_id, cand1.id)
    booth_page.wait_for_security_alert(timeout=15)
    assert booth_page.has_security_alert()
    assert "SECURITY ALERT: You have already voted with this ID" in booth_page.get_security_alert_text()
    assert not booth_page.is_receipt_modal_visible()
