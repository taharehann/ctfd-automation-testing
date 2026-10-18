# Software Quality Engineering (SQE) — Assignment 3
## Unit & System Test Automation Report: CTFd Testing (Member 2)

---

### Executive Summary

This report documents the automated software testing implementation for **Member 2** of the SQE Group Project on **CTFd v3.8.8**.

The project scope was strictly demarcated into two non-overlapping halves between group members:
- **Member 1 Modules**: User Authentication (`/register`, `/login`, `/logout`), Challenges (`/challenges`), and Scoreboard (`/scoreboard`).
- **Member 2 Modules**:
  1. **Module A — Profile & Settings (`/settings`)**: User personal profile updates, password modification, email change with authentication confirmation, website URL formatting, country selection, and affiliation management.
  2. **Module B — Users Directory & Public Profile (`/users`, `/users/<id>`)**: Global users listing, search by query and field, profile rendering, score reflection, and solves history verification.
  3. **Module C — Admin Panel (`/admin`)**: Administrative access control (`@admins_only`), custom page publication lifecycle (`/admin/pages`), and user management (account state transitions, user banning, and security restrictions).

All test suites were developed using **Python `unittest`** and **`ddt` (Data-Driven Testing)**, interfaced with **Selenium WebDriver (Chrome)**. Test execution supports multi-threaded / multi-process parallelization via `ProcessPoolExecutor` with zero test crosstalk and zero reliance on arbitrary `sleep` calls for assertions.

---

### Summary of Test Execution

| Module | Test Design Document | Data Source | Total Tests | Passed | Failed | Pass Rate |
|---|---|---|:---:|:---:|:---:|:---:|
| **Module A: Profile & Settings** | `notes/settings_test_design.md` | `data/settings_data.csv` | 15 | 15 | 0 | **100%** |
| **Module B: Users Directory & Profile** | `notes/users_test_design.md` | `data/users_data.csv` | 13 | 13 | 0 | **100%** |
| **Module C: Admin Panel** | `notes/admin_test_design.md` | `data/admin_data.csv` | 12 | 12 | 0 | **100%** |
| **Total Member 2 Suite** | — | — | **40** | **40** | **0** | **100%** |

---

### Testing Techniques Applied

In compliance with the assignment instructions, Member 2 utilized:
1. **Equivalence Class Partitioning (ECP)** — Mandatory for all modules.
2. **Boundary Value Analysis (BVA)** — Mandatory for all modules.
3. **Techniques Member 1 Did NOT Use**:
   - **Syntax Testing**: Applied to Module A (Profile & Settings) to evaluate website URL parsing, validating protocols schemes (`http://`, `https://`, and invalid schemes like `ftp://`), path strings, and missing scheme syntax.
   - **Pairwise Testing (All-Pairs)**: Applied to Module A (Profile & Settings) across multi-dimensional profile input combinations (Name × Email × Affiliation × Website × Country) to verify combinatorial field updates without combinatorial explosion.
   - **Cause-Effect Graphing / Decision Table Testing**: Applied to Module C (Admin Panel) to model:
     - Access Control Matrix: 4 rules mapping User Authentication State × User Role to Authorization Outcome (Redirect to Login vs. 200 OK Dashboard).
     - Page Publication Matrix: 5 rules mapping Draft Status × Hidden Flag × Auth Required Flag × Visitor Auth State to public accessibility and navbar inclusion.
4. **State Transition Testing (STT)**:
   - Applied to Module C to test the complete account suspension lifecycle:
     $$\text{Active User} \xrightarrow{\text{Admin Ban}} \text{Banned User (403 Forbidden)} \xrightarrow{\text{Admin Unban}} \text{Active User (Restored)}$$
5. **Use Case / Scenario Testing**:
   - Directory-to-Profile Navigation (`USR-UC1`): End-to-end user journey from search to public profile inspection.
   - Challenge Solve Reflection (`USR-UC2`): Verifying that solving a challenge immediately populates the user's public solves table and score.
   - Custom Page Lifecycle (`ADM-UC1`): End-to-end flow of page creation, navbar injection, content verification, and status mutation.
6. **Error Guessing**:
   - Non-existent numeric user IDs (`/users/999999`) and extremely large integers (`/users/99999999`).
   - XSS injection strings in search queries (`<script>`).
   - Non-existent administrative routes (`/admin/nonexistent_xyz_999`).

---

### Architectural Design & Robustness Decisions

1. **Strict Test Isolation via Dynamic Account Generation**:
   Every test generates a fresh user account using `uuid.uuid4().hex[:8]`. No tests share user state or credentials, ensuring that parallel execution with `--workers 2` or `--workers 4` never suffers from race conditions or database lock contention.
2. **Deterministic Browser Synchronization**:
   No arbitrary `time.sleep` calls are used for assertions. All waits utilize `WebDriverWait` with expected conditions (`visibility_of_element_located`, `presence_of_element_located`, `url_contains`, and custom lambdas).
3. **Display Scaling & Viewport Interception Defense**:
   Under Windows 1080p display scaling (150%), default browser viewport heights cause CTFd's sticky footer (`footer.footer`) to overlap submit buttons. To permanently prevent `ElementClickInterceptedException`, the test runner configures:
   - `--force-device-scale-factor=1`
   - `--window-size=1920,1080`
   - Helper `safe_click` with `arguments[0].scrollIntoView({block: 'center'})`
4. **CodeMirror & Hidden Field Handling**:
   CTFd's page editor uses CodeMirror overlaying hidden textarea `#admin-pages-editor`. Tests programmatically interact with CodeMirror via `document.querySelector('.CodeMirror').CodeMirror.setValue(...)` while ensuring form synchronization on submission.

---

### Project Deliverables

1. **Automated Test Files**:
   - `tests/test_settings.py` (15 tests)
   - `tests/test_users.py` (13 tests)
   - `tests/test_admin.py` (12 tests)
2. **Parameterized Data Files**:
   - `data/settings_data.csv` (13 test vectors)
   - `data/users_data.csv` (9 test vectors)
   - `data/admin_data.csv` (9 test vectors)
3. **Test Design Notes**:
   - `notes/settings_test_design.md`
   - `notes/users_test_design.md`
   - `notes/admin_test_design.md`
4. **Test Configuration & Execution**:
   - `test_config.py` (groups: `settings`, `users`, `admin`; suite: `full`)
   - `run_tests.py` (supporting `--group`, `--suite full`, `--workers N`, `--delay N`)
5. **Excel Test Case Workbook**:
   - `docs/CTFd_Test_Cases_Member2.xlsx` (Sheets: `Test Cases`, `Settings Data`, `Users Data`, `Admin Data`, `Summary` with dynamic formulas)
