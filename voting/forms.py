import logging
from django import forms
from django.utils import timezone
from .models import Election, Candidate, Vote
from .utils.encryption import decrypt_vote

logger = logging.getLogger('chainvote.forms')


def candidate_has_recorded_votes(candidate):
    """
    Safely inspect the election's encrypted votes to determine if any vote
    was cast for this specific candidate.
    Returns True if at least one decrypted ballot matches candidate.id, False otherwise.
    Fails closed: If ANY ballot fails decryption, treats the ledger state as uncertain
    and returns True to block candidate deletion.
    Never exposes plain votes or voter identities.
    """
    if not candidate or not candidate.id or not candidate.election_id:
        return False

    votes = Vote.objects.filter(election_id=candidate.election_id).only('encrypted_vote')
    for vote in votes:
        try:
            decrypted_id = decrypt_vote(vote.encrypted_vote)
            if decrypted_id == candidate.id:
                return True
        except Exception:
            # FAIL-CLOSED: Decryption failure indicates corrupted, tampered, or unreadable ballot data.
            # Block candidate deletion to prevent destroying records for an unverified ballot.
            logger.warning(
                "Decryption failure encountered while checking recorded votes for candidate ID %s in election ID %s. "
                "Failing closed to block deletion.",
                candidate.id,
                candidate.election_id
            )
            return True
    return False


def election_has_recorded_votes_or_ledger(election):
    """
    Safely inspect the election to determine if any votes or blockchain ledger records exist.
    Returns True if at least one Vote record exists, False otherwise.
    Fails closed: Any database or query exception returns True to protect the ledger.
    """
    if not election or not getattr(election, 'id', None):
        return False
    try:
        return Vote.objects.filter(election_id=election.id).exists()
    except Exception as exc:
        logger.warning(
            "Exception encountered while checking recorded votes for election ID %s: %s. "
            "Failing closed to block deletion.",
            getattr(election, 'id', None),
            exc
        )
        return True


def get_election_deletion_blocking_reason(election):
    """
    Evaluates whether an election is eligible for safe deletion.
    An election may be deleted only if:
    - It has zero recorded votes.
    - It has no associated blockchain ledger entries.
    - It is not currently active.
    - Deletion does not violate system protocol integrity.

    Returns None if eligible for deletion; returns a descriptive reason string if blocked.
    Fails closed: Any uncertainty or ledger linkage blocks deletion.
    """
    if not election or not getattr(election, 'id', None):
        return "Invalid election instance."

    # 1. System protocol election cannot be deleted
    if getattr(election, 'title', '') == 'ChainVote Network Audit & Protocol Ledger':
        return "Protected system protocol election cannot be deleted."

    # 2. Cannot delete if recorded votes or blockchain ledger entries exist (Priority: protect immutable ledger)
    if election_has_recorded_votes_or_ledger(election):
        return "Deletion locked: Protected to preserve cryptographic ledger integrity. Recorded votes exist on the blockchain."

    # 3. Cannot delete an active election
    if election.status == Election.STATUS_ACTIVE:
        return "Deletion locked: Active elections currently receiving ballots cannot be deleted."

    return None


class ElectionForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white/90 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-all shadow-sm',
            },
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white/90 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-all shadow-sm',
            },
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )

    class Meta:
        model = Election
        fields = ['title', 'description', 'start_time', 'end_time']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white/90 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-all shadow-sm',
                'placeholder': 'e.g. Student Council Presidential Election 2026',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white/90 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-all shadow-sm',
                'rows': 4,
                'placeholder': 'Describe election objectives, rules, and eligibility criteria...',
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("Election title is required.")
        if len(title) < 3:
            raise forms.ValidationError("Election title must be at least 3 characters long.")
        return title

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if end_time <= start_time:
                self.add_error('end_time', "End time must be after start time.")
        return cleaned_data


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white/90 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-all shadow-sm',
                'placeholder': 'Candidate Full Name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white/90 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition-all shadow-sm',
                'rows': 3,
                'placeholder': 'Candidate manifesto or biographical background...',
            }),
        }

    def __init__(self, *args, election=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.election = election or (self.instance.election if getattr(self, 'instance', None) and self.instance.pk else None)

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Candidate name is required.")

        # Enforce unique candidate name per election
        if self.election:
            query = Candidate.objects.filter(election=self.election, name__iexact=name)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError(f"A candidate named '{name}' already exists in this election.")
        return name
