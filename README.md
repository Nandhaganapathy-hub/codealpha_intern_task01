# 🔍 Data Redundancy Removal System (DRRS)

> **CodeAlpha Internship Project** — A full-stack web application that detects and prevents duplicate data entries using exact matching and AI-powered fuzzy string comparison.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![MySQL](https://img.shields.io/badge/MySQL-8.0-orange) ![RapidFuzz](https://img.shields.io/badge/RapidFuzz-3.6-purple)

---

## 📁 Complete Project Structure

```
codealpha_intern_task1/
│
├── app.py                    ← Flask application + all routes
├── config.py                 ← DB credentials & system thresholds
├── requirements.txt          ← Python dependencies
├── .env.example              ← Environment variable template
├── .gitignore
│
├── modules/                  ← Backend logic (Python packages)
│   ├── __init__.py
│   ├── db.py                 ← MySQL connection manager
│   ├── validator.py          ← Input validation (regex-based)
│   ├── detector.py           ← Duplicate detection engine (RapidFuzz)
│   └── dashboard.py          ← Dashboard statistics queries
│
├── templates/                ← Jinja2 HTML templates
│   ├── base.html             ← Shared layout (navbar, flash, scripts)
│   ├── index.html            ← Dashboard with charts & stats
│   ├── add_record.html       ← Data entry form
│   ├── result.html           ← Classification result page
│   ├── records.html          ← View all records + search
│   └── logs.html             ← Submission audit log
│
├── static/
│   └── css/
│       └── style.css         ← Dark glassmorphism design system
│
├── database/
│   └── schema.sql            ← All CREATE TABLE + seed data
│
└── tests/
    ├── __init__.py
    ├── test_detector.py      ← Unit tests (pytest)
    └── sample_data.csv       ← Sample data for testing
```

---

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `records` | Master table — stores only UNIQUE verified records |
| `submission_log` | Audit trail — logs every attempt with classification |
| `duplicate_pairs` | Pairs of similar records for manual review |
| `dashboard_stats` | Cached counter stats for fast dashboard loading |

---

## 🔧 Step-by-Step Setup Instructions

### Step 1: Prerequisites

Make sure you have installed:
- **Python 3.10+** — [python.org](https://python.org)
- **MySQL 8.0+** — [mysql.com](https://dev.mysql.com/downloads/)
- **pip** (comes with Python)

Verify:
```bash
python --version   # Should say Python 3.10.x or higher
mysql --version    # Should say mysql  Ver 8.x
```

---

### Step 2: Clone / Open the Project

```bash
cd c:\nandha\codealpha_intern_task1
```

---

### Step 3: Create Python Virtual Environment

```bash
# Create virtual environment (isolates project dependencies)
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# OR on Windows CMD
venv\Scripts\activate.bat
```

You'll see `(venv)` appear in your terminal prompt — that means it's active.

---

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `Flask` — Web framework
- `mysql-connector-python` — MySQL driver
- `rapidfuzz` — Fuzzy string matching
- `pandas` — Data manipulation for CSV processing
- `flask-cors` — Cross-origin requests

---

### Step 5: Set Up MySQL Database

Open MySQL shell or MySQL Workbench, then run:

```bash
# From terminal
mysql -u root -p < database/schema.sql
```

OR open MySQL Workbench → Open SQL Script → `database/schema.sql` → Execute.

This creates:
- The `data_redundancy_db` database
- All 4 tables
- 10 sample seed records

---

### Step 6: Configure Your Database Credentials

Open `config.py` and update:

```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",         # ← Your MySQL username
    "password": "YOUR_PASSWORD", # ← Your MySQL password
    "database": "data_redundancy_db",
    ...
}
```

OR copy `.env.example` to `.env` and fill in your values (more secure).

---

### Step 7: Run the Application

```bash
python app.py
```

You should see:
```
=======================================================
  DATA REDUNDANCY REMOVAL SYSTEM
  Running at http://127.0.0.1:5000
=======================================================
```

Open your browser: **http://127.0.0.1:5000**

---

## 🧪 Testing Procedure

### Manual Testing

Use these test cases with the **Add Record** form:

#### Test 1: Unique Record (should be ACCEPTED ✅)
```
Unique ID: EMP099
Full Name: Deepa Krishnamurthy
Email:     deepa.k@testmail.com
Phone:     9500012345
City:      Coimbatore
State:     Tamil Nadu
```

#### Test 2: Exact Duplicate (should be BLOCKED 🚫)
```
Unique ID: EMP099          ← Same ID as above
Full Name: Deepa K         ← Different name
Email:     deepa.k@testmail.com  ← Same email
Phone:     9500012345      ← Same phone
City:      Coimbatore, Tamil Nadu
```

#### Test 3: False Positive (similar but not identical ⚠️)
```
Unique ID: EMP100
Full Name: Deepa Krishnamurty  ← Typo in last name
Email:     deepa.krish@other.com  ← Different email
Phone:     9500054321      ← Different phone
Address:   Same address as above
City:      Coimbatore, Tamil Nadu
```

### Automated Unit Tests

```bash
# Install pytest first
pip install pytest

# Run all tests
python -m pytest tests/ -v
```

Expected output:
```
tests/test_detector.py::TestValidator::test_valid_record_passes        PASSED
tests/test_detector.py::TestValidator::test_missing_required_fields    PASSED
tests/test_detector.py::TestValidator::test_invalid_email              PASSED
tests/test_detector.py::TestValidator::test_invalid_phone              PASSED
tests/test_detector.py::TestDetector::test_exact_email_match_is_redundant PASSED
tests/test_detector.py::TestDetector::test_no_match_returns_none       PASSED
```

---

## 📊 Feature Summary

| Feature | Description |
|---------|-------------|
| **Dashboard** | Live stats: total, unique, redundant, false positive counts |
| **Donut Chart** | Visual breakdown of classification distribution |
| **Data Entry Form** | Validated form with real-time client-side checks |
| **Duplicate Detection** | Exact match on email/phone/ID |
| **Fuzzy Matching** | RapidFuzz `token_sort_ratio` for names, `partial_ratio` for addresses |
| **Classification Result** | Detailed verdict page with similarity meter animation |
| **View Records** | Searchable master records table |
| **Submission Logs** | Full audit trail with filter by classification |
| **Delete Records** | Remove records with confirmation dialog |
| **REST API** | `/api/check` and `/api/stats` JSON endpoints |

---

## 🧠 How Duplicate Detection Works

```
Incoming Record
      │
      ▼
┌─────────────────────────────────────┐
│  STEP 1: Exact Match Check          │
│  - email == existing email?         │
│  - phone == existing phone?         │
│  - unique_id == existing ID?        │
└─────────────────────────────────────┘
      │ Match Found ──→ REDUNDANT (100% score, REJECTED)
      │ No Match
      ▼
┌─────────────────────────────────────┐
│  STEP 2: Fuzzy Similarity Check     │
│  (RapidFuzz against all records)    │
│                                     │
│  Name Score  = token_sort_ratio()   │
│  Addr Score  = partial_ratio()      │
│  Combined    = 60% Name + 40% Addr  │
└─────────────────────────────────────┘
      │ Score ≥ 95% ──→ REDUNDANT (REJECTED)
      │ Score 75-94% ─→ FALSE_POSITIVE (FLAGGED)
      │ Score < 75% ──→ UNIQUE (SAVED TO DATABASE ✅)
```

---

## ⚙️ Configurable Thresholds

In `config.py`:

```python
DUPLICATE_THRESHOLD    = 95   # ≥95% → REDUNDANT
FALSE_POSITIVE_THRESHOLD = 75  # 75-94% → FALSE_POSITIVE
```

Increase `DUPLICATE_THRESHOLD` to be more lenient. Decrease `FALSE_POSITIVE_THRESHOLD` to catch more potential duplicates.

---

## 🚀 Technologies Used

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML5 + CSS3 + JavaScript | UI and user interaction |
| CSS Design | Custom Vanilla CSS | Glassmorphism dark theme |
| Charts | Chart.js | Dashboard donut chart |
| Icons | Font Awesome 6 | UI iconography |
| Backend | Flask 3.0 | Web framework |
| Database | MySQL 8.0 | Persistent storage |
| DB Driver | mysql-connector-python | Python ↔ MySQL bridge |
| Fuzzy Match | RapidFuzz 3.6 | String similarity scoring |
| Data Processing | Pandas | CSV/bulk processing |
| Testing | pytest + unittest.mock | Automated unit tests |
