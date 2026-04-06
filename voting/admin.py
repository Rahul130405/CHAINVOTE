from django.contrib import admin
from .models import Election, Candidate, Vote
from .utils.encryption import decrypt_vote  # Assuming you have this function


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


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'election', 'vote_count']
    list_filter = ['election']
    search_fields = ['name', 'election__title']

    def vote_count(self, obj):
        # Count votes for this candidate by decrypting each vote
        count = 0
        for v in obj.election.votes.all():
            try:
                if decrypt_vote(v.encrypted_vote) == str(obj.id) or decrypt_vote(v.encrypted_vote) == obj.id:
                    count += 1
            except Exception:
                pass
        return count
    vote_count.short_description = "Votes"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    # Updated to show the blockchain hash in the list view
    list_display = ['election', 'short_hash', 'voter_ip', 'voted_at']
    list_filter = ['election', 'voted_at']
    search_fields = ['voter_hash', 'block_hash']
    
    # Expose the new blockchain fields to the admin, but make EVERYTHING read-only
    readonly_fields = [
        'election', 
        'encrypted_vote', 
        'voter_hash', 
        'voter_ip', 
        'voted_at', 
        'previous_hash', 
        'block_hash'
    ]

    # 🔒 STRICT BLOCKCHAIN SECURITY: No tampering allowed via Admin panel
    def has_add_permission(self, request):
        """Prevent manually adding fake votes."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent altering existing votes (which would break the hash)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting votes (which would break the chain for subsequent votes)."""
        return False