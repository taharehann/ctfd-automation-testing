# Test Notes: Profile and Settings Module (CTFd)

Module: User Profile and Account Settings (`/settings`)
Techniques used: Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA), Syntax Testing, Pairwise Testing

## What the settings page accepts

Rules verified from testing the page in the browser and inspecting CTFd's `UserSchema` (`CTFd/schemas/users.py`):

1. **Username (`name`)**:
   - Cannot be empty after trimming whitespace (min 1, max 128 chars).
   - Must be unique across all users; duplicate name produces `"User name has already been taken"`.
   - Empty or spaces-only produces `"User names must not be empty"`.
2. **Email (`email`)**:
   - Must be a valid email format.
   - Changing email requires providing the correct current password in `confirm`.
   - Missing `confirm` produces `"Please confirm your current password"`.
   - Incorrect `confirm` produces `"Your previous password is incorrect"`.
   - Existing email produces `"Email address has already been used"`.
3. **Password (`password` and `confirm`)**:
   - Changing password requires `confirm` (current password).
   - If `confirm` is omitted, server returns `"Please confirm your current password"`.
   - If `confirm` is incorrect, server returns `"Your previous password is incorrect"`.
   - If `confirm` is correct, the password is updated and server returns `"Your profile has been updated"`.
4. **Website (`website`)**:
   - Optional.
   - If provided, must be a valid URL starting with `http://` or `https://`.
   - Invalid scheme or raw text produces `"Websites must be a proper URL starting with http or https"`.
5. **Affiliation (`affiliation`) and Country (`country`)**:
   - Free text affiliation (up to 128 chars) and ISO 2-letter country code dropdown.
   - Updating these fields succeeds without requiring `confirm` password and persists across page reloads.

---

## 1. Equivalence Class Partitioning (ECP)

| ID | Field | Class | Valid / Invalid | Sample Input | Expected Result |
|---|---|---|---|---|---|
| SET-EC1 | Username | Valid unique name | Valid | `set_{uid}` | Profile updated (`Your profile has been updated`) |
| SET-EC3 | Username | Already taken name | Invalid | `admin` | Rejected (`User name has already been taken`) |
| SET-EC4 | Email | Valid new email with correct confirm | Valid | `new_{uid}@test.com` + `Pass@123` | Profile updated (`Your profile has been updated`) |
| SET-EC5 | Email | Already used email with correct confirm | Invalid | `admin@test.com` + `Pass@123` | Rejected (`Email address has already been used`) |
| SET-EC6 | Email | New email without confirm password | Invalid | `new_{uid}@test.com` (no confirm) | Rejected (`Please confirm your current password`) |
| SET-EC7 | Password | Valid change (correct confirm + new password) | Valid | `Pass@123` + `NewPass@456` | Profile updated (`Your profile has been updated`) |
| SET-EC8 | Password | Wrong confirm password | Invalid | `Wrong@999` + `NewPass@456` | Rejected (`Your previous password is incorrect`) |
| SET-EC9 | Password | New password given without confirm | Invalid | `""` + `NewPass@456` | Rejected (`Please confirm your current password`) |
| SET-EC10 | Website | Valid HTTPS URL | Valid | `https://ctfd.io` | Profile updated (`Your profile has been updated`) |
| SET-EC11 | Website | Valid HTTP URL | Valid | `http://example.com` | Profile updated (`Your profile has been updated`) |
| SET-EC12 | Website | Missing scheme / plain text | Invalid | `example.com` | Rejected (`Websites must be a proper URL starting with http or https`) |

---

## 2. Boundary Value Analysis (BVA)

| ID | Field | Boundary | Input Value | Expected Result |
|---|---|---|---|---|
| SET-BVA1 | Username | Min length - 1 (0 characters, empty) | `""` | Rejected (`User names must not be empty`) |
| SET-BVA2 | Username | Minimum length (1 character) | `"a"` | Profile updated (`Your profile has been updated`) |
| SET-BVA3 | Username | Max length (128 characters) | 128 x `"a"` | Profile updated (`Your profile has been updated`) |
| SET-BVA4 | Website | Empty string (clear website) | `""` | Profile updated (clears website) |

---

## 3. Syntax Testing (Website URL Format)

Syntax testing verifies adherence to formal URL grammatical production rules: `scheme "://" host [path]` where `scheme in {"http", "https"}`.

| ID | Aspect Tested | Grammar Rule Violation | Sample Input | Expected Result |
|---|---|---|---|---|
| SET-SYN1 | Scheme | Unsupported scheme (`ftp://`) | `ftp://ftp.example.com` | Rejected (`Websites must be a proper URL starting with http or https`) |
| SET-SYN2 | Scheme | Missing colon-slash (`http:example.com`) | `http:example.com` | Rejected (`Websites must be a proper URL starting with http or https`) |
| SET-SYN3 | Scheme | Raw domain without scheme | `www.myctf.org` | Rejected (`Websites must be a proper URL starting with http or https`) |
| SET-SYN4 | Valid Syntax | Well-formed HTTPS with path | `https://github.com/ctfd` | Accepted (`Your profile has been updated`) |

---

## 4. Pairwise Testing (Combinatorial Feature Coverage)

Testing combinations of Profile fields (Username, Affiliation, Country, Website) to detect undesirable component interactions with minimal test redundancy:

| ID | Username | Affiliation | Country | Website | Expected Result |
|---|---|---|---|---|---|
| SET-PW1 | Unique new (`{uid}`) | Organization (`Security Lab`) | United States (`US`) | `https://lab.org` | Accepted (`Your profile has been updated`) |
| SET-PW2 | Unchanged (`current`) | Empty (`""`) | Pakistan (`PK`) | `http://insecure.net` | Accepted (`Your profile has been updated`) |
| SET-PW3 | Unique new (`{uid}`) | Special chars (`Hack&Learn #1`) | Empty (`""`) | Empty (`""`) | Accepted (`Your profile has been updated`) |
| SET-PW4 | Unchanged (`current`) | Long affiliation (50 chars) | United Kingdom (`GB`) | `https://uk-cyber.gov.uk` | Accepted (`Your profile has been updated`) |
