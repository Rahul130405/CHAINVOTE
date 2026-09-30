"""
Authentication & Session Management Tests (TC-AUTH-01 to TC-AUTH-05).
Covers voter registration, validation, credential login, and deep-link access control.
"""

import pytest
from tests.pages.login_page import LoginPage
from tests.pages.register_page import RegisterPage
from tests.pages.voting_booth_page import VotingBoothPage


@pytest.mark.django_db(transaction=True)
def test_tc_auth_01_successful_registration(browser, live_server, unique_username):
    """
    TC-AUTH-01: Successful voter registration.
    Submitting valid, matching registration details creates an account,
    logs the user in automatically, and redirects to the Command Center.
    """
    register_page = RegisterPage(browser, live_server.url)
    register_page.navigate()

    username = unique_username()
    password = "VoterSecure@2026!"

    register_page.register(username, password, password)

    # Verifications
    assert register_page.wait_for_user_logged_in()
    assert register_page.is_user_logged_in()
    assert username in register_page.get_logged_in_username()


@pytest.mark.django_db(transaction=True)
def test_tc_auth_02_registration_password_mismatch(browser, live_server, unique_username):
    """
    TC-AUTH-02: Registration password mismatch validation.
    Submitting differing passwords keeps the user on /register/ and
    displays the error 'Passwords do not match.'.
    """
    register_page = RegisterPage(browser, live_server.url)
    register_page.navigate()

    username = unique_username()
    register_page.register(username, "PasswordA!123", "PasswordB!999")

    # Verifications
    assert "/register/" in register_page.get_current_url()
    assert register_page.has_error_alert()
    assert "Passwords do not match." in register_page.get_error_message()
    assert not register_page.is_user_logged_in()


@pytest.mark.django_db(transaction=True)
def test_tc_auth_03_registration_duplicate_username(browser, live_server, test_user):
    """
    TC-AUTH-03: Registration duplicate username validation.
    Submitting an already-registered username keeps the user on /register/ and
    displays the error 'Username already taken.'.
    """
    register_page = RegisterPage(browser, live_server.url)
    register_page.navigate()

    register_page.register(test_user.username, "AnyPassword123!", "AnyPassword123!")

    # Verifications
    assert "/register/" in register_page.get_current_url()
    assert register_page.has_error_alert()
    assert "Username already taken." in register_page.get_error_message()
    assert not register_page.is_user_logged_in()


@pytest.mark.django_db(transaction=True)
def test_tc_auth_04_valid_login(browser, live_server, test_user):
    """
    TC-AUTH-04: Valid voter login & session establishment.
    Submitting correct credentials redirects to home with an active session.
    """
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()

    login_page.login(test_user.username, test_user.raw_password)

    # Verifications
    assert login_page.wait_for_user_logged_in()
    assert login_page.is_user_logged_in()
    assert test_user.username in login_page.get_logged_in_username()


@pytest.mark.django_db(transaction=True)
def test_tc_auth_05_deep_link_redirect(browser, live_server, test_user, active_election):
    """
    TC-AUTH-05: Deep-link authentication guard and redirection.
    Accessing a protected voting booth while unauthenticated redirects to /login/?next=...
    Upon successful login, user is forwarded directly to the requested election booth.
    """
    target_path = f"/election/{active_election.id}/"
    browser.get(f"{live_server.url}{target_path}")

    login_page = LoginPage(browser, live_server.url)

    # Verify redirected to login with next parameter
    assert "/login/" in browser.current_url
    assert f"next={target_path}" in browser.current_url

    # Authenticate
    login_page.login(test_user.username, test_user.raw_password)

    # Verify forwarded to requested voting booth
    booth_page = VotingBoothPage(browser, live_server.url)
    assert booth_page.wait_for_url_contains(target_path)
    assert booth_page.is_visible(VotingBoothPage.VOTE_FORM)
    assert booth_page.get_election_title() == active_election.title
