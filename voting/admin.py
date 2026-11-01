import logging
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.db import transaction, DatabaseError
from django.db.models import ProtectedError

from .models import Election, Candidate, Vote, SecurityLog, ScheduledDataPush, CandidateAutomationState
from .utils.encryption import decrypt_vote
from .forms import get_election_deletion_blocking_reason, election_has_recorded_votes_or_ledger, candidate_has_recorded_votes
from .decorators import is_authorized_admin

logger = logging.getLogger('chainvote.admin')


class CandidateInline(admin.TabularInline):
    """Show candidates directly inside the Election admin page."""
    model = Candidate
    extra = 2
    fields = ['name', 'description']


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'start_time', 'end_time', 'total_votes', 'created_at']
    list_filter = ['start_time', 'end_time']
    search_fields = ['title', 'description']
    inlines = [CandidateInline]
    readonly_fields = ['created_at']

    def status(self, obj):
        return obj.status
    status.short_description = 'Status'

    def total_votes(self, obj):
        return obj.total_votes
    total_votes.short_description = "Total Votes"

    def has_module_permission(self, request):
        user = getattr(request, 'user', None)
        if user and (is_authorized_admin(user) or user.is_superuser):
            return True
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        user = getattr(request, 'user', None)
        if user and (is_authorized_admin(user) or user.is_superuser):
            return True
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        user = getattr(request, 'user', None)
        if user and (is_authorized_admin(user) or user.is_superuser):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Prevents deletion in Django Admin if:
        - Recorded votes exist on the cryptographic ledger.
        - Election is currently active.
        - System protocol ledger election.
        """
        if obj is not None:
            if election_has_recorded_votes_or_ledger(obj):
                return False
            if obj.status == Election.STATUS_ACTIVE:
                return False
            if getattr(obj, 'title', '') == 'ChainVote Network Audit & Protocol Ledger':
                return False
        user = getattr(request, 'user', None)
        if user and (is_authorized_admin(user) or user.is_superuser):
            return True
        return super().has_delete_permission(request, obj)

    def delete_view(self, request, object_id, extra_context=None):
        """
        Gracefully handles Django Admin election deletion.
        Intercepts ProtectedError, DatabaseError, and unexpected exceptions
        to prevent raw HTTP 500 errors. Re-raises PermissionDenied for 403 enforcement.
        """
        try:
            return super().delete_view(request, object_id, extra_context=extra_context)
        except PermissionDenied:
            raise
        except ProtectedError as pe:
            logger.warning("Admin delete_view: ProtectedError for election ID %s: %s", object_id, pe)
            messages.error(
                request,
                "Cannot delete this election: It is referenced by protected dependent records (e.g. recorded cryptographic votes)."
            )
            return HttpResponseRedirect(reverse('admin:voting_election_changelist'))
        except DatabaseError as de:
            cause = getattr(de, '__cause__', None)
            pgcode = getattr(cause, 'pgcode', None) or getattr(de, 'pgcode', None)
            logger.error(
                "Admin delete_view: DatabaseError (%s, pgcode=%s) for election ID %s: %s",
                de.__class__.__name__, pgcode, object_id, de
            )
            code_str = f", SQLSTATE {pgcode}" if pgcode else ""
            messages.error(
                request,
                f"Database error ({de.__class__.__name__}{code_str}) "
                f"encountered while accessing election deletion for ID {object_id}. Deletion was aborted."
            )
            return HttpResponseRedirect(reverse('admin:voting_election_changelist'))
        except Exception as exc:
            logger.exception("Admin delete_view: Unexpected error for election ID %s: %s", object_id, exc)
            messages.error(request, "An unexpected error occurred while preparing election deletion.")
            return HttpResponseRedirect(reverse('admin:voting_election_changelist'))

    def delete_model(self, request, obj):
        """Defense-in-depth single model deletion."""
        reason = get_election_deletion_blocking_reason(obj)
        if reason:
            messages.error(request, f"Security Alert: Cannot delete election '{obj.title}'. {reason}")
            raise PermissionDenied(reason)
        with transaction.atomic():
            super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Admin bulk delete action: safely skips protected elections."""
        blocked = []
        deleted_count = 0
        for election in queryset:
            reason = get_election_deletion_blocking_reason(election)
            if reason:
                blocked.append((election.title, reason))
                continue
            try:
                with transaction.atomic():
                    election.delete()
                    deleted_count += 1
            except ProtectedError as pe:
                blocked.append((election.title, "Referenced by protected dependent records."))
            except DatabaseError as de:
                blocked.append((election.title, f"Database error ({de.__class__.__name__})."))

        if blocked:
            for title, reason in blocked:
                messages.error(request, f"Cannot delete election '{title}': {reason}")
        if deleted_count > 0:
            messages.success(request, f"Successfully deleted {deleted_count} eligible election(s).")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'election', 'vote_count']
    list_filter = ['election']
    search_fields = ['name', 'election__title']
    list_select_related = ['election']

    def vote_count(self, obj):
        count = 0
        for v in obj.election.votes.all():
            try:
                if decrypt_vote(v.encrypted_vote) == str(obj.id) or decrypt_vote(v.encrypted_vote) == obj.id:
                    count += 1
            except Exception:
                pass
        return count
    vote_count.short_description = "Votes"

    def has_module_permission(self, request):
        user = getattr(request, 'user', None)
        if user and (is_authorized_admin(user) or user.is_superuser):
            return True
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        user = getattr(request, 'user', None)
        if user and (is_authorized_admin(user) or user.is_superuser):
            return True
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        user = getattr(request, 'user', None)
        if user and (is_authorized_admin(user) or user.is_superuser):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Prevents deletion in Django Admin if:
        - Election is not strictly 'upcoming' (candidates cannot be deleted once active or ended).
        - Candidate has recorded votes on the blockchain ledger.
        """
        if obj is not None:
            if obj.election.status != 'upcoming':
                return False
            if candidate_has_recorded_votes(obj):
                return False
        user = getattr(request, 'user', None)
        if user and (is_authorized_admin(user) or user.is_superuser):
            return True
        return super().has_delete_permission(request, obj)

    def delete_view(self, request, object_id, extra_context=None):
        """
        Gracefully handles Django Admin candidate deletion.
        Intercepts ProtectedError, DatabaseError, and unexpected exceptions
        to prevent raw HTTP 500 errors. Re-raises PermissionDenied for 403 enforcement.
        """
        try:
            return super().delete_view(request, object_id, extra_context=extra_context)
        except PermissionDenied:
            raise
        except ProtectedError as pe:
            logger.warning("Admin delete_view: ProtectedError for candidate ID %s: %s", object_id, pe)
            messages.error(
                request,
                "Cannot delete this candidate: Referenced by protected dependent records."
            )
            return HttpResponseRedirect(reverse('admin:voting_candidate_changelist'))
        except DatabaseError as de:
            cause = getattr(de, '__cause__', None)
            pgcode = getattr(cause, 'pgcode', None) or getattr(de, 'pgcode', None)
            logger.error(
                "Admin delete_view: DatabaseError (%s, pgcode=%s) for candidate ID %s: %s",
                de.__class__.__name__, pgcode, object_id, de
            )
            code_str = f", SQLSTATE {pgcode}" if pgcode else ""
            messages.error(
                request,
                f"Database error ({de.__class__.__name__}{code_str}) "
                f"encountered while accessing candidate deletion for ID {object_id}. Deletion was aborted."
            )
            return HttpResponseRedirect(reverse('admin:voting_candidate_changelist'))
        except Exception as exc:
            logger.exception("Admin delete_view: Unexpected error for candidate ID %s: %s", object_id, exc)
            messages.error(request, "An unexpected error occurred while preparing candidate deletion.")
            return HttpResponseRedirect(reverse('admin:voting_candidate_changelist'))

    def delete_model(self, request, obj):
        """Defense-in-depth single candidate deletion."""
        if obj.election.status != 'upcoming':
            messages.error(request, f"Security Alert: Cannot delete candidate '{obj.name}'. Election is {obj.election.status}.")
            raise PermissionDenied(f"Election is {obj.election.status}.")
        if candidate_has_recorded_votes(obj):
            messages.error(request, f"Security Alert: Cannot delete candidate '{obj.name}' because votes have already been recorded.")
            raise PermissionDenied("Candidate has recorded votes.")
        with transaction.atomic():
            super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Admin bulk delete action: safely skips protected candidates."""
        blocked = []
        deleted_count = 0
        for cand in queryset:
            if cand.election.status != 'upcoming':
                blocked.append((cand.name, f"Election is {cand.election.status}"))
                continue
            if candidate_has_recorded_votes(cand):
                blocked.append((cand.name, "Recorded votes exist on the ledger."))
                continue
            try:
                with transaction.atomic():
                    cand.delete()
                    deleted_count += 1
            except ProtectedError as pe:
                blocked.append((cand.name, "Referenced by protected dependent records."))
            except DatabaseError as de:
                blocked.append((cand.name, f"Database error ({de.__class__.__name__})."))

        if blocked:
            for name, reason in blocked:
                messages.error(request, f"Cannot delete candidate '{name}': {reason}")
        if deleted_count > 0:
            messages.success(request, f"Successfully deleted {deleted_count} eligible candidate(s).")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['election', 'short_hash', 'voter_ip', 'voted_at']
    list_filter = ['election', 'voted_at']
    search_fields = ['voter_hash', 'block_hash']
    list_select_related = ['election']

    readonly_fields = [
        'election',
        'encrypted_vote',
        'voter_hash',
        'voter_ip',
        'voted_at',
        'previous_hash',
        'block_hash'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ['level', 'action', 'ip_address', 'timestamp']
    list_filter = ['level', 'timestamp']
    search_fields = ['action', 'ip_address', 'details']
    readonly_fields = ['level', 'action', 'ip_address', 'details', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ScheduledDataPush)
class ScheduledDataPushAdmin(admin.ModelAdmin):
    list_display = [
        'push_type',
        'status',
        'executed_at',
        'last_successful_display',
        'next_eligible_display',
        'created_at'
    ]
    list_filter = ['status', 'push_type', 'executed_at']
    search_fields = ['push_type', 'details', 'error_message']
    readonly_fields = [
        'push_type',
        'status',
        'executed_at',
        'last_successful_push',
        'next_eligible_display',
        'details',
        'error_message',
        'created_at',
        'updated_at'
    ]

    def last_successful_display(self, obj):
        return obj.last_successful_push.strftime('%Y-%m-%d %H:%M:%S') if obj.last_successful_push else 'None'
    last_successful_display.short_description = "Last Successful Push"

    def next_eligible_display(self, obj):
        next_dt = obj.next_eligible_push
        return next_dt.strftime('%Y-%m-%d %H:%M:%S') if next_dt else 'N/A'
    next_eligible_display.short_description = "Next Eligible Push"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CandidateAutomationState)
class CandidateAutomationStateAdmin(admin.ModelAdmin):
    list_display = ['election', 'candidate_name', 'last_generated_at', 'next_eligible_display']
    list_filter = ['election', 'last_generated_at']
    search_fields = ['election__title', 'candidate__name', 'details']
    list_select_related = ['election', 'candidate']
    readonly_fields = ['election', 'candidate', 'last_generated_at', 'details', 'created_at']

    def candidate_name(self, obj):
        return obj.candidate.name if obj.candidate else "None"
    candidate_name.short_description = "Generated Candidate"

    def next_eligible_display(self, obj):
        return obj.next_eligible_at.strftime('%Y-%m-%d %H:%M:%S') if obj.next_eligible_at else 'N/A'
    next_eligible_display.short_description = "Next Addition Eligible"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
