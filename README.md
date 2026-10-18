# CTFd Selenium Test Automation

Automated Selenium test suites for [CTFd](https://github.com/CTFd/CTFd) (v3.8.8), an open-source Capture-The-Flag platform built on Python and Flask. Developed for Software Quality Engineering (SQE) Assignment 3.

---

## Project Overview & Team Contributions

The test automation project is divided across two members covering six distinct functional modules with zero overlapping tests:

| Member | Assigned Modules | Test Files | Parameterized Datasets | Test Design Notes | Automated Tests |
|---|---|---|---|---|:---:|
| **Member 1** | **Authentication** (Register, Login, Logout)<br>**Challenges** (Flag Submission)<br>**Scoreboard** | `tests/test_smoke.py`<br>`tests/test_auth_register.py`<br>`tests/test_auth_login.py`<br>`tests/test_challenges.py`<br>`tests/test_scoreboard.py` | `data/register_data.csv`<br>`data/login_data.csv`<br>`data/flag_data.csv` | `notes/auth_test_design.md`<br>`notes/challenges_test_design.md`<br>`notes/scoreboard_test_design.md` | **49** |
| **Member 2** | **Profile & Settings** (`/settings`)<br>**Users Directory & Profile** (`/users`, `/users/<id>`)<br>**Admin Panel** (`/admin`, `/admin/pages`, `/admin/users`) | `tests/test_settings.py`<br>`tests/test_users.py`<br>`tests/test_admin.py` | `data/settings_data.csv`<br>`data/users_data.csv`<br>`data/admin_data.csv` | `notes/settings_test_design.md`<br>`notes/users_test_design.md`<br>`notes/admin_test_design.md` | **40** |
| **Total** | **Full CTFd Test Automation Suite** | **8 test suites** | **6 CSV datasets** | **6 design documents** | **89 Tests (100% Pass)** |

---

## Testing Techniques Applied

- **Equivalence Class Partitioning (ECP)**: Input domain partitioning applied across all modules.
- **Boundary Value Analysis (BVA)**: Upper and lower bounds on field lengths, scores, solve counts, and pagination limits.
- **Syntax Testing**: Validation of URI schemes (`http://`, `https://`, and invalid schemes such as `ftp://`) and malformed URL structures in user profiles.
- **Pairwise Testing (All-Pairs)**: Combinatorial test generation across orthogonal profile fields (affiliation, website, country).
- **Cause-Effect Graphing / Decision Table Testing**: Comprehensive logic modeling for:
  - Role-based Access Control Matrix (`unauth`, `regular`, `admin` accessing administrative routes).
  - Multi-variable Page Publication Matrix (`draft`, `hidden`, `auth_required`, visitor auth status).
- **State Transition Testing (STT)**: User account suspension lifecycle (`Active` $\rightarrow$ `Banned [403]` $\rightarrow$ `Unbanned [Active]`).
- **Use Case / Scenario Testing**: Multi-step workflows including Directory-to-Profile Navigation, Challenge Solve Reflection, and Custom Page Navbar Publication.
- **Error Guessing**: Robust handling of non-existent large numeric user IDs, script injections in search queries, and invalid admin subroutes.

---

## Deliverables & Documentation

- **Test Workbooks (Excel)**:
  - `docs/CTFd_Test_Cases.xlsx` (Member 1 Test Cases & Summary)
  - `docs/CTFd_Test_Cases_Member2.xlsx` (Member 2 Test Cases, Datasets, and Dynamic Formula Summary)
- **Summary Reports**:
  - `docs/Unit Test Automation Summary Report CTFd.pdf` (Member 1 Report)
  - `docs/Member2_Summary_Report.md` (Member 2 Report)
- **Setup Videos**:
  - `docs/Setup_video.mp4` (Cloning, installing, and starting CTFd)
  - `docs/Setup_video_Part2.mp4` (Setup wizard and initial admin configuration)

---

## Setup & Prerequisites

Prerequisites: Python 3.9+ (Python 3.11/3.12 recommended), Git, and Google Chrome.

### 1. Start Local CTFd Instance
Clone and start CTFd in a separate directory next to this repository:
```bash
git clone https://github.com/CTFd/CTFd.git
cd CTFd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python serve.py
```
CTFd runs locally at `http://localhost:4000`. Keep this terminal window open.

### 2. Complete CTFd Initial Setup (One-time)
Open `http://localhost:4000` in your browser and complete the initial configuration:
- **Event Name:** `TestCTF`
- **User Mode:** Users
- **Admin Account:** `admin` / `Admin@12345` / `admin@test.com`
- **Email Verification:** Disabled

### 3. Add Benchmark Challenge
Log in as administrator and create one challenge under **Admin Panel $\rightarrow$ Challenges $\rightarrow$ Create**:
- **Name:** `Test Challenge`
- **Category:** `Web`
- **Value:** `100`
- **Type:** `standard`
- **Flag:** `flag{test123}` (static, case-sensitive)
- **State:** `Visible`

### 4. Setup Test Runner Environment
In a second terminal, inside this repository:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running the Automated Tests

CTFd must be running on `http://localhost:4000` while executing tests.

```bash
# Run the entire test suite (89 tests, sequential)
python run_tests.py --suite full

# Run full test suite in parallel with 2 workers (recommended for SQLite)
python run_tests.py --suite full --workers 2

# Run Member 2 modules only
python run_tests.py --group settings users admin --workers 2

# Run individual test groups
python run_tests.py --group settings      # Profile & Settings (15 tests)
python run_tests.py --group users         # Users Directory & Profile (13 tests)
python run_tests.py --group admin         # Admin Panel (12 tests)
python run_tests.py --group challenges    # Challenge submissions (12 tests)
python run_tests.py --group auth          # Register & Login (27 tests)
python run_tests.py --group scoreboard    # Scoreboard (9 tests)
python run_tests.py --group smoke         # Smoke tests (1 test)

# Quick suite (smoke + auth)
python run_tests.py --suite quick

# Slow-motion execution for live presentation / demonstration (adds pause per step)
python run_tests.py --group settings --delay 2

# List all test IDs in their exact configured execution order
python run_tests.py --list
```

You can also run any test module directly via standard `unittest`:
```bash
python tests/test_settings.py
python tests/test_users.py
python tests/test_admin.py
```

---

## Test Architecture & Configuration

All execution settings are configured in `test_config.py`:

- **Groups**: `smoke`, `auth`, `challenges`, `scoreboard`, `settings`, `users`, `admin`. Groups execute sequentially in this defined order.
- **Suites**:
  - `quick`: `smoke`, `auth`
  - `full`: all 7 groups (`smoke`, `auth`, `challenges`, `scoreboard`, `settings`, `users`, `admin`)
- **Execution Order (`METHOD_ORDER`)**: Deterministic method execution within test classes.
- **Strict Test Isolation**: Every automated test registers a dynamically generated account with UUID suffixes (`uuid.uuid4().hex[:8]`). Tests maintain zero shared state, eliminating database locks and enabling clean multi-worker parallel execution.
- **Display Scaling & Safe Interaction**: Chrome instances launch with `--force-device-scale-factor=1` and `--window-size=1920,1080`, using a centered scroll mechanism (`scrollIntoView({block: 'center'})`) to eliminate element interception from CTFd's sticky footer.
