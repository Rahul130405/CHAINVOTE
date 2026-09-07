import logging
import random
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from voting.models import Election, Candidate, CandidateAutomationState

logger = logging.getLogger('chainvote.candidate_automation')

INTERVAL_HOURS = 144  # 6 days (144 hours)

# Predefined candidate pool for periodic additions
CANDIDATE_POOL = [
    ("Neha Kapoor", "Future India Alliance"),
    ("Arjun Singh", "People's Reform Party"),
    ("Ananya Gupta", "Digital Democracy Front"),
    ("Vikram Rao", "National Progress Party"),
    ("Kavya Nair", "Citizens First"),
    ("Aditya Malhotra", "Development Alliance"),
    ("Meera Joshi", "Democratic Unity Front"),
    ("Rahul Khanna", "People's Voice Party"),
    ("Ishita Sharma", "New India Movement"),
    ("Karan Verma", "Progressive India"),
]

DYNAMIC_FIRST_NAMES = [
    "Siddharth", "Aanya", "Rishi", "Tara", "Dev", "Pooja", "Varun", "Simran", "Nikhil", "Sneha",
    "Kabir", "Diya", "Reyansh", "Anika", "Shaurya", "Myra", "Advait", "Tanvi", "Vihaan", "Khushi"
]

DYNAMIC_LAST_NAMES = [
    "Patel", "Reddy", "Choudhury", "Bose", "Deshmukh", "Menon", "Kapoor", "Singhania", "Mukherjee", "Bhatia",
    "Nair", "Iyer", "Saxena", "Malik", "Pandey", "Kulkarni", "Banerjee", "Pillai", "Goswami", "Chatterjee"
]

DYNAMIC_PARTIES = [
    "United Democratic Coalition",
    "National Renewal Movement",
    "Forward India Party",
    "Citizens Action Front",
    "Youth Leadership Party",
    "Progressive Democratic Forum",
    "Digital Freedom League",
    "New Generation Alliance"
]


def ensure_initial_election_data():
    """
    Ensures that at least one realistic active election with candidates exists in the database.
    If no active user election exists, initializes the 2026 National Election.
    """
    now = timezone.now()

    active_elections = (
        Election.objects.filter(start_time__lte=now, end_time__gte=now)
        .exclude(title='ChainVote Network Audit & Protocol Ledger')
    )

    if active_elections.exists():
        election = active_elections.order_by('-start_time').first()
        # If the active election has no candidates, populate them
        if not election.candidates.exists():
            _create_initial_candidates(election)
        return election

    # Create the default 2026 National Election
    election, _ = Election.objects.get_or_create(
        title="2026 National Election",
        defaults={
            "description": "National Digital Democracy Election powered by cryptographic ledgers.",
            "start_time": now - timedelta(days=1),
            "end_time": now + timedelta(days=60),
        }
    )

    # Ensure status is active by adjusting start/end times if necessary
    if election.end_time <= now or election.start_time > now:
        election.start_time = now - timedelta(days=1)
        election.end_time = now + timedelta(days=60)
        election.save(update_fields=['start_time', 'end_time'])

    _create_initial_candidates(election)
    return election


def _create_initial_candidates(election):
    """Populates the initial 3 demo candidates for an election."""
    initial_candidates = [
        ("Aarav Sharma", "Digital India Party"),
        ("Priya Verma", "National Reform Alliance"),
        ("Rohan Mehta", "People's Development Front"),
    ]
    for name, desc in initial_candidates:
        Candidate.objects.get_or_create(
            election=election,
            name=name,
            defaults={"description": desc}
        )


def get_active_target_election():
    """
    Retrieves the primary active election for candidate automation.
    If none exists, initializes the 2026 National Election.
    """
    now = timezone.now()
    election = (
        Election.objects.filter(start_time__lte=now, end_time__gte=now)
        .exclude(title='ChainVote Network Audit & Protocol Ledger')
        .order_by('-start_time')
        .first()
    )
    if not election:
        election = ensure_initial_election_data()
    return election


def _pick_next_candidate(existing_names):
    """
    Selects the next unused candidate from CANDIDATE_POOL.
    If all pool candidates are used, generates a unique realistic candidate.
    """
    for name, party in CANDIDATE_POOL:
        if name not in existing_names:
            return name, party

    # Fallback: Generate a unique dynamic candidate name
    for _ in range(100):
        first = random.choice(DYNAMIC_FIRST_NAMES)
        last = random.choice(DYNAMIC_LAST_NAMES)
        full_name = f"{first} {last}"
        if full_name not in existing_names:
            party = random.choice(DYNAMIC_PARTIES)
            return full_name, party

    # Ultimate fallback with counter
    counter = len(existing_names) + 1
    return f"Candidate {counter}", "Independent Digital Coalition"


def execute_candidate_automation(force=False):
    """
    Executes automated candidate generation:
    1. Finds the active target election.
    2. Checks if 6 days (144 hours) have elapsed since the last automated candidate.
    3. If elapsed (or initial run or force=True), selects an unused candidate and inserts it.
    4. Idempotent: Never creates duplicate candidates for the same 6-day cycle.
    """
    now = timezone.now()
    election = get_active_target_election()

    logger.info(f"Checking candidate automation for election: {election.title}")

    # Check last automated generation
    last_state = (
        CandidateAutomationState.objects.filter(election=election)
        .order_by('-last_generated_at')
        .first()
    )

    if last_state and not force:
        elapsed = now - last_state.last_generated_at
        if elapsed < timedelta(hours=INTERVAL_HOURS):
            remaining = timedelta(hours=INTERVAL_HOURS) - elapsed
            hours_left = round(remaining.total_seconds() / 3600, 2)
            msg = f"Candidate automation skipped - 6 days have not elapsed. Next candidate eligible in {hours_left} hours."
            logger.info(msg)
            return {
                "status": "skipped",
                "message": msg,
                "election": election.title,
                "election_id": election.id,
                "last_generated_at": last_state.last_generated_at.isoformat(),
                "next_eligible_at": (last_state.last_generated_at + timedelta(hours=INTERVAL_HOURS)).isoformat(),
                "hours_remaining": hours_left,
                "current_candidate_count": election.candidates.count(),
            }

    # Generate next candidate atomically
    try:
        with transaction.atomic():
            existing_names = set(election.candidates.values_list('name', flat=True))
            name, party = _pick_next_candidate(existing_names)

            new_candidate = Candidate.objects.create(
                election=election,
                name=name,
                description=party
            )

            state = CandidateAutomationState.objects.create(
                election=election,
                candidate=new_candidate,
                last_generated_at=now,
                details=f"Automated candidate generated: {name} ({party})"
            )

        cache.delete('home_landing_context')
        logger.info(f"Successfully created candidate '{new_candidate.name}' for election '{election.title}'.")
        return {
            "status": "success",
            "message": f"Successfully generated new candidate '{new_candidate.name}' for election '{election.title}'.",
            "election": election.title,
            "election_id": election.id,
            "candidate": {
                "id": new_candidate.id,
                "name": new_candidate.name,
                "party": new_candidate.description,
            },
            "generated_at": now.isoformat(),
            "next_eligible_at": (now + timedelta(hours=INTERVAL_HOURS)).isoformat(),
            "total_candidates": election.candidates.count(),
        }

    except Exception as exc:
        err_msg = str(exc)
        logger.error(f"Candidate automation failed: {err_msg}")
        return {
            "status": "failed",
            "message": f"Candidate automation failed: {err_msg}",
            "election": election.title,
            "error": err_msg,
        }
