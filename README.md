# ⛓️ ChainVote

### **Transparent. Immutable. Trustless.**  
*The next generation of digital democracy, powered by cryptographic ledgers.*

---

[![Security: SHA-256](https://img.shields.io/badge/Security-SHA--256-blue.svg)](https://en.wikipedia.org/wiki/SHA-2)
[![Encryption: AES-256](https://img.shields.io/badge/Encryption-AES--256-emerald.svg)](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)
[![Framework: Django](https://img.shields.io/badge/Framework-Django-092e20.svg)](https://www.djangoproject.com/)
[![Styling: Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38bdf8.svg)](https://tailwindcss.com/)

## 📌 Overview

**ChainVote** is a decentralized voting protocol designed to eliminate electoral fraud and restore public trust. By leveraging blockchain principles—without the overhead of a public gas-based network—ChainVote ensures that every vote is **mathematically verifiable**, **permanently recorded**, and **completely anonymous**.

Traditional voting systems rely on "blind trust" in centralized databases. ChainVote replaces trust with **cryptographic proof**.

---

## 🌟 Key Features

### 🛡️ Security & Integrity
*   **SHA-256 Blockchain Chaining:** Every vote (block) is linked to the previous one via a cryptographic hash. Any attempt to alter a past vote breaks the entire chain instantly.
*   **AES-256 Ballot Encryption:** Vote payloads are secured using military-grade encryption before being committed to the ledger.
*   **Tamper-Evident Ledger:** A built-in integrity validator that scans the entire chain for consistency.

### 👤 Privacy-First
*   **Zero-Knowledge Identity Hashing:** Voter IDs (Aadhaar/Roll No) are hashed client-side using a one-way salt. We verify your right to vote without ever storing your actual identity.
*   **Anonymous Ballots:** The link between the voter's identity and their choice is cryptographically severed.

### 📊 Transparency & Control
*   **Live Ledger Explorer:** A public audit trail where anyone can verify their vote's presence on the chain using a private receipt.
*   **Real-Time Results:** Automated tallying that only unlocks once the election cycle concludes.
*   **SOC Dashboard:** A Security Operations Center (SOC) that monitors network anomalies and duplicate voting attempts.

---

## 🧠 How It Works

1.  **Authenticate:** The voter enters their unique ID. The system generates a one-way cryptographic hash.
2.  **Encrypt:** The voter selects a candidate. The ballot is sealed in an AES-256 encrypted envelope.
3.  **Mine:** The system generates a new block containing the encrypted payload and the hash of the previous block.
4.  **Verify:** The voter receives a digital receipt (Block Hash) to audit the public ledger.

---

## 🏗️ Project Structure

```text
CHAINVOTE/
├── chainvote/              # Core System Configuration
│   ├── settings.py         # Security & App Config
│   └── urls.py             # Global Routing
├── voting/                 # Main Application Logic
│   ├── management/         # Custom CLI tools (Data Seeding)
│   ├── migrations/         # Database Evolution
│   ├── static/             # Assets (CSS/JS)
│   ├── templates/          # Apple-style UI (Glassmorphism)
│   ├── utils/              # The "Engine"
│   │   ├── blockchain.py   # Chain Logic & SHA-256 Chaining
│   │   └── encryption.py   # AES-256 Implementation
│   ├── models.py           # Ledger & Election Schemas
│   └── views.py            # Logic for Booth & Dashboard
├── db.sqlite3              # Local Ledger Store
└── manage.py               # System Entry Point
```

## 📸 Screenshots

<div align="center">
  <img src="Screenshot 2026-04-07 190219.png" width="800" alt="Dashboard View">
  <p><i>System Overview and Dashboard</i></p>
  <br>
  <img src="Screenshot 2026-04-07 190243.png" width="800" alt="Login Page">
  <p><i>Secure Authentication Interface</i></p>
  <br>
  <img src="Screenshot 2026-04-07 190305.png" width="800" alt="Voting Booth">
  <p><i>Encrypted Digital Voting Booth</i></p>
  <br>
  <img src="Screenshot 2026-04-07 190317.png" width="800" alt="Blockchain Explorer">
  <p><i>Live Immutable Ledger Explorer</i></p>
  <br>
  <img src="Screenshot 2026-04-07 190431.png" width="800" alt="Results Page">
  <p><i>Transparent Election Results</i></p>
</div>

---

## ⚙️ Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Backend** | Django 4.2 | Application Framework |
| **Frontend** | Tailwind CSS | UI/UX (Apple Glassmorphism) |
| **Cryptography** | PyCryptodome / SHA-256 | Data Security |
| **Database** | SQLite / PostgreSQL | Permanent Storage |
| **Logic** | Python 3.10+ | Blockchain & Tallying |

---

## ⚡ Setup Instructions (Windows)

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
pip install cryptography  # Ensure crypto-libs are present
```

### 4. Initialize Ledger
```powershell
python manage.py migrate
python manage.py seed_data  # Optional: Populate with sample elections
```

### 5. Launch
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000` to enter the voting booth.

---

## 🔌 API Endpoints (Read-Only)

*   `GET /api/elections/` — List all active and ended elections.
*   `GET /api/elections/<id>/results/` — Fetch tallied results (post-election).
*   `GET /api/blockchain/<election_id>/` — View the raw public ledger.

---

## 🔐 Security Highlights

> **"Mathematical Integrity over Human Promise."**

*   **Immutable History:** Once a block is mined, it cannot be changed without recalculating every subsequent hash, a computationally expensive task detected by the SOC.
*   **AES-256 GCM:** Ensures not just confidentiality but also authenticity of the vote payload.
*   **CSRF & SQLi Protection:** Built on top of Django's hardened security middleware.

---

## 🚀 Future Roadmap

*   [ ] **Decentralized Nodes:** Shifting from a single ledger to distributed nodes for higher availability.
*   [ ] **Biometric Integration:** Face-ID/Fingerprint authentication for Aadhaar verification.
*   [ ] **Blind Signatures:** Further enhancing anonymity using RSA blind signatures.

---

## ⚠️ Realistic Disclaimer

This project is developed as an MVP for a hackathon. While it utilizes industry-standard cryptographic primitives, it should be audited by security professionals before any use in real-world large-scale governmental elections.

---

## 👨‍💻 Author

## 👨‍💻 Author

**Rahul Raj Jaiswal**
*Cybersecurity & Blockchain Enthusiast*

🔗 LinkedIn: https://www.linkedin.com/in/rahulrajjaiswal/


---

### **🏆 One Vote. One Chain. Total Trust.**
