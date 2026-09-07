from django.core.management.base import BaseCommand
from voting.utils.candidate_automation import execute_candidate_automation


class Command(BaseCommand):
    help = 'Executes the 6-day automated candidate generation for active elections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Bypass the 6-day (144 hours) cooldown check and force candidate generation',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write("Checking candidate automation...")

        result = execute_candidate_automation(force=force)
        status = result.get('status')

        if status == 'success':
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] {result.get('message')}"))
            c = result.get('candidate', {})
            self.stdout.write(f"   Candidate: {c.get('name')} ({c.get('party')}) [ID: {c.get('id')}]")
            self.stdout.write(f"   Election: {result.get('election')}")
            self.stdout.write(f"   Total Candidates: {result.get('total_candidates')}")
            self.stdout.write(f"   Next eligible addition: {result.get('next_eligible_at')}")
        elif status == 'skipped':
            self.stdout.write(self.style.WARNING(f"[SKIPPED] {result.get('message')}"))
            self.stdout.write(f"   Last generated: {result.get('last_generated_at')}")
            self.stdout.write(f"   Next eligible addition: {result.get('next_eligible_at')}")
            self.stdout.write(f"   Current candidates: {result.get('current_candidate_count')}")
        else:
            self.stdout.write(self.style.ERROR(f"[FAILED] {result.get('message')}"))
