# Test Notes: Admin Panel Module (CTFd)

Module: Admin Dashboard, Pages Management, and User Administration (`/admin`, `/admin/pages`, `/admin/users`)  
Techniques used: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA), Cause-Effect Graphing / Decision Table Testing, State Transition Testing, Use Case Testing, Error Guessing

## What the Admin Panel Accepts and Enforces

Verified by inspecting CTFd source code (`CTFd/admin/`, `CTFd/views.py`, `CTFd/utils/initialization/`) and live behavior on CTFd 3.8.8:

1. **Access Control (`@admins_only`)**:
   - Routes starting with `/admin` require an authenticated session where `user.type == 'admin'`.
   - Unauthenticated visitors accessing `/admin` are redirected to `/login?next=%2Fadmin`.
   - Regular (non-admin) authenticated users accessing `/admin` are also redirected to `/login?next=%2Fadmin`.
   - Authenticated admins (`admin` / `Admin@12345`) successfully access the admin panel at `/admin` (which renders the Admin Statistics dashboard).

2. **Custom Pages Management (`/admin/pages`)**:
   - Custom pages are created at `/admin/pages/new` with fields: `title`, `route`, `content` (Markdown or HTML), `draft` (bool), `hidden` (bool), `auth_required` (bool).
   - **Published & Visible** (`draft=False`, `hidden=False`): Page link is automatically injected into the global navbar on all pages, and direct URL `/<route>` renders content with HTTP 200.
   - **Hidden Page** (`draft=False`, `hidden=True`): Page link does NOT appear in the navbar, but direct URL `/<route>` is accessible.
   - **Draft Page** (`draft=True`): Page is unpublished. Visiting `/<route>` returns HTTP 404 Not Found.
   - **Authentication Required** (`auth_required=True`): Unauthenticated visitors accessing `/<route>` are redirected to `/login?next=/<route>`. Authenticated users access the page with HTTP 200.

3. **User Administration (`/admin/users`)**:
   - Lists all registered users with status indicators (Admin, Verified, Hidden, Banned).
   - Clicking a user opens their admin detail page at `/admin/users/<id>`.
   - When a user is **banned**:
     - The user's authenticated requests are immediately blocked with HTTP 403 ("You have been banned from this CTF").
     - The user profile displays the `banned` status badge in the admin panel.
   - When a user is **hidden**:
     - The user is omitted from public `/users` and `/scoreboard` listings.

---

## 1. Equivalence Class Partitioning (ECP)

| ID | Aspect | Class | Valid / Invalid | Sample Input | Expected Result |
|---|---|---|---|---|---|
| ADM-EC1 | Role Authorization | Unauthenticated visitor | Invalid | Access `/admin` | Redirected to `/login?next=%2Fadmin` |
| ADM-EC2 | Role Authorization | Authenticated regular user | Invalid | Access `/admin` | Redirected to `/login?next=%2Fadmin` |
| ADM-EC3 | Role Authorization | Authenticated administrator | Valid | Access `/admin` with admin creds | 200 OK, Admin Panel dashboard loads |
| ADM-EC4 | Page Creation | Valid published page | Valid | Title: `Rules`, Route: `rules`, Draft: False | Page saved, accessible at `/rules`, shown in nav |
| ADM-EC5 | Page Creation | Valid draft page | Valid | Title: `Drafts`, Route: `draft-page`, Draft: True | Page saved, accessing `/draft-page` returns 404 |
| ADM-EC6 | Page Creation | Auth-required page | Valid | Title: `Members`, Route: `members`, AuthReq: True | Unauth gets redirect to `/login`, auth gets 200 |
| ADM-EC7 | User Admin | Admin user listing | Valid | Access `/admin/users` | Table of users renders with action controls |

---

## 2. Boundary Value Analysis (BVA)

| ID | Aspect | Boundary | Value | Expected Result |
|---|---|---|---|---|
| ADM-BVA1 | Route Length | Single character route | Route: `r` | Valid custom page created at `/r` |
| ADM-BVA2 | Route Format | Multi-word hyphenated route | Route: `official-rules-2026` | Valid custom page created at `/official-rules-2026` |
| ADM-BVA3 | Empty Title | Min boundary violation (0 chars) | Title: `""` | Submission rejected or browser form prevents submit |

---

## 3. Cause-Effect Graphing / Decision Table Testing

### 3.1 Access Control Matrix

| Rule # | User Authenticated? | User Role == Admin? | Target Route | Expected Effect |
|---|---|---|---|---|
| R1 | No | N/A | `/admin` | E1: Redirect to `/login` |
| R2 | Yes | No (Regular) | `/admin` | E1: Redirect to `/login` |
| R3 | Yes | Yes (Admin) | `/admin` | E2: 200 OK (Admin Dashboard) |
| R4 | No | N/A | `/admin/pages` | E1: Redirect to `/login` |
| R5 | Yes | Yes (Admin) | `/admin/pages` | E3: 200 OK (Pages Manager) |

### 3.2 Page Publication Decision Table

| Rule # | Draft? | Auth Required? | User Logged In? | Hidden? | Expected Route Outcome | Navbar Display |
|---|---|---|---|---|---|---|
| P1 | False | False | Any | False | 200 OK (Page rendered) | Shown in Navbar |
| P2 | False | False | Any | True | 200 OK (Page rendered) | Hidden from Navbar |
| P3 | True | Any | Any | Any | 404 Not Found | Hidden from Navbar |
| P4 | False | True | No | False | Redirect to `/login?next=...` | Shown in Navbar |
| P5 | False | True | Yes | False | 200 OK (Page rendered) | Shown in Navbar |

---

## 4. State Transition Testing (STT)

### User Ban Lifecycle
1. **State 1 (Active)**: User registers and logs in. Submits correct flag for Test Challenge. Solves reflected.
2. **State 2 (Banned)**: Admin navigates to `/admin/users/<id>` or uses admin action to set `banned=True`.
3. **State 3 (Access Attempt)**: User attempts to view challenges or profile while banned -> Returns HTTP 403 with message `"You have been banned from this CTF"`.
4. **State 4 (Unbanned)**: Admin unbans user -> User can access challenges again.

---

## 5. Use Case / Scenario Testing

| ID | Scenario | Steps | Expected Outcome |
|---|---|---|---|
| ADM-UC1 | End-to-End Page Lifecycle | 1. Admin creates published page `/announcements`.<br>2. Guest verifies page renders in navbar and URL.<br>3. Admin edits page to `Draft`.<br>4. Guest visits URL again. | Guest initially sees page; after draft update, guest receives 404. |
| ADM-UC2 | Admin Access Enforcement | 1. Register regular user `user1`.<br>2. Try navigating to `/admin`.<br>3. Verify redirected to login.<br>4. Login as admin and access `/admin`. | Access denied for regular user; permitted for admin. |

---

## 6. Error Guessing

| ID | Heuristic / Guess | Input | Expected Result |
|---|---|---|---|
| ADM-EG1 | Non-existent admin route | `/admin/nonexistent_feature_123` | Returns 404 error page gracefully |
| ADM-EG2 | Special characters in page route | Route: `custom@page!#$` | Handled safely, sanitized or rejected |
