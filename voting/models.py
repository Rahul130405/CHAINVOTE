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

    def __str__(self):
        return f"[{self.level}] {self.action} - {self.ip_address}"