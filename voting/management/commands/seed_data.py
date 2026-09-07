"""
Usage: python manage.py seed_data

Creates sample elections, candidates, and a test user so you can
explore ChainVote immediately after setup.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from voting.models import Election, Candidate


class Command(BaseCommand):
    help = 'Seeds the database with sample elections and candidates'

    def handle(self, *args, **options):
        now = timezone.now()

        # Create superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@chainvote.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('✅ Superuser created: admin / admin123'))

        # Create test voter
        if not User.objects.filter(username='voter1').exists():
            User.objects.create_user('voter1', password='voter123')
            self.stdout.write(self.style.SUCCESS('✅ Test user created: voter1 / voter123'))

        # ── Active Election: 2026 National Election ───────────────────
        e0, _ = Election.objects.get_or_create(
            title='2026 National Election',
            defaults={
                'description': 'National Digital Democracy Election powered by cryptographic ledgers.',
                'start_time': now - timedelta(days=1),
                'end_time': now + timedelta(days=60),
            }
        )
        for name, desc in [
            ('Aarav Sharma', 'Digital India Party'),
            ('Priya Verma', 'National Reform Alliance'),
            ('Rohan Mehta', "People's Development Front"),
        ]:
            Candidate.objects.get_or_create(election=e0, name=name, defaults={'description': desc})

        # ── Active Election ──────────────────────────
        e1, _ = Election.objects.get_or_create(
            title='Best Programming Language 2025',
            defaults={
                'description': 'Vote for your favorite programming language of the year.',
                'start_time': now - timedelta(hours=1),
                'end_time': now + timedelta(days=2),
            }
        )
        for name, desc in [
            ('Python', 'Simple, readable, powerful.'),
            ('JavaScript', 'The language of the web.'),
            ('Rust', 'Fast, safe, and low-level.'),
            ('Go', 'Simple concurrency built-in.'),
        ]:
            Candidate.objects.get_or_create(election=e1, name=name, defaults={'description': desc})

        # ── Upcoming Election ────────────────────────
        e2, _ = Election.objects.get_or_create(
            title='Best Frontend Framework 2025',
            defaults={
                'description': 'Which frontend framework reigns supreme?',
                'start_time': now + timedelta(days=1),
                'end_time': now + timedelta(days=5),
            }
        )
        for name, desc in [
            ('React', 'Component-based UI library by Meta.'),
            ('Vue.js', 'Progressive JavaScript framework.'),
            ('Angular', 'Full-featured framework by Google.'),
            ('Svelte', 'Compiles away at build time.'),
        ]:
            Candidate.objects.get_or_create(election=e2, name=name, defaults={'description': desc})

        # ── Ended Election ───────────────────────────
        e3, _ = Election.objects.get_or_create(
            title='Best Code Editor 2024',
            defaults={
                'description': 'The ultimate code editor showdown.',
                'start_time': now - timedelta(days=10),
                'end_time': now - timedelta(days=1),
            }
        )
        for name, desc in [
            ('VS Code', 'Microsoft\'s popular open-source editor.'),
            ('Neovim', 'Modal editing powerhouse.'),
            ('JetBrains IDEs', 'Smart IDE suite.'),
        ]:
            Candidate.objects.get_or_create(election=e3, name=name, defaults={'description': desc})

        self.stdout.write(self.style.SUCCESS('✅ Sample data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('  🌐 App:        http://127.0.0.1:8000/')
        self.stdout.write('  🔧 Admin:      http://127.0.0.1:8000/admin/')
        self.stdout.write('  👤 Admin login: admin / admin123')
        self.stdout.write('  👤 Test voter:  voter1 / voter123')
