# CTFd Selenium Test Automation

Automated Selenium tests for [CTFd](https://github.com/CTFd/CTFd), an open-source CTF platform written in Python (Flask). Built for SQE Assignment 3.

## Setup video

- `docs/Setup_video.mp4` shows cloning, installing and starting CTFd.
- `docs/Setup_video_Part2.mp4` shows the setup page and the first login.

## Modules tested

| Module | Test files | Test data |
|---|---|---|
| Authentication (register, login, logout) | `tests/test_auth_register.py`, `tests/test_auth_login.py` | `data/register_data.csv`, `data/login_data.csv` |
| Challenges (flag submission) | `tests/test_challenges.py` | `data/flag_data.csv` |
| Scoreboard | `tests/test_scoreboard.py` | none (users are created by the tests) |

The test design notes (ECP, BVA, decision table and so on) for each module are in the `notes/` folder.

## Setup

You need Python 3.9 or newer, Git and Google Chrome.

1. Clone and start CTFd (in its own folder, next to this repo):
   ```
   git clone https://github.com/CTFd/CTFd.git
   cd CTFd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python serve.py
   ```
   CTFd runs at http://localhost:4000. Leave this window open.

2. Open http://localhost:4000 and finish the setup page once:
   - Event name: `TestCTF`
   - Mode: Users
   - Create an admin account (`admin` / `admin@test.com`)
   - Do not turn on email verification

3. Log in as admin and create one challenge (Admin Panel, Challenges, plus button):
   - Name `Test Challenge`, category `Web`, message anything, value `100`, type `standard`
   - Flag: `flag{test123}`, static, case sensitive
   - State: Visible, no limit on attempts

4. In a second terminal, in this repo:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the tests

CTFd must be running while the tests run.

```
# run everything, one test at a time
python run_tests.py

# smoke + auth only
python run_tests.py --suite quick

# one group
python run_tests.py --group challenges

# run the tests of each group in parallel
python run_tests.py --workers 3

# pause in each test so it can be watched
python run_tests.py --delay 2

# show the groups and tests in run order
python run_tests.py --list
```

A single file can also be run on its own, for example `python tests\test_scoreboard.py`.

## Groups, suites and order

All of this is set in `test_config.py`.

- **Groups:** `smoke`, `auth`, `challenges`, `scoreboard`. They run in the order they are written in the file.
- **Suites:** `quick` (smoke, auth) and `full` (all groups).
- **Test order inside a class** comes from `METHOD_ORDER` in the same file.
- **Parallel runs:** with `--workers N`, the tests of one group run at the same time, each with its own browser. Groups still run one after another. Every test creates its own user, so the tests do not depend on each other. Because CTFd uses SQLite, 2 or 3 workers is a safe number.
- **Data driven tests:** the register, login and flag tests read their inputs from the CSV files in `data/` (using `ddt`), and each row runs as its own test.

## Notes

- `login_user` is created by the login tests on the first run. If it already exists, CTFd shows an error and the tests carry on.
- The tests assume the admin account and the Test Challenge above. If you use different values, change them in the CSV files and test files.
