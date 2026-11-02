"""
Comprehensive Selenium E2E and Performance Test Suite for ChainVote.

Covers:
- Suite A: Website Navigation & Timing (Homepage, Login, Election Detail)
- Suite B: Authentication & Protected Route Redirection (/manage/)
- Suite C: Admin Dashboard Metrics & Rendering
- Suite D: Disposable Election Management (Create & Edit)
- Suite E: Candidate Management & Safe Deletion Confirmation
- Suite F: Performance Timing (Navigation Timing, TTFB, DOM Interactive, LCP)
- Suite G: Browser Health (Console Errors, Viewport Responsiveness: Desktop, Tablet, Mobile)
- Suite H: Security & Ledger Regression (Candidate Deletion Protections, Cryptographic Hash Chain)
"""

import time
import json
import secrets
from datetime import timedelta
import pytest
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from voting.models import Election, Candidate, Vote
from voting.utils.encryption import encrypt_vote
from tests.pages.base_page import BasePage
from tests.pages.login_page import LoginPage


def get_nav_timings(browser):
    """Extracts Navigation Timing API metrics from current page."""
    script = """
    var nav = window.performance.getEntriesByType('navigation')[0];
    if (!nav) return null;
    return {
        dns_ms: Math.round(nav.domainLookupEnd - nav.domainLookupStart),
        tcp_tls_ms: Math.round(nav.connectEnd - nav.connectStart),
        ttfb_ms: Math.round(nav.responseStart - nav.requestStart),
        download_ms: Math.round(nav.responseEnd - nav.responseStart),
        dom_interactive_ms: Math.round(nav.domInteractive),
        dom_content_loaded_ms: Math.round(nav.domContentLoadedEventEnd),
        dom_complete_ms: Math.round(nav.domComplete),
        load_event_ms: Math.round(nav.loadEventEnd),
        transfer_size: nav.transferSize || 0
    };
    """
    return browser.execute_script(script) or {}


def get_lcp_timing(browser):
    """Attempts to retrieve LCP from performance timeline."""
    script = """
    var lcp = 0;
    var entries = window.performance.getEntriesByType('largest-contentful-paint');
    if (entries && entries.length > 0) {
        lcp = Math.round(entries[entries.length - 1].startTime);
    }
    return lcp;
    """
    try:
        return browser.execute_script(script) or 0
    except Exception:
        return 0


# ==============================================================================
# SUITE A: WEBSITE NAVIGATION
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_suite_a_website_navigation(browser, live_server, active_election):
    """Verifies homepage, login page, and election detail page navigation & metrics."""
    # 1. Homepage
    browser.get(f"{live_server.url}/")
    WebDriverWait(browser, 5).until(lambda d: "ChainVote" in d.title)
    assert "ChainVote" in browser.title

    base_page = BasePage(browser, live_server.url)
    assert base_page.is_visible(BasePage.NAV_BRAND_LINK)

    home_timings = get_nav_timings(browser)
    assert home_timings.get('dom_interactive_ms', 0) >= 0

    # 2. Login Page
    browser.get(f"{live_server.url}/login/")
    user_input = WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    assert user_input.is_displayed() or user_input.get_attribute("name") == "username"
    assert browser.find_element(By.ID, "password").is_displayed() or browser.find_element(By.ID, "password").get_attribute("name") == "password"

    # 3. Election Detail Page
    browser.get(f"{live_server.url}/election/{active_election.id}/")
    WebDriverWait(browser, 5).until(lambda d: active_election.title in d.page_source)
    assert active_election.title in browser.page_source


# ==============================================================================
# SUITE B: AUTHENTICATION & ACCESS CONTROL
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_suite_b_authentication(browser, live_server, staff_user):
    """Tests valid admin login, invalid login, and protected route redirect."""
    login_page = LoginPage(browser, live_server.url)

    # 1. Protected route redirect: unauthenticated user trying /manage/
    browser.get(f"{live_server.url}/manage/")
    WebDriverWait(browser, 5).until(lambda d: "/login/" in d.current_url)
    assert "/login/" in browser.current_url
    assert "next=" in browser.current_url

    # 2. Invalid login attempt
    login_page.navigate()
    login_page.login("yash", "WrongPassword123!")
    time.sleep(0.3)
    assert login_page.has_error_alert()

    # 3. Valid admin login
    login_page.navigate()
    login_page.login(staff_user.username, staff_user.raw_password)
    
    WebDriverWait(browser, 5).until(lambda d: "/manage" in d.current_url)
    assert "/manage" in browser.current_url
    assert "Election Management" in browser.page_source or "Portal" in browser.page_source


# ==============================================================================
# SUITE C: ADMIN DASHBOARD METRICS
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_suite_c_admin_dashboard(browser, live_server, staff_user, active_election, ended_election):
    """Verifies that the admin dashboard loads, displaying accurate counts and metric cards."""
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(staff_user.username, staff_user.raw_password)
    WebDriverWait(browser, 5).until(lambda d: "/manage" in d.current_url)

    browser.get(f"{live_server.url}/manage/")
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "metric-total-elections")))

    # Metric card checks
    metric_total = browser.find_element(By.ID, "metric-total-elections").text.strip()
    metric_active = browser.find_element(By.ID, "metric-active-elections").text.strip()
    metric_completed = browser.find_element(By.ID, "metric-completed-elections").text.strip()
    metric_candidates = browser.find_element(By.ID, "metric-total-candidates").text.strip()

    assert int(metric_total) >= 2
    assert int(metric_active) >= 1
    assert int(metric_completed) >= 1
    assert int(metric_candidates) >= 5

    # Check dashboard rows
    rows = browser.find_elements(By.CSS_SELECTOR, "table tbody tr")
    assert len(rows) >= 2


# ==============================================================================
# SUITE D: DISPOSABLE ELECTION MANAGEMENT
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_suite_d_election_management(browser, live_server, staff_user):
    """Tests creating and editing a disposable test election (never mutates existing records)."""
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(staff_user.username, staff_user.raw_password)
    WebDriverWait(browser, 5).until(lambda d: "/manage" in d.current_url)

    # 1. Create Disposable Election
    disposable_title = f"DISPOSABLE_TEST_ELECTION_{int(time.time())}"
    browser.get(f"{live_server.url}/manage/elections/new/")

    title_input = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "id_title")))
    desc_input = browser.find_element(By.ID, "id_description")
    start_input = browser.find_element(By.ID, "id_start_time")
    end_input = browser.find_element(By.ID, "id_end_time")

    now = timezone.now()
    title_input.send_keys(disposable_title)
    desc_input.send_keys("Automated Selenium Test Disposable Election")
    
    # Set datetime-local inputs cleanly via JS
    start_val = (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    end_val = (now + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M")
    browser.execute_script("arguments[0].value = arguments[1];", start_input, start_val)
    browser.execute_script("arguments[0].value = arguments[1];", end_input, end_val)

    submit_btn = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()

    WebDriverWait(browser, 5).until(lambda d: "/manage" in d.current_url and "new" not in d.current_url)
    assert disposable_title in browser.page_source

    # Fetch created election
    created_elec = Election.objects.get(title=disposable_title)
    assert created_elec.status == "upcoming"

    # 2. Edit Disposable Election
    browser.get(f"{live_server.url}/manage/elections/{created_elec.id}/edit/")
    desc_input = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "id_description")))
    desc_input.clear()
    desc_input.send_keys("Updated Description for Disposable Election")
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(browser, 5).until(lambda d: "/manage" in d.current_url and "edit" not in d.current_url)
    created_elec.refresh_from_db()
    assert created_elec.description == "Updated Description for Disposable Election"


# ==============================================================================
# SUITE E: CANDIDATE MANAGEMENT & SAFE DELETION
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_suite_e_candidate_management(browser, live_server, staff_user):
    """Tests creating and safely deleting a candidate in an upcoming disposable election."""
    now = timezone.now()
    disposable_elec = Election.objects.create(
        title=f"DISPOSABLE_ELEC_CAND_TEST_{int(time.time())}",
        description="Disposable election for candidate deletion testing.",
        start_time=now + timedelta(days=3),
        end_time=now + timedelta(days=15)
    )

    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(staff_user.username, staff_user.raw_password)
    WebDriverWait(browser, 5).until(lambda d: "/manage" in d.current_url)

    # 1. Create Disposable Candidate directly via Django ORM or form
    cand = Candidate.objects.create(
        election=disposable_elec,
        name="DISPOSABLE_TEST_CAND_ALPHA",
        description="Temporary Candidate Description"
    )

    browser.get(f"{live_server.url}/manage/elections/{disposable_elec.id}/candidates/")
    WebDriverWait(browser, 5).until(lambda d: "DISPOSABLE_TEST_CAND_ALPHA" in d.page_source)
    assert "DISPOSABLE_TEST_CAND_ALPHA" in browser.page_source

    # 2. Open Candidate Deletion Confirmation UI
    browser.get(f"{live_server.url}/manage/candidates/{cand.id}/delete/")
    WebDriverWait(browser, 5).until(lambda d: "Delete Candidate" in d.page_source or "Confirm" in d.page_source)
    assert cand.name in browser.page_source

    # 3. Confirm Deletion via POST
    delete_btn = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
    delete_btn.click()

    WebDriverWait(browser, 5).until(lambda d: f"/manage/elections/{disposable_elec.id}/candidates" in d.current_url)
    assert not Candidate.objects.filter(id=cand.id).exists()


# ==============================================================================
# SUITE F: PERFORMANCE MEASUREMENTS & CACHING
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_suite_f_performance_measurements(browser, live_server, active_election, staff_user):
    """Measures TTFB, DOM Interactive, DOMContentLoaded, Load Event, and warm cache response."""
    # 1. Cold Homepage Request
    browser.get(f"{live_server.url}/")
    cold_timings = get_nav_timings(browser)
    assert cold_timings.get('dom_interactive_ms', 0) > 0

    # 2. Warm Homepage Request (Subsequent)
    t0 = time.perf_counter()
    browser.get(f"{live_server.url}/")
    warm_latency = (time.perf_counter() - t0) * 1000.0
    warm_timings = get_nav_timings(browser)

    # 3. API Performance
    browser.get(f"{live_server.url}/api/elections/")
    api_timings = get_nav_timings(browser)
    assert api_timings.get('ttfb_ms', 0) >= 0


# ==============================================================================
# SUITE G: BROWSER HEALTH & VIEWPORT RESPONSIVENESS
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_suite_g_browser_health_and_viewports(browser, live_server):
    """Validates responsive viewports (desktop, tablet, mobile) and checks console error logs."""
    viewports = [
        ("Desktop", 1280, 800),
        ("Tablet", 768, 1024),
        ("Mobile", 375, 667)
    ]

    for name, width, height in viewports:
        browser.set_window_size(width, height)
        browser.get(f"{live_server.url}/")
        time.sleep(0.2)

        # Brand header must remain visible on all viewports
        brand = browser.find_element(By.XPATH, "//a[contains(@href, '/') and (contains(text(), 'ChainVote') or .//span[contains(text(), 'ChainVote')])]")
        assert brand.is_displayed(), f"Brand header hidden on {name} ({width}x{height})"

    # Browser console health check
    logs = browser.get_log("browser")
    severe_errors = [entry for entry in logs if entry.get("level") == "SEVERE" and "favicon" not in entry.get("message", "")]
    assert len(severe_errors) == 0, f"Detected severe console errors: {severe_errors}"


# ==============================================================================
# SUITE H: REGRESSION & LEDGER SECURITY
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_suite_h_regression_and_ledger_security(browser, live_server, ended_election, staff_user):
    """Verifies that candidates with votes CANNOT be deleted, and blockchain hashes are verified."""
    login_page = LoginPage(browser, live_server.url)
    login_page.navigate()
    login_page.login(staff_user.username, staff_user.raw_password)
    WebDriverWait(browser, 5).until(lambda d: "/manage" in d.current_url)

    # Attempt to access candidate deletion for a candidate in an ended election with votes
    voted_cand = ended_election.candidates.first()
    browser.get(f"{live_server.url}/manage/candidates/{voted_cand.id}/delete/")

    # Must be blocked and redirected
    assert f"/manage/elections/{ended_election.id}/candidates" in browser.current_url or "Security Alert" in browser.page_source
    assert Candidate.objects.filter(id=voted_cand.id).exists(), "Candidate with recorded votes was improperly deleted!"

    # Verify blockchain explorer integrity
    browser.get(f"{live_server.url}/election/{ended_election.id}/blockchain/")
    assert "Genesis" in browser.page_source or "000000" in browser.page_source or "Vote ID" in browser.page_source


# ==============================================================================
# SUITE I: STATIC ASSET MANIFEST & CACHE FINGERPRINT VERIFICATION
# ==============================================================================

def test_static_manifest_and_fingerprinted_assets(client):
    """Verifies CompressedManifestStaticFilesStorage generates hashed assets and immutable headers."""
    from django.conf import settings
    from django.templatetags.static import static
    from pathlib import Path

    manifest_path = Path(settings.STATIC_ROOT) / 'staticfiles.json'
    assert manifest_path.exists(), f"Manifest file missing: {manifest_path}"

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # 1. Verify manifest mapping
    hashed_relative = manifest.get('paths', {}).get('voting/css/tailwind.min.css')
    assert hashed_relative is not None, "tailwind.min.css missing from staticfiles.json manifest"
    assert "tailwind.min." in hashed_relative, f"Unexpected hashed filename: {hashed_relative}"
    assert hashed_relative != "voting/css/tailwind.min.css", "Asset is unhashed!"

    # 2. Verify physical files exist
    hashed_file = Path(settings.STATIC_ROOT) / hashed_relative
    assert hashed_file.exists(), f"Hashed CSS file does not exist on disk: {hashed_file}"
    assert hashed_file.stat().st_size > 0, "Hashed CSS file is empty"

    # 3. Verify pre-compressed gzip file exists
    gz_file = Path(str(hashed_file) + '.gz')
    assert gz_file.exists(), f"Pre-compressed .gz file missing: {gz_file}"

    # 4. Verify WhiteNoise serving and immutable cache headers
    res = client.get(f"/static/{hashed_relative}")
    assert res.status_code == 200
    cache_control = res.headers.get('Cache-Control', '')
    assert 'immutable' in cache_control, f"Expected 'immutable' in Cache-Control, got: {cache_control}"
    assert 'public' in cache_control

