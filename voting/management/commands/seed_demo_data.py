import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from voting.models import Election, Candidate

class Command(BaseCommand):
    help = 'Create a demo active election and candidates'

    def handle(self, *args, **options):
        # 1. Create a new election
        start_time = timezone.now()
        end_time = start_time + datetime.timedelta(days=7)
        
        election = Election.objects.create(
            title="Lok Sabha General Election 2029 (Demo)",
            description="Demo election created for testing the online voting system.",
            start_time=start_time,
            end_time=end_time
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created election: {election.title} (ID: {election.id})'))

        # 2. Create candidates
        candidates_data = [
            ("Narendra Modi", "Bharatiya Janata Party (BJP) - Prime Minister Candidate"),
            ("Rahul Gandhi", "Indian National Congress (INC) - Prime Minister Candidate"),
            ("Arvind Kejriwal", "Aam Aadmi Party (AAP) - Prime Minister Candidate"),
        ]
        
        for name, desc in candidates_data:
            candidate = Candidate.objects.create(
                election=election,
                name=name,
                description=desc
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created candidate: {candidate.name} (ID: {candidate.id})'))
