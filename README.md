<div align="center">

  <img src="voting/static/voting/images/logo.webp" alt="ChainVote Logo" width="100" height="100" />

  # ChainVote

  ### **Decentralized, Tamper-Evident Digital Voting Architecture Powered by Cryptographic Ledgers**

  An enterprise-grade, auditable electronic voting platform combining authenticated ballot encryption, hash-linked blockchain chaining, and real-time security monitoring—without public cryptocurrency gas fees or wallet friction.

  <p align="center">
    <a href="https://chainvote-rrj.vercel.app/"><img src="https://img.shields.io/badge/Live_Demo-Active_Deployment-10b981?style=for-the-badge&logo=vercel&logoColor=white" alt="Live Demo" /></a>
    <a href="https://github.com/Rahul130405/CHAINVOTE"><img src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Repo" /></a>
    <a href="https://www.djangoproject.com/"><img src="https://img.shields.io/badge/Django-4.2_LTS-092e20?style=for-the-badge&logo=django&logoColor=white" alt="Django 4.2" /></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" /></a>
    <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-Supabase-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" /></a>
  </p>

  <p align="center">
    <a href="#project-overview">Overview</a> •
    <a href="#key-features">Key Features</a> •
    <a href="#system-architecture">Architecture</a> •
    <a href="#technology-stack">Tech Stack</a> •
    <a href="#voting-workflow">Voting Workflow</a> •
    <a href="#security-and-integrity-approach">Security</a> •
    <a href="#installation-and-local-setup">Setup</a> •
    <a href="#testing-and-quality-assurance">Testing</a> •
    <a href="#author">Author</a>
  </p>

</div>

---

<h2 id="project-overview">📌 Project Overview</h2>

**ChainVote** is a web-based electronic voting application engineered to solve the transparency, integrity, and auditability challenges inherent in traditional digital voting systems.

### The Problem
Traditional electronic voting systems typically rely on centralized, relational databases where votes are stored in mutable tables. In this model, an adversary, malicious insider, or compromised database administrator can alter or delete ballots silently without leaving an indelible audit trail. Conversely, deploying elections on public cryptocurrency networks (such as Ethereum or Solana) introduces prohibitive transaction ("gas") fees, volatile costs, slow transaction finality, and complex wallet onboarding that excludes ordinary voters.

### The ChainVote Solution
ChainVote bridges this gap by delivering **cryptographic proof of electoral integrity** within a performant, zero-cost web application:
- **Tamper-Evident Chaining:** Votes are structured as an append-only, cryptographic blockchain ledger using SHA-256 block hashing where each vote links immutably to the preceding record.
- **Authenticated Ballot Encryption:** Individual ballot choices are sealed using Fernet symmetric encryption (128-bit AES in CBC mode with HMAC-SHA256 authentication).
- **Decoupled Identity Protection:** Raw voter credentials are never stored. Voter eligibility is verified using one-way SHA-256 identity hashing to strictly prevent double voting while decoupling identity from ballot contents.
- **Account-Free Voter Usability:** Voters participate directly using validated identification without creating accounts or managing cryptocurrency wallets.
- **Dual Audience Architecture:**
  - **Voters:** Experience a clean, bilingual interface (English and Hindi) with instant digital receipt generation for transparent self-auditing.
  - **Administrators:** Benefit from a hardened management portal (`/manage/`) with election lifecycle scheduling, fail-closed deletion protections, and a real-time SOC Threat Operations dashboard.

---

<h2 id="key-features">🌟 Key Features</h2>

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🛡️ Cryptographic Ledger & Security</h3>
      <ul>
        <li><strong>SHA-256 Hash Chaining:</strong> Each vote block contains the hash of the preceding block (genesis block: <code>0*64</code>). Altering any historical block invalidates all downstream hashes.</li>
        <li><strong>Fernet Ballot Encryption:</strong> Ballots are encrypted at rest using AES-128-CBC with HMAC-SHA256 authenticated integrity before database persistence.</li>
        <li><strong>Fail-Closed Ledger Verification:</strong> <code>verify_election_blockchain()</code> validates the entire chain prior to decrypting tallies. Any detected anomaly halts tallying immediately.</li>
        <li><strong>Concurrency & Atomicity:</strong> Employs atomic database transactions (<code>transaction.atomic()</code>) and row-level locks (<code>select_for_update()</code>) during ballot mining.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>👤 Voter Validation & Privacy</h3>
      <ul>
        <li><strong>Strict 10-Character Voter ID:</strong> Regex-enforced pattern <code>^(?=.*[A-Za-z])(?=.*[0-9])[A-Za-z0-9]{10}$</code> requiring at least one letter and one number on client and server.</li>
        <li><strong>One-Way Identity Hashing:</strong> Voter IDs are transformed into SHA-256 hashes upon submission; raw credentials are never persisted.</li>
        <li><strong>Duplicate-Vote Prevention:</strong> Database-level unique constraint on <code>(election, voter_hash)</code> rejects duplicate voting attempts.</li>
        <li><strong>Cryptographic Receipt Modal:</strong> Successful voters receive a 64-character SHA-256 transaction hash for public verification.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>⚙️ Administrative Governance (<code>/manage/</code>)</h3>
      <ul>
        <li><strong>Single-Admin Access Control:</strong> Guarded by <code>@admin_required</code>, restricted strictly to the predefined administrative username (<code>AUTHORIZED_ADMIN_USERNAME='yash'</code>).</li>
        <li><strong>Election Lifecycle Management:</strong> Schedule upcoming elections, monitor active polls, and conclude elections with ISO datetime precision.</li>
        <li><strong>Fail-Closed Candidate Deletion:</strong> Candidates with recorded votes cannot be deleted; attempts are rejected with security alerts.</li>
        <li><strong>SOC Threat Operations Log:</strong> Real-time monitoring of prevented duplicate vote attacks, anomalous payloads, and origin IP addresses.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>📊 Transparency & High Performance</h3>
      <ul>
        <li><strong>Public Blockchain Explorer:</strong> Inspect block index, current block hash, previous block hash, and timestamps (<code>/election/&lt;id&gt;/blockchain/</code>).</li>
        <li><strong>Sealed Election Results:</strong> Results remain cryptographically sealed until polls close and the ledger passes blockchain integrity checks.</li>
        <li><strong>Precompiled Tailwind CSS:</strong> High-performance static stylesheet pipeline eliminating runtime JIT compiler overhead.</li>
        <li><strong>Optimized Database Layer:</strong> Eliminates N+1 queries using Django ORM <code>select_related()</code>, <code>prefetch_related()</code>, and <code>Count()</code> annotations.</li>
      </ul>
    </td>
  </tr>
</table>

---

<h2 id="system-architecture">🏗️ System Architecture</h2>

ChainVote is structured into five distinct operational layers, ensuring clean separation of concerns, rapid response times, and defense-in-depth security:

```mermaid
flowchart TD
    subgraph Client ["1. Client & Presentation Layer"]
        UI["Bilingual Glassmorphic UI\n(English / Hindi)"]
        Forms["Client Validation\n(10-char Alphanumeric Voter ID)"]
        Modals["Review & Receipt Modals\n(Masked Voter ID & SHA-256 Receipt)"]
    end

    subgraph Edge ["2. Edge & Routing Layer"]
        Vercel["Vercel Serverless Gateway\n(bom1 Mumbai Region)"]
        WhiteNoise["WhiteNoise Static Storage\n(CompressedManifestStaticFilesStorage)"]
    end

    subgraph App ["3. Application Server Layer (Django 4.2 LTS)"]
        Auth["Admin RBAC Guard\n(@admin_required - 'yash')"]
        Views["Voting Views & REST API\n(/election/, /manage/, /api/)"]
        Cache["LocMem Cache Layer\n(Micro-Caching for High Traffic)"]
    end

    subgraph Crypto ["4. Cryptographic & Blockchain Engine"]
        Fernet["Fernet Authenticated Cipher\n(AES-128-CBC + HMAC-SHA256)"]
        Hasher["One-Way SHA-256\n(Voter ID -> voter_hash)"]
        Chain["Blockchain Mining & Validation\n(Previous Hash + Block Hash Linking)"]
    end

    subgraph Persistence ["5. Database & Audit Layer"]
        Postgres[("PostgreSQL Database\n(Supabase / Local Test)")]
        VotesTable[("votes Table\n(unique: election + voter_hash)")]
        SecLog[("security_log Table\n(SOC Threat Audit Trail)")]
    end

    UI --> Forms --> Modals
    Modals -->|HTTPS POST| Vercel
    Vercel --> WhiteNoise
    Vercel --> App
    Views --> Auth
    Views --> Cache
    Views --> Crypto
    Fernet --> VotesTable
    Hasher --> VotesTable
    Chain --> VotesTable
    Crypto --> Persistence
    Views --> SecLog
```

---

<h2 id="technology-stack">💻 Technology Stack</h2>

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | [Django](https://www.djangoproject.com/) | `4.2.30 LTS` | Core application framework, ORM, URL routing, and session management |
| **API Framework** | [Django REST Framework](https://www.django-rest-framework.org/) | `3.17.1` | Read-only JSON endpoints for external integration and explorer auditing |
| **Cryptography** | [`cryptography`](https://cryptography.io/) | `49.0.0` | Fernet authenticated symmetric encryption (AES-128-CBC + HMAC-SHA256) |
| **Hashing Engine** | Python Standard `hashlib` | Built-in | SHA-256 for voter identity anonymization and block hash chaining |
| **Frontend Styling** | [Tailwind CSS](https://tailwindcss.com/) | `^3.4.19` | Precompiled minified CSS for an Apple-inspired responsive glassmorphic UI |
| **Static Asset Engine** | [WhiteNoise](https://whitenoise.readthedocs.io/) | `6.9.0` | Compressed, content-hashed, immutable static asset delivery |
| **Database (Production)** | [PostgreSQL](https://www.postgresql.org/) / [Supabase](https://supabase.com/) | `15+` | ACID-compliant relational storage with PgBouncer connection pooling |
| **Database (Dev/Test)** | SQLite / PostgreSQL | `3.x / 15+` | Local development and isolated test execution environment |
| **Database Connector** | `psycopg2-binary` & `dj-database-url` | `2.9.10 / 2.3.0` | High-performance PostgreSQL driver and 12-factor configuration |
| **Browser Automation** | [Selenium WebDriver](https://www.selenium.dev/) | `4.x` | Headless Chrome end-to-end and regression UI test automation |
| **Testing Framework** | [pytest](https://docs.pytest.org/) & `pytest-django` | `9.1.1 / 4.14.0` | Unit, integration, security, and performance test harness |
| **Deployment Platform** | [Vercel](https://vercel.com/) | Serverless | Serverless WSGI deployment running in the Mumbai (`bom1`) compute region |

---

<h2 id="voting-workflow">🗳️ Voting Workflow</h2>

The flowchart below illustrates the exact voter journey from election discovery to cryptographic ballot confirmation:

```mermaid
flowchart TD
    Start(["Voter Discovers Active Election"]) --> Step1["Browse Candidate Profiles & Manifestos"]
    Step1 --> Step2["Input 10-Character Alphanumeric Voter ID"]
    Step2 --> Step3{"Client-Side Validation\n(Regex Pattern Check)"}

    Step3 -- "Invalid Format" --> Error1["Show Inline Validation Warning\n(Must contain letters & numbers)"]
    Error1 --> Step2

    Step3 -- "Valid ID" --> Step4["Select Candidate & Click 'Review Vote'"]
    Step4 --> Step5["Ballot Review Modal Opens\n(Displays Masked ID: •••• •••• EF09)"]

    Step5 --> Step6["Click 'Confirm & Cast Ballot'"]
    Step6 --> Step7["Server-Side Verification & Client IP Logging"]

    Step7 --> Step8["Compute One-Way SHA-256 Voter Hash\nEncrypt Ballot Choice with Fernet Cipher"]

    Step8 --> Step9{"Check Election Unique Constraint\n(election_id, voter_hash)"}

    Step9 -- "Duplicate Detected" --> SecLog["Log CRITICAL Security Threat\nDisplay Security Alert & Block Ballot"]

    Step9 -- "Eligible Ballot" --> Step10["Fetch Preceding Block Hash (select_for_update)\nCompute SHA-256 Block Hash"]

    Step10 --> Step11["Atomic Commit to PostgreSQL Ledger\n(Link previous_hash & block_hash)"]

    Step11 --> Step12["Display Cryptographic Receipt Modal\n(64-char SHA-256 Transaction Hash)"]

    Step12 --> Verify(["Optional: Verify Block on Public Blockchain Explorer\n(/election/<id>/blockchain/)"])
```

### Detailed Voter Steps
1. **Discover Election:** The voter visits the homepage command center and selects an election bearing the green `Active` badge.
2. **Review Candidates:** The voting booth presents candidate names, manifesto descriptions, and selection radios.
3. **Input Voter ID:** The voter enters their standardized 10-character alphanumeric identification (e.g., `V1ABCDEF09`).
4. **Interactive Review:** Clicking **Review Vote** triggers client-side validation and displays a modal featuring the candidate name and masked ID (`•••• •••• EF09`) for confirmation.
5. **Atomic Commit:** Clicking **Confirm & Cast Ballot** transmits the payload. The server validates the request inside `transaction.atomic()`, performs Fernet ballot encryption, retrieves the last block's hash, computes the new block hash, and inserts the record.
6. **Digital Receipt:** The voter is issued an immutable 64-character SHA-256 transaction hash.
7. **Independent Verification:** The voter can cross-reference their transaction hash on the live Blockchain Explorer (`/election/<id>/blockchain/`).

---

<h2 id="security-and-integrity-approach">🔒 Security and Integrity Approach</h2>

ChainVote follows a defense-in-depth security model designed to provide high auditability without unsupported claims:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CHAINVOTE SECURITY MODEL                        │
├────────────────────────────┬───────────────────────────────────────────┤
│ Security Pillar            │ Implementation Detail                     │
├────────────────────────────┼───────────────────────────────────────────┤
│ Ledger Immutability        │ Tamper-Evident SHA-256 Hash Chaining      │
│ Ballot Secrecy             │ Fernet AES-128-CBC + HMAC-SHA256 Cipher   │
│ Voter Eligibility          │ One-Way SHA-256 Hashing (Raw ID Not Kept) │
│ Duplicate Prevention       │ Database-Level Unique Constraint          │
│ Administrative Access      │ Hardened Single-Admin RBAC ('yash')       │
│ Concurrency Control        │ Row-Level Database Locks (SELECT FOR UPDATE)│
│ Session Security           │ HttpOnly, Secure, SameSite Session Cookies│
│ Audit Logging              │ Automated SecurityLog Threat Operations   │
└────────────────────────────┴───────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Cryptographic Scope & Realities:**
> - **Tamper-Evident, Not Mathematically Guaranteed:** The blockchain structure is **tamper-evident**. Any alteration of past votes is immediately detectable during chain traversal, but the system relies on standard server-side relational database integrity rather than distributed decentralized consensus.
> - **Ballot Encryption:** Ballots are encrypted symmetrically using Fernet. The decryption key is held securely on the server environment. This architecture protects ballots at rest and during active voting, but does not implement asymmetric blind signatures or zero-knowledge proofs.
> - **Independent Security Audits:** While verified through extensive automated testing, ChainVote has not undergone an independent third-party cryptographic audit and should be evaluated accordingly.

---

<h2 id="application-screenshots">📸 Application Screenshots</h2>

Below is a preview of the ChainVote interface across administrative and voter-facing flows:

<table>
  <tr>
    <td width="50%" align="center">
      <strong>Voter Landing & Command Center</strong><br />
      <img src="voting/static/voting/images/logo.webp" alt="ChainVote Emblem" width="160" /><br />
      <em>Real-time metrics, active elections, and bilingual toggle</em>
      <!-- SCREENSHOT PLACEHOLDER: Voter Command Center Homepage (/) - Add screenshot here -->
    </td>
    <td width="50%" align="center">
      <strong>Administrative Management Portal</strong><br />
      <img src="voting/static/voting/images/logo.webp" alt="ChainVote Admin" width="160" /><br />
      <em>KPI cards, election rosters, and SOC Threat Operations</em>
      <!-- SCREENSHOT PLACEHOLDER: Admin Dashboard (/manage/) - Add screenshot here -->
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <strong>Voting Booth & Ballot Review Modal</strong><br />
      <img src="voting/static/voting/images/logo.webp" alt="Voting Booth" width="160" /><br />
      <em>Candidate selection, 10-char voter validation, masked review</em>
      <!-- SCREENSHOT PLACEHOLDER: Voting Booth & Modal (/election/<id>/) - Add screenshot here -->
    </td>
    <td width="50%" align="center">
      <strong>Cryptographic Vote Receipt Modal</strong><br />
      <img src="voting/static/voting/images/logo.webp" alt="Vote Receipt" width="160" /><br />
      <em>64-character SHA-256 block transaction hash</em>
      <!-- SCREENSHOT PLACEHOLDER: Vote Receipt Modal - Add screenshot here -->
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <strong>Concluded Election Results</strong><br />
      <img src="voting/static/voting/images/logo.webp" alt="Election Results" width="160" /><br />
      <em>Decrypted tallies, winner badge, and ledger status</em>
      <!-- SCREENSHOT PLACEHOLDER: Concluded Results (/election/<id>/results/) - Add screenshot here -->
    </td>
    <td width="50%" align="center">
      <strong>Public Blockchain Explorer</strong><br />
      <img src="voting/static/voting/images/logo.webp" alt="Blockchain Explorer" width="160" /><br />
      <em>Block height, previous block hashes, and timestamps</em>
      <!-- SCREENSHOT PLACEHOLDER: Blockchain Explorer (/election/<id>/blockchain/) - Add screenshot here -->
    </td>
  </tr>
</table>

---

<h2 id="installation-and-local-setup">⚡ Installation and Local Setup</h2>

Follow these steps to set up and run ChainVote locally on your development machine.

### Prerequisites
- **Python**: Version `3.10` or higher
- **Git**: Installed and configured
- **Node.js**: (Optional, only required if modifying Tailwind CSS source styles)

### 1. Clone the Repository
```bash
git clone https://github.com/Rahul130405/CHAINVOTE.git
cd CHAINVOTE
```

### 2. Configure Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv env
.\env\Scripts\activate
```
On macOS / Linux:
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root directory (`D:\CHAINVOTE\.env`) matching the application configuration:

```ini
# Core Django Security
SECRET_KEY=your-secure-development-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration (Defaults to SQLite if omitted)
# For local SQLite development:
DATABASE_URL=sqlite:///db.sqlite3

# For PostgreSQL (e.g. Supabase or Local PostgreSQL):
# DATABASE_URL=postgresql://postgres:password@localhost:5432/chainvote

# Single-Admin Security Model
AUTHORIZED_ADMIN_USERNAME=yash

# Security & Cookie Flags
SECURE_COOKIES=False
```

> [!CAUTION]
> Never commit real secrets, private keys, or database credentials to version control.

### 5. Initialize Database & Seed Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 6. Create Superuser (Administrator)
```bash
python manage.py createsuperuser --username yash
```
*(Ensure the username matches `AUTHORIZED_ADMIN_USERNAME`, which defaults to `yash`.)*

### 7. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser to interact with the platform.

---

<h2 id="testing-and-quality-assurance">🧪 Testing and Quality Assurance</h2>

ChainVote maintains a comprehensive automated testing suite verified across two distinct test layers:

### 1. Selenium End-to-End & Regression Automation
- **Coverage**: **19 / 19 Tests Passed (100%)**
  - **10 End-to-End Tests (TC-01 to TC-10):** Admin authentication, session redirection, dashboard metrics, election creation, candidate addition, ballot casting, and cryptographic receipt verification.
  - **9 Regression & Security Tests (TC-11 to TC-19):** Empty form validation, session termination, unauthenticated route guarding, safe metadata edits, fail-closed candidate deletion, strict voter ID regex validation, duplicate vote blocking, and results tally display.
- **Duration**: **118.60 seconds**
- **Test Target**: Isolated local PostgreSQL test database (`chainvote_test` on port 5433) using `chainvote.settings_test`.
- **Command to Execute**:
  ```bash
  python run_selenium_performance_suite.py
  # Or via pytest directly:
  pytest -v tests/test_performance_and_e2e.py --html=selenium_test_report.html --self-contained-html
  ```

### 2. Full Repository Unit, Security & Integration Suite
- **Coverage**: **142 / 142 Tests Passed (100%)** covering administrative authorization, session cookies, voter ID validation permutations, blockchain traversal, and theme regression.
- **Duration**: **244.57 seconds**
- **Command to Execute**:
  ```bash
  pytest -q --ignore=tests/test_performance_and_e2e.py
  ```

> [!NOTE]
> The combined reported total is **161 passing test executions** across the two separate test suites. Automated tests ran against an isolated local database and do not substitute for a formal independent security audit.

---

<h2 id="project-structure">📂 Project Structure</h2>

```text
CHAINVOTE/
├── chainvote/                        # Core Django Project Configuration
│   ├── __init__.py
│   ├── asgi.py                       # ASGI entry point
│   ├── settings.py                   # Production & base settings (WhiteNoise, Cache, Auth)
│   ├── settings_test.py              # Isolated test database settings (PostgreSQL port 5433)
│   ├── urls.py                       # Global URL configuration & favicon routing
│   └── wsgi.py                       # WSGI entry point for Vercel Serverless
├── voting/                           # Core Voting & Cryptographic Application
│   ├── management/commands/          # Management CLI commands (seed_data, add_candidate)
│   ├── migrations/                   # Database schema migrations
│   ├── static/voting/                # Static assets (images, logos, CSS, bilingual JS)
│   ├── templates/voting/             # Bilingual glassmorphic HTML templates
│   │   ├── manage/                   # Admin portal templates (dashboard, forms, rosters)
│   │   ├── base.html                 # Root layout with bilingual header and navigation
│   │   ├── booth.html                # Digital voting booth with review & receipt modals
│   │   ├── explorer.html             # Public Blockchain Explorer interface
│   │   ├── index.html                # Command center homepage
│   │   ├── login.html                # Administrator authentication interface
│   │   └── results.html              # Cryptographically sealed/unlocked results view
│   ├── utils/                        # Cryptographic & ledger utilities
│   │   ├── blockchain.py             # Blockchain verification traversal (verify_election_blockchain)
│   │   ├── candidate_automation.py   # Scheduled candidate maintenance
│   │   └── encryption.py             # Fernet symmetric encryption and decryption helpers
│   ├── decorators.py                 # Admin authorization (@admin_required, no-cache headers)
│   ├── forms.py                      # Election and candidate management forms with fail-closed checks
│   ├── models.py                     # Election, Candidate, Vote (Blockchain), SecurityLog models
│   ├── serializers.py                # Django REST Framework serializers
│   ├── urls.py                       # Application route definitions
│   └── views.py                      # Core views, voting logic, and REST API endpoints
├── tests/                            # Automated Pytest & Selenium Test Suite
│   ├── pages/                        # Page Object Models (BasePage, LoginPage, VotingBoothPage)
│   ├── screenshots/                  # Automated failure capture screenshots
│   ├── conftest.py                   # Global pytest fixtures and headless Chrome driver setup
│   ├── test_admin.py                 # Admin authorization & fail-closed deletion tests
│   ├── test_auth.py                  # Authentication and registration flow tests
│   ├── test_dark_mode_removal.py     # Theme and styling regression tests
│   ├── test_performance_and_e2e.py  # 19-Case Selenium E2E and regression test suite
│   ├── test_phase2_functional.py     # Functional integration tests
│   ├── test_security.py              # Threat operations and duplicate voting prevention tests
│   ├── test_voter_id_validation.py   # 10-character voter ID validation suite
│   └── test_voting.py                # Digital voting booth and mining workflow tests
├── staticfiles/                      # WhiteNoise fingerprinted static assets for production
├── package.json                      # Tailwind CSS build scripts and dependencies
├── pytest.ini                        # Pytest configuration settings
├── requirements.txt                  # Python application dependencies
├── run_selenium_performance_suite.py # Selenium test runner and report compiler
└── vercel.json                       # Vercel deployment configuration (bom1 region, WSGI, crons)
```

---

<h2 id="deployment-configuration">🌐 Deployment Configuration</h2>

ChainVote is engineered for seamless serverless deployment on **Vercel** coupled with a remote **PostgreSQL (Supabase)** database instance:

- **Compute Region:** Configured to run in the **Mumbai (`bom1`)** region in `vercel.json`, co-located with Supabase's `ap-south-1` region for minimal database latency.
- **Serverless WSGI Engine:** Utilizes `@vercel/python` building `chainvote/wsgi.py`.
- **Static Asset Delivery:** Leverages Django `CompressedManifestStaticFilesStorage` via WhiteNoise with public immutable 1-year cache headers (`max-age=31536000, immutable`).
- **Connection Optimization:** Configures `conn_max_age=0` and disables server-side cursors (`DISABLE_SERVER_SIDE_CURSORS = True`) to maintain high stability under PgBouncer transaction pooling.
- **Verified Production Deployment:**  
  🔗 [https://chainvote-rrj.vercel.app/](https://chainvote-rrj.vercel.app/)

---

<h2 id="future-improvements">🚀 Future Improvements</h2>

The following architectural enhancements are planned for future development:
- [ ] **Multi-Signature Administration:** Require multiple cryptographic administrator approvals before opening, concluding, or altering election metadata.
- [ ] **Asymmetric Public-Key Signatures:** Enable voter clients to sign ballots with asymmetric key pairs (e.g., Ed25519) prior to server submission.
- [ ] **Zero-Knowledge Proof (ZKP) Integration:** Research ZKP protocols to cryptographically prove voter eligibility from an anonymized voter registry without linking identifiers.
- [ ] **Decentralized Multi-Validator Consensus:** Expand beyond the single-ledger model to synchronize block validation across independent multi-party validator nodes.
- [ ] **Hardware Security Key Support:** Integrate WebAuthn / FIDO2 authentication for administrator logins.

---

<h2 id="author">👨‍💻 Author</h2>

**Rahul Raj Jaiswal**  
*Cybersecurity & Blockchain Enthusiast | Full-Stack Software Engineer*

- **GitHub:** [@Rahul130405](https://github.com/Rahul130405)
- **LinkedIn:** [Rahul Raj Jaiswal](https://www.linkedin.com/in/rahulrajjaiswal/)

---

<h2 id="license">📄 License</h2>

This repository does not currently include an open-source license file. All rights reserved. Please contact the author regarding permissions or licensing inquiries.
