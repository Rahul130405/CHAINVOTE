from django.core.management.base import BaseCommand
from voting.utils.data_push import execute_automatic_data_push


class Command(BaseCommand):
    help = 'Executes the scheduled 4-day blockchain audit and data push'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Bypass the 4-day (96 hours) cooldown check and force execution',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write("Triggering automatic backend data push...")
        
        result = execute_automatic_data_push(force=force)
        status = result.get('status')

        if status == 'success':
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] {result.get('message')}"))
            if 'details' in result:
                self.stdout.write(f"   Checkpoint Block Hash: {result['details'].get('checkpoint_block_hash')}")
                self.stdout.write(f"   Elections Scanned: {result['details'].get('elections_scanned')}")
                self.stdout.write(f"   Total Blocks Audited: {result['details'].get('total_blocks_audited')}")
            self.stdout.write(f"   Next eligible push: {result.get('next_eligible_push')}")
        elif status == 'skipped':
            self.stdout.write(self.style.WARNING(f"[SKIPPED] {result.get('message')}"))
            self.stdout.write(f"   Last successful push: {result.get('last_successful_push')}")
            self.stdout.write(f"   Next eligible push: {result.get('next_eligible_push')}")
        else:
            self.stdout.write(self.style.ERROR(f"[FAILED] {result.get('message')}"))
