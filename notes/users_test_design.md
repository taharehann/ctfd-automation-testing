# Test Notes: Users Directory and Public Profile Module (CTFd)

Module: Users Listing and Public Profile (`/users`, `/users/<id>`)
Techniques used: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA), Use Case / Scenario Testing, Error Guessing

## What the users directory and profile accept

Rules verified by inspecting CTFd's source code (`CTFd/views.py`, `CTFd/themes/core/templates/users/`) and testing on the live instance:

1. **Users Directory (`/users`)**:
   - Lists all registered, non-hidden, non-banned users regardless of whether they have scored points (in contrast to the Scoreboard which only displays users with > 0 points).
   - Table columns: `User`, `Website`, `Affiliation`, `Country`.
   - Search form: filters by `field` (`name`, `affiliation`, `website`, `country`) and query string `q`.
   - Clicking a user's name opens their public profile at `/users/<id>`.
2. **Public Profile (`/users/<id>`)**:
   - Displays the username in `<h1>{{ user.name }}</h1>`.
   - Displays affiliation badge, country flag, and website external link if configured.
   - When a user has solved challenges, displays place, total score (e.g., `100 points`), and a **Solves** table containing the challenge name, category, point value, and timestamp.
   - For users with 0 solves, the Solves table and score are not displayed.
3. **Invalid or Non-Existent Users**:
   - Accessing a non-existent user ID (e.g., `/users/999999`) returns HTTP 404 with the CTFd error page containing `"404 Not Found"`.

---

## 1. Equivalence Class Partitioning (ECP)

| ID | Aspect | Class | Valid / Invalid | Sample Input | Expected Result |
|---|---|---|---|---|---|
| USR-EC1 | Directory listing | All registered users | Valid | `/users` | Directory loads, table columns present |
| USR-EC2 | User ID | Valid existing user ID | Valid | `/users/{valid_id}` | Profile page opens with user's name in `h1` |
| USR-EC3 | User ID | Non-existent user ID | Invalid | `/users/999999` | 404 page displayed (`404 Not Found`) |
| USR-EC4 | User Search | Query matches existing user name | Valid | `field=name&q={exact_user}` | Exactly matching user row is listed in table |
| USR-EC5 | User Search | Query matches no users | Invalid | `field=name&q=nonexistent_xyz_999` | 0 matching rows returned in table |

---

## 2. Boundary Value Analysis (BVA)

| ID | Aspect | Boundary | Value | Expected Result |
|---|---|---|---|---|
| USR-BVA1 | Score points | 0 points (min score boundary) | Freshly registered user | User is listed in `/users` table (even with 0 points) |
| USR-BVA2 | Solves count | 1 solve (first solve boundary) | Solves Test Challenge (100 pts) | Profile shows `100 points` and 1 entry in Solves table |
| USR-BVA3 | Pagination | First page (page = 1) | `/users?page=1` | Page loads successfully, displays users table |
| USR-BVA4 | Pagination | Out-of-bounds page | `/users?page=9999` | Returns valid page with 0 rows, does not crash |

---

## 3. Use Case / Scenario Testing

| ID | Scenario | Steps | Expected Outcome |
|---|---|---|---|
| USR-UC1 | Directory-to-Profile Navigation | 1. Register a new user.<br>2. Navigate to `/users`.<br>3. Locate user in table and click link. | Browser navigates to `/users/<id>` and header matches username. |
| USR-UC2 | Solve Reflection Lifecycle | 1. Register a new user.<br>2. Submit correct flag for Test Challenge.<br>3. Open user profile `/users/<id>`. | Solves section appears, challenge name `Test Challenge` and `100` points displayed. |

---

## 4. Error Guessing

| ID | Heuristic / Guess | Input | Expected Result |
|---|---|---|---|
| USR-EG1 | Extremely large non-existent user ID | `/users/99999999` | Returns 404 without 500 error |
| USR-EG2 | Special characters in search query | `field=name&q=<script>` | Safely escaped, no XSS, 0 results returned |
