#  ChainVote: Enterprise Cryptographic Ledger
**Decentralized. Anonymous. Un-hackable.**

ChainVote is a next-generation digital democracy platform built on a custom blockchain architecture. Designed for high-stakes environments, it replaces traditional vulnerable databases with an immutable, transparent, and secure cryptographic ledger.

---

## Key Cybersecurity Features

* **Custom SHA-256 Blockchain:** Every vote is mined as a unique block, cryptographically linked to the previous one. Any attempt to alter a single vote breaks the entire chain.
* **Zero-Knowledge Identity Hashing:** Voter IDs (Aadhaar/Roll Numbers) are run through a one-way SHA-256 salt-hash. Raw identity data is **never** stored on the server.
* **AES-256 Payload Encryption:** Ballots are encrypted at the moment of submission, ensuring that results remain mathematically locked until the election ends.
* **Active Threat SOC Dashboard:** A real-time Security Operations Center that monitors network traffic, logs duplicate voting attempts, and tracks malicious IP addresses in real-time.
* **Verifiable Cryptographic Receipts:** Every voter receives a unique block hash and a printable receipt to independently audit the ledger.

---

##  Technical Stack

* **Backend:** Django (Python 3.11+)
* **Frontend:** Tailwind CSS (Premium Glassmorphism / Apple Aesthetic)
* **Security:** Cryptography (AES-256), Hashlib (SHA-256)
* **Database:** SQLite (Development) / PostgreSQL (Production ready)
* **Integrations:** REST API for third-party auditing nodes

---

##  Setup Guide (Windows)

### Step 1 — Environment Setup
1. Download Python 3.11+ from [python.org](https://python.org/downloads).
2. **Important:** Check "Add Python to PATH" during installation.

### Step 2 — Installation
Open your terminal (PowerShell or CMD) and navigate to the project folder:
```bash
# Navigate to project
cd chainvote

# Create and activate virtual environment
python -m venv env
env\Scripts\activate

# Install requirements
pip install -r requirements.txt