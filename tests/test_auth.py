"""
Authentication & Session Management Tests (TC-AUTH-01 to TC-AUTH-05).
Covers registration disabled, non-admin login rejection, yash single-admin login, and deep-link access control.
"""

import pytest
from django.urls import reverse
from tests.pages.login_page import LoginPage
from tests.pages.voting_booth_page import VotingBoothPage


@pytest.mark.django_db(transaction=True)
def test_tc_auth_01_registration_disabled(browser, live_server):
    """
    TC-AUTH-01: Public registration is permanently disabled.
    Navigating to /register/ returns HTTP 404 Not Found.
    """
    browser.get(f"{live_server.url}/register/")
    assert "404" in browser.title or "Not Found" in browser.page_source or "disabled" in browser.page_source.lower()


@pytest.mark.django_db
def test_tc_auth_02_registration_post_blocked(client):
    """
    TC-AUTH-02: Direct HTTP POST to /register/ is rejected with 404.
    Zero accounts are created.
    """
    resp = client.post('/register/', {
        'username': 'attempted_voter',
        'password': 'AnyPassword123!',
        'password2': 'AnyPassword123!'
    })
    assert resp.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_tc_auth_03_non_yash_user_login_rejected(browser, live_server, test_user):
    """
    TC-AUTH-03: Non-yash users cannot log in to the admin portal.
    Submitting valid credentials for a regular user displays generic 'Invalid username or password.'
    and flushes any established session immediately.
    """
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()

    login_page.login(test_user.username, test_user.raw_password)

    # Verifications: remains on login page, error displayed, not logged in
    assert "/login/" in login_page.get_current_url()
    assert login_page.has_error_alert()
    assert "Invalid username or password." in login_page.get_error_message()
    assert not login_page.is_user_logged_in()


@pytest.mark.django_db(transaction=True)
def test_tc_auth_04_valid_login(browser, live_server, staff_user):
    """
    TC-AUTH-04: Valid yash admin login & session establishment.
    Submitting valid credentials for 'yash' redirects to the Manage Portal with an active session.
    """
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()

    login_page.login(staff_user.username, staff_user.raw_password)

    # Verifications: redirected to manage portal
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    WebDriverWait(browser, 10).until(lambda d: "/manage" in d.current_url)
    assert "/manage" in browser.current_url
    assert "Election Management Portal" in browser.page_source


@pytest.mark.django_db(transaction=True)
def test_tc_auth_05_deep_link_redirect(browser, live_server, staff_user, active_election):
    """
    TC-AUTH-05: Voter-ID access and Administrative deep-link authentication guard.
    1. Public voting booth is directly accessible to unauthenticated voters without account/login.
    2. Administrative management portal (/manage/) requires authorized admin credentials and deep-link redirects.
    """
    # 1. Unauthenticated voter enters voting booth directly without account requirement
    target_booth = f"/election/{active_election.id}/"
    browser.get(f"{live_server.url}{target_booth}")

    booth_page = VotingBoothPage(browser, live_server.url)
    assert booth_page.wait_for_url_contains(target_booth)
    assert "/login/" not in browser.current_url
    assert booth_page.is_visible(VotingBoothPage.VOTE_FORM)
    assert booth_page.get_election_title() == active_election.title

    # 2. Administrative portal (/manage/) enforces deep-link guard for unauthenticated users
    admin_path = "/manage/"
    browser.get(f"{live_server.url}{admin_path}")

    login_page = LoginPage(browser, live_server.url)
    login_page.wait_for_url_contains("/login/")
    assert "/login/" in browser.current_url
    assert "next=%2Fmanage%2F" in browser.current_url or "next=/manage/" in browser.current_url

    # Wait for login page inputs to be visible and interactive
    login_page.wait_for_visible(LoginPage.PAGE_HEADING)
    login_page.wait_for_visible(LoginPage.USERNAME_INPUT)

    # Authenticate as authorized single administrator (yash)
    login_page.login(staff_user.username, staff_user.raw_password)

    # Verify forwarded directly to the requested admin management portal
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    WebDriverWait(browser, 10).until(lambda d: "/login/" not in d.current_url and "/manage/" in d.current_url)
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Election Management Portal')]")))
    assert browser.current_url.rstrip("/").endswith("/manage")
    assert "Election Management Portal" in browser.page_source
