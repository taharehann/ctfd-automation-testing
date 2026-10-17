# Test Notes: Challenges Module (CTFd)

Module: Challenge page and flag submission (`/challenges`)
Techniques used: Equivalence Class Partitioning, Error Guessing, State Transition

## Challenge used for testing

- Name: Test Challenge, category Web, 100 points
- Flag: `flag{test123}` (static, case sensitive)
- No limit on attempts
- Every test registers a new user first, so the challenge is unsolved at the start.

## 1. Equivalence Class Partitioning (flag submission)

| ID  | Class                        | Valid/Invalid | Sample input          | Expected result |
| --- | ---------------------------- | ------------- | --------------------- | --------------- |
| FL1 | Exact correct flag           | Valid         | flag{test123}         | Correct         |
| FL2 | Completely wrong text        | Invalid       | wrong                 | Incorrect       |
| FL3 | Right text, wrong case       | Invalid       | FLAG{TEST123}         | Incorrect       |
| FL4 | Part of the flag (missing })  | Invalid       | flag{test123          | Incorrect       |
| FL5 | Flag with extra characters   | Invalid       | flag{test123}x        | Incorrect       |
| FL6 | Correct flag with spaces around it | Valid   | "  flag{test123}  "   | Correct (spaces are trimmed) |
| FL7 | Empty                        | Invalid       | (blank)               | Incorrect       |

## 2. Error Guessing

| ID  | Input                      | Why                                      | Expected result |
| --- | -------------------------- | ---------------------------------------- | --------------- |
| FL8 | `' OR 1=1 --`              | Check that SQL is not run                | Incorrect       |
| FL9 | 1000 characters of "a"     | Very long input should not break the page | Incorrect       |

## 3. State Transition

| ID  | Start state      | Action                  | End state | Expected result                           |
| --- | ---------------- | ----------------------- | --------- | ----------------------------------------- |
| ST1 | Unsolved         | Wrong flag, then correct flag | Solved | Incorrect, then Correct                   |
| ST2 | Solved           | Wrong flag              | Solved    | Incorrect but you already solved this     |
| ST3 | Solved           | Correct flag again      | Solved    | Message says already solved              |
