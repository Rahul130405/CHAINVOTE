# ⛓️ ChainVote

### **Transparent. Tamper-Evident. Auditable.**
*The next generation of digital democracy, powered by cryptographic ledgers.*

---

[![Security: SHA-256](https://img.shields.io/badge/Security-SHA--256-blue.svg)](https://en.wikipedia.org/wiki/SHA-2)
[![Encryption: Fernet](https://img.shields.io/badge/Encryption-Fernet_AES--128--CBC-emerald.svg)](https://cryptography.io/)
[![Framework: Django](https://img.shields.io/badge/Framework-Django_4.2-092e20.svg)](https://www.djangoproject.com/)
[![Styling: Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38bdf8.svg)](https://tailwindcss.com/)
[![Testing: Pytest](https://img.shields.io/badge/Testing-Pytest_9.1-green.svg)](https://docs.pytest.org/)

## 📌 Overview

**ChainVote** is a tamper-evident digital voting protocol designed to provide electoral auditability through cryptographic controls. By combining hash-linked ledger records with authenticated ballot encryption—without the gas fees or operational overhead of a public cryptocurrency network—ChainVote implements mechanisms where votes are **cryptographically linked**, **encrypted at rest**, and **stored separately from raw voter identifiers**.

ChainVote replaces unverified trust models with **cryptographic verification**, backed by an administrative management suite, staff-accessible security logging, and automated chain integrity checking.

---

## 🌟 Key Features

### 🛡️ Security & Integrity
*   **SHA-256 Blockchain Chaining:** Every vote (block) records the hash of the preceding vote. Any attempt to alter historical votes breaks subsequent block hashes and is detected during chain verification.
*   **Fernet Authenticated Ballot Encryption:** Ballots are encrypted using symmetric Fernet encryption (128-bit AES in CBC mode with HMAC-SHA256 authentication via Python's `cryptography` library) before being written to the database.
*   **Tamper-Evident Ledger Auditing:** Automated chain traversal (`verify_election_blockchain`) validates every block and link before tallying results. If any block is corrupted or out of sequence, tallying is immediately blocked.
*   **Concurrency Controls:** Critical operations (vote casting and candidate deletion) are implemented with atomic transactions (`transaction.atomic`) and row-level locks (`select_for_update`). Note that true row-lock contention behavior requires PostgreSQL and remains unverified locally because the concurrency test skips under SQLite.

### 👤 Privacy & Voter Validation
*   **Strict Voter ID Validation:** Enforces a standardized 10-character alphanumeric ID (`^[A-Za-z0-9]{10}$`) across client-side input forms and server-side request handlers.
*   **One-Way Identity Hashing:** Voter IDs are transformed into SHA-256 hashes upon submission. The system checks voter eligibility and enforces single-vote limits without storing raw identification in the voting records.
*   **Decoupled Ballot Storage:** The voter's identity hash is recorded to prevent duplicate submissions, while the encrypted ballot payload is stored without direct linkage to plain voter credentials, and voters receive an individual block hash receipt.

### ⚙️ Administrative Management Portal (`/manage/`)
*   **Election Lifecycle Control:** Staff and superusers can create new elections, configure start and end timestamps, and edit metadata.
*   **Candidate Management:** Add and update candidate information per election.
*   **Fail-Closed Safe Candidate Deletion:** Candidates can only be deleted while the election is in `upcoming` status and has zero recorded votes. If any ballot fails decryption during auditing, the system fails closed to protect the ledger and forbids deletion.

### 📊 Transparency & Monitoring
*   **Live Blockchain Explorer:** Public audit interface (`/election/<id>/blockchain/`) displaying block hashes, previous hashes, and timestamps.
*   **Cryptographically Locked Results:** Election results remain locked until the designated `end_time` has elapsed and the blockchain passes integrity verification.
*   **Security Event Dashboard:** Restricted interface (`/security/threat-dashboard/`) for staff/admin users to review recorded `SecurityLog` events (such as blocked duplicate voting attempts and associated client IP addresses).

### 🎨 Modern Interface & Accessibility
*   **Apple-Inspired Glassmorphism:** Clean, responsive light interface built with Tailwind CSS, optimized for mobile, tablet, and desktop viewports.
*   **Bilingual Localization:** Dynamic client-side language toggle supporting English and Hindi (हिन्दी) across voter-facing interfaces (home landing, authentication, and voting booth).
*   **Unified Branding:** Custom ChainVote emblem and multi-resolution `favicon.ico` configured across Django and static routing.

---

## 🧠 How It Works

```text
  [ Voter ] ──────► 1. Authenticate (Validate 10-char ID & generate SHA-256 hash)
                           │
                           ▼
                    2. Select Candidate & Encrypt Ballot (Fernet AES-128-CBC/HMAC-SHA256)
                           │
                           ▼
                    3. Atomic Transaction (Row lock candidate, verify election active)
                           │
                           ▼
                    4. Mine Block (Fetch previous block hash, calculate SHA-256)
                           │
                           ▼
  [ Receipt ] ◄──── 5. Issue Proof (Block hash receipt for Blockchain Explorer)
```

1.  **Authenticate:** The voter enters a 10-character alphanumeric ID. The system validates format constraints and generates a one-way SHA-256 hash.
2.  **Encrypt:** The voter selects a candidate. The choice is sealed inside an authenticated Fernet encrypted payload.
3.  **Mine & Link:** Inside an atomic database transaction with row-level locking, the system retrieves the previous block's hash, computes the current block hash, and commits the vote to the ledger.
4.  **Verify:** The voter receives a digital receipt containing the block hash, enabling independent verification via the public Blockchain Explorer.

---

## 🏗️ Project Structure

```text
CHAINVOTE/
├── chainvote/              # Core Django project configuration
│   ├── settings.py         # App configuration, WhiteNoise, DB & cache setup
│   ├── urls.py             # Global route definitions & root favicon redirect
│   └── wsgi.py             # WSGI application entry point for Vercel / Gunicorn
├── voting/                 # Core voting application
│   ├── management/         # Management commands (data seeding, audits)
│   ├── migrations/         # Database migrations
│   ├── static/             # Static assets (images, logos, multi-layer favicon)
│   ├── templates/          # Glassmorphic templates (light mode, bilingual)
│   │   └── voting/
│   │       ├── manage/     # Admin portal templates (elections, candidates)
│   │       └── ...         # Public views (booth, results, explorer, SOC)
│   ├── utils/              # Core cryptographic and ledger logic
│   │   ├── blockchain.py   # Blockchain verification & block traversal
│   │   ├── candidate_automation.py # Periodic candidate automation & initial data seeding
│   │   └── encryption.py   # Fernet encryption & decryption helpers
│   ├── decorators.py       # Staff & superuser access control (@admin_required)
│   ├── forms.py            # Election/Candidate forms & fail-closed vote checking
│   ├── models.py           # Election, Candidate, Vote, SecurityLog models
│   ├── serializers.py      # Django REST Framework serializers
│   ├── urls.py             # Application URLs (booth, manage, SOC, REST API)
│   └── views.py            # Voting booth, results, admin & API endpoints
├── tests/                  # Pytest test suite (68 collected tests)
│   ├── pages/              # Page Object Models for browser interaction
│   ├── conftest.py         # Pytest fixtures and test database setup
│   ├── test_admin.py       # Admin portal, authorization & concurrency tests
│   ├── test_auth.py        # Authentication & registration flow tests
│   ├── test_dark_mode_removal.py # Interface styling & theme regression tests
│   ├── test_phase2_functional.py # End-to-end integration and smoke tests
│   ├── test_security.py    # SOC dashboard & duplicate vote defense tests
│   ├── test_voter_id_validation.py # 10-character ID validation test coverage
│   └── test_voting.py      # Digital voting booth and mining workflow tests
├── staticfiles/            # Collected static files for production deployment
├── db.sqlite3              # Local development database
├── manage.py               # Django management CLI script
├── pytest.ini              # Pytest configuration settings
├── requirements.txt        # Python package dependencies
└── vercel.json             # Vercel deployment routes, headers & cron config
```

---

## ⚙️ Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Backend Framework** | Django 4.2.30 & DRF 3.17.1 | Application server, ORM, and REST endpoints |
| **Frontend & UI** | Tailwind CSS (CDN) | Apple-inspired light glassmorphism & responsive layout |
| **Localization** | JavaScript (Client-side) | English / Hindi bilingual dynamic translation toggle on voter-facing views |
| **Cryptography** | `cryptography` 49.0 (Fernet) & `hashlib` | Authenticated ballot encryption (AES-128-CBC + HMAC-SHA256) & SHA-256 block hashing |
| **Database** | SQLite (Dev) / PostgreSQL (Production) | Relational ledger and relational integrity storage |
| **Static Assets** | WhiteNoise 6.9.0 | Efficient static file compression and caching |
| **Testing** | Pytest 9.1.1 & Selenium WebDriver | Automated unit, security, admin, and browser test suite |
| **Deployment Config** | Vercel (`@vercel/python`) | Configuration files for serverless WSGI hosting, static routing & cron |

---

## ⚡ Setup & Development (Windows)

### 1. Clone & Navigate
```powershell
git clone https://github.com/your-username/ChainVote.git
cd ChainVote/CHAINVOTE
```

### 2. Environment Setup
```powershell
python -m venv env
.\env\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Initialize Database
```powershell
python manage.py migrate
python manage.py seed_data  # Optional: Seed sample elections and candidates
```

### 5. Run the Test Suite
```powershell
pytest -v
```

### 6. Launch Development Server
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000` to access the voting platform.

---

## 🧪 Testing & Verification

ChainVote includes an automated test suite comprising **68 collected tests** (**67 passed, 1 skipped** on SQLite) across backend logic, administrative permissions, voter validation, security controls, and browser flows:

*   **Admin Management (`test_admin.py`):** `@admin_required` decorators, election/candidate CRUD validation, fail-closed vote checking, and deletion constraints.
*   **Voter ID Validation (`test_voter_id_validation.py`):** 10-character alphanumeric constraints, regex enforcement across web views, REST APIs, and client-side forms.
*   **Authentication & Session (`test_auth.py`):** Registration, password mismatch validation, duplicate usernames, session login, and deep-link redirects.
*   **Security & Auditing (`test_security.py`):** Duplicate vote prevention, `SecurityLog` event creation, and access restriction for non-staff voters.
*   **Voting Workflows (`test_voting.py`, `test_phase2_functional.py`):** Ballot selection, review modal confirmation, submission flow, and receipt modal rendering.
*   **Theme & UI Integrity (`test_dark_mode_removal.py`):** Verification of light glassmorphic templates and bilingual toggle state persistence.

### Local Test Execution Summary
*   **67 Passed** in the local test suite execution.
*   **1 Skipped (`test_postgres_concurrency_vote_blocks_deletion`):** This specific test inspects row-lock contention (`SELECT ... FOR UPDATE` verified via `pg_locks`) and is skipped when running against SQLite. Consequently, PostgreSQL concurrency behavior under high contention remains unverified locally until executed against a live PostgreSQL database.

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/elections/` | List all upcoming, active, and ended elections | Public |
| `GET` | `/api/elections/<id>/` | Fetch details and candidate roster for an election | Public |
| `POST` | `/api/elections/<id>/vote/` | Cast an encrypted ballot (requires 10-char Voter ID) | Public / Voter |
| `GET` | `/api/elections/<id>/results/` | Fetch tallied election results (unlocked only after end) | Public |
| `GET`/`POST` | `/api/cron/add-candidate/` | Scheduled task endpoint triggered via Vercel Cron | Internal / Cron |

---

## 🌐 Deployment Configuration

The repository includes configuration files intended for serverless deployment on **Vercel** with a remote **PostgreSQL / Supabase** database. (Note: These files define the intended deployment structure; a live production deployment has not been formally verified or hosted.)

*   **WSGI Entry Point:** `vercel.json` specifies `@vercel/python` targeting `chainvote/wsgi.py`.
*   **Static Asset Routing:** `vercel.json` maps `/static/` and `/favicon.ico` to the `staticfiles/` directory with browser caching headers (`max-age=31536000`).
*   **Scheduled Tasks:** `vercel.json` defines a daily cron entry scheduled for `0 0 * * *` targeting `/api/cron/add-candidate/` (endpoint checks `CRON_SECRET` and enforces a 6-day automation interval).
*   **Supabase / PgBouncer Pooler Settings:** In `chainvote/settings.py`, database connections set `conn_max_age=0` and disable server-side cursors (`DISABLE_SERVER_SIDE_CURSORS = True`) when PostgreSQL is active, matching transaction-pooling (PgBouncer) requirements in serverless environments.

---

## 🔐 Security Highlights

> **"Mathematical Integrity over Human Promise."**

*   **Tamper-Evident Hash Chaining:** Blocks are cryptographically chained using SHA-256 hashes that incorporate the previous block hash and encrypted vote payload. Altering any recorded block invalidates subsequent hashes in the chain.
*   **Fail-Closed Safeguards:** The blockchain verification algorithm and candidate deletion safeguards fail closed: if data corruption, key mismatch, or decryption issues occur, access to results or candidate deletion is denied.
*   **Security Event Logging:** Blocked duplicate voting attempts trigger `CRITICAL` entries recorded in the `SecurityLog` table, which staff users can inspect through the security dashboard.
*   **CSRF & SQL Injection Protection:** Built upon Django's standard middleware, parameterized queries, and CSRF token verification.

---

## 🚀 Future Roadmap

*   [ ] **Decentralized Multi-Node Consensus:** Transitioning from a single ledger model to distributed validator nodes.
*   [ ] **Biometric Verification Integration:** Optional biometric or hardware token support for elevated voter authentication.
*   [ ] **Blind Signatures:** Exploring blind signature schemes for voter privacy.

---

## ⚠️ Disclaimer

ChainVote is an educational and hackathon project demonstrating cryptographic principles applied to electoral integrity. While it employs standard cryptographic libraries and security best practices, formal independent security audits and penetration testing are recommended before considering any production deployment in official public elections.

---

## 👨‍💻 Author  

**Rahul Raj Jaiswal**  
*Cybersecurity & Blockchain Enthusiast | Full-Stack Developer*  

🔗 [LinkedIn](https://www.linkedin.com/in/rahulrajjaiswal/)  

---

### **🏆 One Vote. One Chain. Auditable Verification.**
