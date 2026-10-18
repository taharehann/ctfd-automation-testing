# Test Notes: Scoreboard Module (CTFd)

Module: Scoreboard page (`/scoreboard`)
Techniques used: Equivalence Class Partitioning, Boundary Value Analysis, Use Case Testing

## What the page shows

A chart of the top 10 users and a table with the columns Place, User and Score. Only users who have scored points are listed. The scoreboard changes every time a user solves a challenge, so the tests only check things that stay true between runs and do not depend on exact positions.

The challenge used is "Test Challenge" worth 100 points.

## 1. Equivalence Class Partitioning

| ID  | Class                              | Sample                     | Expected result                              |
| --- | ---------------------------------- | -------------------------- | -------------------------------------------- |
| SB1 | Page opened by a logged in user    | Open /scoreboard           | Page heading is "Scoreboard"                 |
| SB2 | Table columns                      | Place, User, Score         | All three columns are in the table header    |
| SB3 | User with no solves                | Newly registered user      | User is not in the table                     |
| SB4 | User with a solve                  | User who solved the 100 point challenge | User is in the table with 100 points |

## 2. Boundary Value Analysis (score)

| ID  | Boundary                     | Input                          | Expected result                  |
| --- | ---------------------------- | ------------------------------ | -------------------------------- |
| SB3 | Lowest score (0 points)      | User with no solves            | Not listed                       |
| SB4 | Just above lowest (100 points, one solve) | User with one solve | Listed with 100 points           |

## 3. Use Case Testing

| ID  | Use case                                  | Steps                                                             | Expected result                                 |
| --- | ----------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------- |
| SB5 | Solve a challenge, then check the ranking | Register, solve Test Challenge, open scoreboard                   | User is listed with 100 points                  |
| SB6 | Scores are ordered                        | Open scoreboard with several users                                | Scores go from highest to lowest                |
| SB7 | Places are numbered                       | Open scoreboard with several users                                | Places are 1, 2, 3, ... with no gaps            |
| SB8 | Open a user from the scoreboard           | Click a username in the table                                     | The user's profile page opens (URL has /users/) |
