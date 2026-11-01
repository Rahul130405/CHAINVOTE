from django.db import migrations
from django.core.management import call_command


def create_cache_table(apps, schema_editor):
    try:
        call_command('createcachetable', database=schema_editor.connection.alias)
    except Exception:
        pass


def remove_cache_table(apps, schema_editor):
    table_name = 'chainvote_cache_table'
    try:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0006_candidate_idx_candidate_election_name_and_more'),
    ]

    operations = [
        migrations.RunPython(create_cache_table, reverse_code=remove_cache_table),
    ]
