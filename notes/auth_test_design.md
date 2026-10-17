# Test Notes: Authentication Module (CTFd)

Module: Registration and Login (`/register`, `/login`)
Techniques used: Equivalence Class Partitioning, Boundary Value Analysis, Decision Table, Error Guessing

## What the register form accepts

I tried the form and read through `auth.py` to find the rules:

- Username: cannot be empty (spaces are trimmed first), must be unique, and cannot look like an email address.
- Email: must be a valid email format and must not be used already. It is converted to lowercase.
- Password: cannot be empty (spaces are trimmed first) and cannot be longer than 128 characters. There is no minimum length by default.

## 1. Equivalence Class Partitioning

| ID | Field | Class | Valid/Invalid | Sample input | Expected result |
|---|---|---|---|---|---|
| EC1 | Username | Unique, not empty, not an email | Valid | user_ok1 | Account created |
| EC2 | Username | Empty or only spaces | Invalid | (blank), "   " | Pick a longer user name |
| EC3 | Username | Already taken | Invalid | admin | That user name is already taken |
| EC4 | Username | In email format | Invalid | a@b.com | Your user name cannot be an email address |
| EC5 | Email | Valid format, not used | Valid | ok1@test.com | Account created |
| EC6 | Email | Wrong format | Invalid | abc, abc@, @test.com | Please enter a valid email address |
| EC7 | Email | Already used | Invalid | admin@test.com | That email has already been used |
| EC8 | Password | 1 to 128 characters | Valid | Pass@123 | Account created |
| EC9 | Password | Empty or only spaces | Invalid | (blank), "   " | Pick a longer password |
| EC10 | Password | More than 128 characters | Invalid | 129 x "a" | Pick a shorter password |

## 2. Boundary Value Analysis

| ID | Field | Boundary | Input | Expected result |
|---|---|---|---|---|
| BVA1 | Username | Below minimum (0 chars) | (blank) | Pick a longer user name |
| BVA2 | Username | Minimum (1 char) | a | Account created |
| BVA3 | Username | Just above minimum (2 chars) | ab | Account created |
| BVA4 | Password | Below minimum (0 chars) | (blank) | Pick a longer password |
| BVA5 | Password | Minimum (1 char) | a | Account created |
| BVA6 | Password | Just below maximum (127 chars) | 127 x "a" | Account created |
| BVA7 | Password | Maximum (128 chars) | 128 x "a" | Account created |
| BVA8 | Password | Just above maximum (129 chars) | 129 x "a" | Pick a shorter password |

## 3. Decision Table (Registration)

| Rule | Username valid | Email valid | Password valid | Expected result |
|---|---|---|---|---|
| R1 | Yes | Yes | Yes | Account created, user lands on Challenges page |
| R2 | No | Yes | Yes | Username error |
| R3 | Yes | No | Yes | Email error |
| R4 | Yes | Yes | No | Password error |
| R5 | No | No | Yes | Username and email errors |
| R6 | No | Yes | No | Username and password errors |
| R7 | Yes | No | No | Email and password errors |
| R8 | No | No | No | All three errors |

## 4. Login

| ID | Username/Email | Password | Expected result |
|---|---|---|---|
| L1 | Valid username | Correct | Logged in, Challenges page opens |
| L2 | Valid email | Correct | Logged in, Challenges page opens |
| L3 | Valid username | Wrong | Your username or password is incorrect |
| L4 | Unknown username | Any | Your username or password is incorrect |
| L5 | (blank) | (blank) | Not logged in, form shows a required field message |
| L6 | Logged in user clicks Logout | n/a | Back on home page, Login link is visible |

## 5. Error Guessing

| ID | Input | Why |
|---|---|---|
| EG1 | Username "  user  " with spaces around it | The app trims spaces |
| EG2 | Email OK@TEST.COM when ok@test.com exists | The app lowercases emails, so it should count as a duplicate |
| EG3 | Username `<script>alert(1)</script>` | Check that scripts are not run |
| EG4 | Username `' OR 1=1 --` | Check that SQL is not run |
