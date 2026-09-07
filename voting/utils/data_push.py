import hashlib
import json
import logging
import uuid
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from voting.models import Election, Candidate, Vote, SecurityLog, ScheduledDataPush
from voting.utils.encryption import encrypt_vote
from voting.utils.blockchain import verify_election_blockchain

logger = logging.getLogger('chainvote.datapush')

INTERVAL_HOURS = 96  # 4 days (96 hours)


def execute_automatic_data_push(force=False):
    """
    Executes an automated backend data push every 4 days (96 hours).
    
    1. Checks the timestamp of the last successful push.
    2. Skips if less than 96 hours have passed (unless force=True).
    3. Runs an atomic transaction to:
       - Cryptographically audit existing election chains.
       - Mine an immutable checkpoint block on the System Audit Ledger.
       - Log a SOC security event.
       - Record the successful push execution in ScheduledDataPush.
    4. Handles failures gracefully and logs errors.
    """
    now = timezone.now()
    logger.info("Automatic data push started")

    # 1. Check last successful push timestamp
    last_successful = (
        ScheduledDataPush.objects.filter(status=ScheduledDataPush.STATUS_SUCCESS)
        .order_by('-executed_at')
        .first()
    )

    if last_successful and last_successful.executed_at:
        logger.info(f"Last successful push: {last_successful.executed_at.isoformat()}")
        elapsed = now - last_successful.executed_at
        if not force and elapsed < timedelta(hours=INTERVAL_HOURS):
            remaining = timedelta(hours=INTERVAL_HOURS) - elapsed
            hours_left = round(remaining.total_seconds() / 3600, 2)
            logger.info("Automatic data push skipped - 4 days have not elapsed")
            return {
                "status": "skipped",
                "message": f"Automatic data push skipped - 4 days have not elapsed. Next push eligible in {hours_left} hours.",
                "last_successful_push": last_successful.executed_at.isoformat(),
                "next_eligible_push": (last_successful.executed_at + timedelta(hours=INTERVAL_HOURS)).isoformat(),
                "hours_remaining": hours_left,
            }
    else:
        logger.info("Last successful push: None (Initial run)")

    # 2. Execute atomic data creation
    try:
        with transaction.atomic():
            # (A) Cryptographic Ledger Integrity Audit across existing elections
            elections = Election.objects.all()
            scanned_elections = []
            total_blocks_audited = 0
            all_intact = True

            for election in elections:
                is_valid, msg = verify_election_blockchain(election)
                block_count = election.votes.count()
                total_blocks_audited += block_count
                scanned_elections.append({
                    "election_id": election.id,
                    "title": election.title,
                    "blocks": block_count,
                    "is_valid": is_valid,
                    "verification_message": msg,
                })
                if not is_valid:
                    all_intact = False

            # (B) Official System Audit & Protocol Ledger
            audit_election, _ = Election.objects.get_or_create(
                title="ChainVote Network Audit & Protocol Ledger",
                defaults={
                    "description": (
                        "Autonomous immutable cryptographic ledger recording 4-day system integrity checkpoints, "
                        "network consensus, and blockchain validation proofs."
                    ),
                    "start_time": now - timedelta(days=365),
                    "end_time": now + timedelta(days=3650),
                }
            )

            audit_candidate, _ = Candidate.objects.get_or_create(
                election=audit_election,
                name="Network Ledger Integrity Verified",
                defaults={
                    "description": "Cryptographic proof that all election blocks and SHA-256 links are intact and untampered."
                }
            )

            # (C) Mine new audit block into the blockchain
            cycle_id = f"SYSTEM_AUDIT_CYCLE_{now.strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:12]}"
            voter_hash = hashlib.sha256(cycle_id.encode()).hexdigest()
            encrypted_ballot = encrypt_vote(audit_candidate.id)

            # Creating the Vote triggers Vote.save(), which:
            # - links previous_hash to the latest block
            # - generates the SHA-256 block_hash
            new_block = Vote.objects.create(
                election=audit_election,
                encrypted_vote=encrypted_ballot,
                voter_hash=voter_hash,
                voter_ip="127.0.0.1"
            )

            # (D) Record SOC Security / Threat Dashboard Event
            SecurityLog.objects.create(
                level='WARNING',
                action='Periodic 4-Day Blockchain Audit Sealed',
                ip_address='127.0.0.1',
                details=(
                    f"Automated 4-day ledger push succeeded. Mined checkpoint block: {new_block.short_hash()}. "
                    f"Scanned {len(scanned_elections)} election ledgers ({total_blocks_audited} total blocks). "
                    f"Ledger integrity intact: {all_intact}."
                )
            )

            # (E) Record tracking in ScheduledDataPush
            push_details = {
                "cycle": cycle_id,
                "audit_election_id": audit_election.id,
                "checkpoint_block_id": new_block.id,
                "checkpoint_block_hash": new_block.block_hash,
                "checkpoint_previous_hash": new_block.previous_hash,
                "elections_scanned": len(scanned_elections),
                "total_blocks_audited": total_blocks_audited,
                "all_ledgers_intact": all_intact,
            }

            ScheduledDataPush.objects.create(
                push_type='SYSTEM_LEDGER_AUDIT',
                status=ScheduledDataPush.STATUS_SUCCESS,
                executed_at=now,
                last_successful_push=now,
                details=json.dumps(push_details, indent=2),
                error_message=""
            )

        logger.info("Automatic data push completed successfully")
        return {
            "status": "success",
            "message": "Automatic data push completed successfully",
            "executed_at": now.isoformat(),
            "next_eligible_push": (now + timedelta(hours=INTERVAL_HOURS)).isoformat(),
            "details": push_details,
        }

    except Exception as exc:
        err_msg = str(exc)
        logger.error(f"Automatic data push failed: {err_msg}")
        ScheduledDataPush.objects.create(
            push_type='SYSTEM_LEDGER_AUDIT',
            status=ScheduledDataPush.STATUS_FAILED,
            executed_at=now,
            last_successful_push=last_successful.executed_at if last_successful else None,
            details="Atomic transaction failed and rolled back.",
            error_message=err_msg
        )
        return {
            "status": "failed",
            "message": f"Automatic data push failed: {err_msg}",
            "executed_at": now.isoformat(),
            "error": err_msg,
        }
