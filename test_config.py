"""Configuration for the test runner: groups, suites and execution order."""

# GROUPS: each group is a list of test classes.
# The groups run in the order they are written here.
GROUPS = {
    "smoke": ["tests.test_smoke.SmokeTest"],
    "auth": [
        "tests.test_auth_register.RegisterTests",
        "tests.test_auth_login.LoginTests",
    ],
    "challenges": ["tests.test_challenges.ChallengeTests"],
    "scoreboard": ["tests.test_scoreboard.ScoreboardTests"],
}

# SUITES: named sets of groups that can be run with --suite
SUITES = {
    "quick": ["smoke", "auth"],
    "full": ["smoke", "auth", "challenges", "scoreboard"],
}

# METHOD_ORDER: the order of the test cases inside a class.
# A test runs earlier if its name starts with an earlier entry.
# Tests that are not listed run last, in alphabetical order.
METHOD_ORDER = {
    "LoginTests": [
        "test_login",
        "test_logout",
    ],
    "ChallengeTests": [
        "test_submit_flag",
        "test_wrong_then_correct",
        "test_solved_then_wrong",
        "test_solved_then_correct_again",
    ],
    "ScoreboardTests": [
        "test_scoreboard_page_opens",
        "test_table_has_column",
        "test_user_without_solves",
        "test_user_appears_after_solving",
        "test_scores_are_in_descending_order",
        "test_places_are_numbered_from_one",
        "test_username_link_opens_profile",
    ],
}
