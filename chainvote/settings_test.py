"""
Local Test Settings for ChainVote.
Strictly isolated from Supabase staging and production databases.
Used exclusively by pytest and test runners.
"""
import os
from .settings import *

def _get_test_db_password():
    pwd = os.environ.get('CHAINVOTE_TEST_DB_PASSWORD')
    if not pwd and os.name == 'nt':
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment')
            pwd, _ = winreg.QueryValueEx(key, 'CHAINVOTE_TEST_DB_PASSWORD')
            key.Close()
        except Exception:
            pass
    return pwd or ''

_test_pwd = _get_test_db_password()

# ── 1. ISOLATED LOCAL POSTGRESQL DATABASE CONFIGURATION ─────────────────────
# Completely override DATABASES to ensure zero inheritance from DATABASE_URL or staging.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chainvote_test',
        'USER': 'postgres',
        'PASSWORD': _test_pwd,
        'HOST': '127.0.0.1',
        'PORT': 5433,
        'TEST': {
            'NAME': 'test_chainvote_test',
        },
        'OPTIONS': {},
    }
}

# ── 2. FAIL-CLOSED SAFETY VALIDATION ─────────────────────────────────────────
# Verify configuration strictly targets the isolated local PostgreSQL instance on port 5433.
_default_db = DATABASES.get('default', {})
_engine = _default_db.get('ENGINE', '')
_host = str(_default_db.get('HOST', ''))
_port = str(_default_db.get('PORT', ''))
_name = str(_default_db.get('NAME', ''))

if _engine != 'django.db.backends.postgresql':
    raise RuntimeError(
        f"CRITICAL SAFETY VIOLATION: Database ENGINE must be 'django.db.backends.postgresql', got '{_engine}'."
    )

if _host not in ('127.0.0.1', 'localhost'):
    raise RuntimeError(
        f"CRITICAL SAFETY VIOLATION: Database HOST must be '127.0.0.1' or 'localhost', got '{_host}'."
    )

if _port != '5433':
    raise RuntimeError(
        f"CRITICAL SAFETY VIOLATION: Database PORT must be 5433, got '{_port}'."
    )

if _name != 'chainvote_test':
    raise RuntimeError(
        f"CRITICAL SAFETY VIOLATION: Database NAME must be 'chainvote_test', got '{_name}'."
    )

if not _test_pwd:
    raise RuntimeError(
        "CRITICAL SAFETY VIOLATION: Environment variable 'CHAINVOTE_TEST_DB_PASSWORD' must be set."
    )

_blocked_keywords = ['supabase', 'pooler', 'aws', 'eu-west-2', 'azure', 'render']
for _kw in _blocked_keywords:
    if _kw in _host.lower() or _kw in _name.lower():
        raise RuntimeError(
            f"CRITICAL SAFETY VIOLATION: Remote signature '{_kw}' detected in test database configuration."
        )
