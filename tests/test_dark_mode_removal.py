"""
Tests for Requirement 1: Complete Removal of Dark Mode.

Verifies:
1. No dark/light theme toggle button exists on any page (voter, booth, admin/SOC, results, explorer).
2. The <html> element does not have the 'dark' CSS class.
3. If localStorage had 'color-theme': 'dark', page initialization clears it.
4. English/Hindi bilingual toggle and localStorage persistence remain fully intact.
5. Static responses across all URLs contain zero theme toggle buttons or darkMode class configuration.
"""

import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By

from tests.pages.base_page import BasePage


# ─────────────────────────────────────────────────────────────
# 1. SERVER-SIDE / TEMPLATE CONTENT TESTS
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_templates_do_not_contain_theme_toggle_or_dark_config(client, test_user, active_election):
    """Verifies server responses for all pages do not contain theme-toggle or darkMode config."""
    # Unauthenticated pages
    anon_urls = [
        reverse("home"),
        reverse("login"),
        reverse("register"),
        reverse("results", kwargs={"election_id": active_election.id}),
    ]
    for url in anon_urls:
        response = client.get(url)
        assert response.status_code == 200, f"Failed GET for {url}"
        content = response.content.decode("utf-8")
        assert 'id="theme-toggle"' not in content, f"theme-toggle found in {url}"
        assert "darkMode: 'class'" not in content, f"darkMode: 'class' found in {url}"
        assert '<html lang="en" class="dark">' not in content, f"dark html class found in {url}"

    # Authenticated pages (voting booth, blockchain explorer)
    client.force_login(test_user)
    auth_urls = [
        reverse("election_detail", kwargs={"election_id": active_election.id}),
        reverse("blockchain_explorer", kwargs={"election_id": active_election.id}),
    ]
    for url in auth_urls:
        response = client.get(url)
        assert response.status_code == 200, f"Failed GET for {url}"
        content = response.content.decode("utf-8")
        assert 'id="theme-toggle"' not in content, f"theme-toggle found in {url}"
        assert "darkMode: 'class'" not in content, f"darkMode: 'class' found in {url}"
        assert '<html lang="en" class="dark">' not in content, f"dark html class found in {url}"


@pytest.mark.django_db
def test_threat_dashboard_does_not_contain_theme_toggle(admin_client):
    """Verifies threat dashboard (SOC) does not contain theme toggle or darkMode config."""
    response = admin_client.get(reverse("threat_dashboard"))
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'id="theme-toggle"' not in content
    assert "darkMode: 'class'" not in content
    assert '<html lang="en" class="dark">' not in content


# ─────────────────────────────────────────────────────────────
# 2. BROWSER TESTS (END-TO-END)
# ─────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_browser_pages_render_without_dark_mode_and_no_toggle(browser, live_server, active_election):
    """Verifies in a live browser that every primary page renders in light mode without theme toggle."""
    test_urls = [
        ("/", "Home"),
        ("/login/", "Login"),
        ("/register/", "Register"),
        (f"/election/{active_election.id}/", "Booth"),
        (f"/results/{active_election.id}/", "Results"),
        (f"/blockchain/{active_election.id}/", "Ledger"),
    ]

    base_page = BasePage(browser, live_server.url)

    for path, name in test_urls:
        browser.get(live_server.url + path)
        assert not base_page.has_theme_toggle(), f"{name} ({path}) must not have a theme toggle button"
        assert not base_page.is_dark_mode(), f"{name} ({path}) must not have 'dark' class on html element"


@pytest.mark.django_db(transaction=True)
def test_browser_clears_stale_dark_mode_localstorage(browser, live_server):
    """Verifies that even if localStorage previously contained 'color-theme': 'dark', it is cleared."""
    browser.get(live_server.url + "/")
    # Artificially inject stale dark mode preference
    browser.execute_script("localStorage.setItem('color-theme', 'dark');")
    assert browser.execute_script("return localStorage.getItem('color-theme');") == "dark"

    # Reload page
    browser.refresh()

    base_page = BasePage(browser, live_server.url)
    assert not base_page.is_dark_mode(), "Page must not apply dark mode despite stale localStorage"
    stored_theme = browser.execute_script("return localStorage.getItem('color-theme');")
    assert stored_theme is None, f"Expected color-theme to be removed, but got {stored_theme}"


@pytest.mark.django_db(transaction=True)
def test_browser_language_toggle_persists_independently(browser, live_server):
    """Verifies language toggle works and persists independently after dark mode removal."""
    browser.get(live_server.url + "/")
    base_page = BasePage(browser, live_server.url)

    # Initial language is English
    assert base_page.get_current_language() == "en"

    # Switch to Hindi
    base_page.toggle_language()
    assert base_page.get_current_language() == "hi"

    # Navigate to login and verify Hindi persistence
    browser.get(live_server.url + "/login/")
    assert base_page.get_current_language() == "hi"

    # Switch back to English
    base_page.toggle_language()
    assert base_page.get_current_language() == "en"
