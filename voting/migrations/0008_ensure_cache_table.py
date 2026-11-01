"""
Forward Migration 0008: Idempotent and Fail-Fast Cache Table Integrity.

Ensures 'chainvote_cache_table' exists without swallowing exceptions.
Safe across all database backends (PostgreSQL, SQLite).
Non-destructive rollback: reverse_code does not drop the table.
"""

from django.db import migrations
from django.core.management import call_command


def ensure_cache_table(apps, schema_editor):
    """
    Idempotently verifies and creates 'chainvote_cache_table'.
    If the table already exists, exits cleanly.
    If missing, invokes createcachetable and asserts table creation.
    Does NOT suppress exceptions.
    """
    table_name = 'chainvote_cache_table'
    connection = schema_editor.connection

    # 1. Idempotency Check: Introspect existing database tables
    existing_tables = connection.introspection.table_names()
    if table_name in existing_tables:
        return

    # 2. Fail-Fast Execution: Invoke Django's core createcachetable
    # Exceptions are allowed to bubble up naturally without blind suppression
    call_command('createcachetable', database=connection.alias)

    # 3. Post-Creation Hard Assertion: Verify the table physically exists
    post_tables = connection.introspection.table_names()
    if table_name not in post_tables:
        raise RuntimeError(
            f"CRITICAL: 'createcachetable' executed for database '{connection.alias}', "
            f"but table '{table_name}' was not detected in introspection."
        )


def reverse_noop(apps, schema_editor):
    """
    Non-destructive reverse operation.
    Does NOT drop 'chainvote_cache_table' because the table may have existed
    prior to migration 0008 being applied.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0007_create_cache_table'),
    ]

    operations = [
        migrations.RunPython(
            ensure_cache_table,
            reverse_code=reverse_noop,
        ),
    ]
