"""
Shared test harness and fixtures for CHAINVOTE Selenium test suite.

Provides:
- Headless Chrome WebDriver fixture with explicit wait helpers.
- Test user fixture with known credentials.
- Active election fixture with candidates for digital booth and live voting tests.
- Ended election fixture with pre-mined chained votes for results verification.
- Automatic cache clearing fixture to ensure isolated landing page metrics.
- Unique ID and username generation helpers.
"""

import hashlib
import os
import secrets
import uuid
from datetime import timedelta
import pytest

os.environ.setdefault("SE_OFFLINE", "true")
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from voting.models import Election, Candidate, Vote
from voting.utils.encryption import encrypt_vote


@pytest.fixture
def browser():
    """
    Selenium WebDriver fixture configured for headless Google Chrome.
    Uses Selenium Manager to automatically locate the installed Chrome binary.
    Configured with standard desktop viewport (1920x1080) and headless switches.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-pipe")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(20)

    yield driver

    driver.quit()


@pytest.fixture(autouse=True)
def clear_cache():
    """
    Flushes the cache ('chainvote_cache_table') before and after each test
    to eliminate cross-test cache contamination of landing page metrics.
    """
    try:
        from voting.views import _clear_fallback_failures
        _clear_fallback_failures('127.0.0.1')
    except Exception:
        pass
    try:
        cache.clear()
    except Exception:
        from django.core.management import call_command
        try:
            call_command('createcachetable')
            cache.clear()
        except Exception:
            pass
    yield
    try:
        from voting.views import _clear_fallback_failures
        _clear_fallback_failures('127.0.0.1')
    except Exception:
        pass
    try:
        cache.clear()
    except Exception:
        pass


@pytest.fixture
def test_user(db):
    """
    Creates an isolated standard voter account in the Django test database.
    Attaches raw_password for automated form login tests.
    """
    raw_pass = f"TestPass_{secrets.token_urlsafe(12)}!"
    user = User.objects.create_user(
        username="test_voter",
        password=raw_pass,
        email="test_voter@chainvote.test"
    )
    user.raw_password = raw_pass
    return user


@pytest.fixture
def staff_user(db):
    """
    Creates the authorized single-admin (yash) account in the test database.
    """
    raw_pass = f"StaffPass_{secrets.token_urlsafe(12)}!"
    user = User.objects.create_user(
        username="yash",
        password=raw_pass,
        email="yash@chainvote.test",
        is_staff=True
    )
    user.raw_password = raw_pass
    return user


@pytest.fixture
def other_staff_user(db):
    """
    Creates a non-yash staff account to verify it is strictly denied admin access.
    """
    raw_pass = f"OtherStaff_{secrets.token_urlsafe(12)}!"
    user = User.objects.create_user(
        username="other_staff",
        password=raw_pass,
        email="other_staff@chainvote.test",
        is_staff=True
    )
    user.raw_password = raw_pass
    return user


@pytest.fixture
def other_superuser(db):
    """
    Creates a non-yash superuser account to verify it is strictly denied admin access.
    """
    raw_pass = f"OtherSuper_{secrets.token_urlsafe(12)}!"
    user = User.objects.create_superuser(
        username="other_super",
        password=raw_pass,
        email="other_super@chainvote.test"
    )
    user.raw_password = raw_pass
    return user


@pytest.fixture
def active_election(db):
    """
    Creates an active election with 3 candidates in the isolated test database.
    start_time is in the past, end_time is in the future.
    """
    now = timezone.now()
    election = Election.objects.create(
        title="Active General Election 2026",
        description="Active test election for digital voting booth automation.",
        start_time=now - timedelta(days=1),
        end_time=now + timedelta(days=7),
    )
    Candidate.objects.create(
        election=election,
        name="Candidate Alpha",
        description="Party of Progress"
    )
    Candidate.objects.create(
        election=election,
        name="Candidate Beta",
        description="Alliance of Reform"
    )
    Candidate.objects.create(
        election=election,
        name="Candidate Gamma",
        description="Independent Coalition"
    )
    return election


@pytest.fixture
def ended_election(db):
    """
    Creates a concluded election with candidates and valid chained votes
    in the isolated test database.
    start_time and end_time are in the past.
    The votes are created sequentially so Vote.save() generates a verified SHA-256 chain.
    """
    now = timezone.now()
    election = Election.objects.create(
        title="Concluded Election 2024",
        description="Concluded test election with validly mined blocks for results tally verification.",
        start_time=now - timedelta(days=14),
        end_time=now - timedelta(days=1),
    )
    cand1 = Candidate.objects.create(
        election=election,
        name="Winner Candidate",
        description="Leader Party"
    )
    cand2 = Candidate.objects.create(
        election=election,
        name="Runner-up Candidate",
        description="Alliance Party"
    )

    # Cast 3 valid votes sequentially to build a valid cryptographic chain:
    # Vote 1 for cand1 (Winner)
    Vote.objects.create(
        election=election,
        encrypted_vote=encrypt_vote(cand1.id),
        voter_hash=hashlib.sha256("SYNTHETIC-VOTER-ID-1".encode()).hexdigest(),
        voter_ip="127.0.0.1",
    )
    # Vote 2 for cand1 (Winner)
    Vote.objects.create(
        election=election,
        encrypted_vote=encrypt_vote(cand1.id),
        voter_hash=hashlib.sha256("SYNTHETIC-VOTER-ID-2".encode()).hexdigest(),
        voter_ip="127.0.0.1",
    )
    # Vote 3 for cand2 (Runner-up)
    Vote.objects.create(
        election=election,
        encrypted_vote=encrypt_vote(cand2.id),
        voter_hash=hashlib.sha256("SYNTHETIC-VOTER-ID-3".encode()).hexdigest(),
        voter_ip="127.0.0.1",
    )
    return election


@pytest.fixture
def unique_voter_id():
    """
    Returns a callable factory generating unique synthetic voter IDs
    to avoid collisions across test runs without using real identities.
    Generates strictly valid 10-character alphanumeric IDs (A-Z, 0-9),
    guaranteeing at least one letter and at least one digit.
    """
    def _generator():
        return f"V1{uuid.uuid4().hex[:8].upper()}"
    return _generator


@pytest.fixture
def unique_username():
    """
    Returns a callable factory generating unique usernames
    for account registration tests.
    """
    def _generator():
        return f"voter_{uuid.uuid4().hex[:8]}"
    return _generator
