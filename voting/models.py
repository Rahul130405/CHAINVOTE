import hashlib
import json
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

class Election(models.Model):
    STATUS_UPCOMING = 'upcoming'
    STATUS_ACTIVE = 'active'
    STATUS_ENDED = 'ended'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time', 'end_time'], name='idx_election_active'),
            models.Index(fields=['-start_time'], name='idx_election_start'),
        ]

    def __str__(self):
        return self.title

    @property
    def status(self):
        now = timezone.now()
        if now < self.start_time:
            return self.STATUS_UPCOMING
        elif now > self.end_time:
            return self.STATUS_ENDED
        else:
            return self.STATUS_ACTIVE

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def total_votes(self):
        if hasattr(self, 'total_votes_count'):
            return self.total_votes_count
        return self.votes.count()


class Candidate(models.Model):
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='candidates'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['election', 'name']  # No duplicate names per election
        indexes = [
            models.Index(fields=['election', 'name'], name='idx_candidate_election_name'),
        ]

    def __str__(self):
        return f"{self.name} ({self.election.title})"


class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    encrypted_vote = models.CharField(max_length=255)
    voter_hash = models.CharField(max_length=64)
    voter_ip = models.GenericIPAddressField(null=True, blank=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    # 🔗 BLOCKCHAIN FIELDS
    previous_hash = models.CharField(max_length=64, default="0"*64)
    block_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        unique_together = ['election', 'voter_hash']
        indexes = [
            models.Index(fields=['election', 'id'], name='idx_vote_election_id'),
            models.Index(fields=['election', '-id'], name='idx_vote_election_latest'),
            models.Index(fields=['voted_at'], name='idx_vote_voted_at'),
        ]

    def __str__(self):
        return f"Encrypted vote in {self.election.title}"

    def short_hash(self):
        return self.block_hash[:10] + "..." if self.block_hash else "Pending..."

    def generate_hash(self):
        """Creates a SHA-256 hash of the vote's data PLUS the previous vote's hash."""
        vote_data = {
            "election_id": self.election.id,
            "encrypted_vote": self.encrypted_vote,
            "voter_hash": self.voter_hash,
            "previous_hash": self.previous_hash
        }
        block_string = json.dumps(vote_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    # 🛡️ THE BULLETPROOF FIX: Override the save method
    def save(self, *args, **kwargs):
        # Only run this logic if it's a BRAND NEW vote being created
        if not self.pk: 
            with transaction.atomic():
                # 1. Find the last vote in this specific election to link to
                last_vote = Vote.objects.filter(election=self.election).select_for_update().order_by('-id').first()
                
                # 2. Set the previous hash
                if last_vote and last_vote.block_hash:
                    self.previous_hash = last_vote.block_hash
                else:
                    self.previous_hash = "0" * 64
                
                # 3. Generate this block's hash
                self.block_hash = self.generate_hash()
                
        # Actually save it to the database
        super(Vote, self).save(*args, **kwargs)


class SecurityLog(models.Model):
    LEVEL_CHOICES = [
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical Breach Attempt')
    ]
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='WARNING')
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp'], name='idx_seclog_timestamp'),
            models.Index(fields=['level', '-timestamp'], name='idx_seclog_level_time'),
        ]

    def __str__(self):
        return f"[{self.level}] {self.action} - {self.ip_address}"


class ScheduledDataPush(models.Model):
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_SKIPPED = 'SKIPPED'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_SKIPPED, 'Skipped (Interval Not Reached)'),
        (STATUS_FAILED, 'Failed'),
    ]

    push_type = models.CharField(max_length=100, default='SYSTEM_LEDGER_AUDIT')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    executed_at = models.DateTimeField(default=timezone.now)
    last_successful_push = models.DateTimeField(null=True, blank=True)
    details = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-executed_at']
        verbose_name = 'Scheduled Data Push'
        verbose_name_plural = 'Scheduled Data Pushes'
        indexes = [
            models.Index(fields=['status', '-executed_at'], name='idx_datapush_status_time'),
        ]

    def __str__(self):
        return f"[{self.status}] {self.push_type} - {self.executed_at.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def next_eligible_push(self):
        from datetime import timedelta
        if self.status == self.STATUS_SUCCESS and self.executed_at:
            return self.executed_at + timedelta(hours=96)
        return None


class CandidateAutomationState(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidate_automations')
    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, blank=True)
    last_generated_at = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_generated_at']
        verbose_name = 'Candidate Automation Log'
        verbose_name_plural = 'Candidate Automation Logs'
        indexes = [
            models.Index(fields=['election', '-last_generated_at'], name='idx_candauto_elec_time'),
        ]

    def __str__(self):
        c_name = self.candidate.name if self.candidate else "Unknown"
        return f"Added {c_name} for {self.election.title} at {self.last_generated_at.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def next_eligible_at(self):
        from datetime import timedelta
        return self.last_generated_at + timedelta(days=6)
