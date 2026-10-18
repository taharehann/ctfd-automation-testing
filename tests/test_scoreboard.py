import os
import time
import unittest
import uuid

from ddt import ddt, data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "http://localhost:4000"
CHALLENGE_URL = BASE_URL + "/challenges#Test%20Challenge-1"
CORRECT_FLAG = "flag{test123}"
CHALLENGE_VALUE = "100"

# Pause in seconds so the viewer can see what happens. Use 0 for fast runs:
#   PowerShell:  $env:STEP_DELAY=0
DELAY = float(os.environ.get("STEP_DELAY", "2"))


@ddt
class ScoreboardTests(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)
        # A new user for every test, who has not solved anything yet
        self.username = self.register_new_user()

    def tearDown(self):
        self.driver.quit()

    def register_new_user(self):
        driver = self.driver
        uid = uuid.uuid4().hex[:8]
        username = "score_" + uid
        driver.get(BASE_URL + "/register")
        driver.find_element(By.NAME, "name").send_keys(username)
        driver.find_element(By.NAME, "email").send_keys(username + "@test.com")
        driver.find_element(By.NAME, "password").send_keys("Score@123")
        driver.find_element(By.CSS_SELECTOR, "form [type='submit']").click()
        WebDriverWait(driver, 10).until(EC.url_contains("/challenges"))
        return username

    def solve_challenge(self):
        driver = self.driver
        driver.get(CHALLENGE_URL)
        driver.refresh()
        box = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder='Flag']"))
        )
        box.send_keys(CORRECT_FLAG)
        box.send_keys(Keys.ENTER)
        WebDriverWait(driver, 10).until(
            lambda d: "Correct" in d.find_element(By.TAG_NAME, "body").text
        )

    def open_scoreboard(self):
        self.driver.get(BASE_URL + "/scoreboard")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
        # wait until the column headers have their text (the page may still be drawing)
        WebDriverWait(self.driver, 10).until(
            lambda d: len(self.read_headers()) >= 3 and all(self.read_headers())
        )
        time.sleep(DELAY)

    def read_headers(self):
        return [th.text.strip().lower()
                for th in self.driver.find_elements(By.CSS_SELECTOR, "table thead th")]

    def read_rows(self):
        """Return the scoreboard as a list of (place, username, score)."""
        rows = []
        for tr in self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr"):
            cells = tr.find_elements(By.CSS_SELECTOR, "th, td")  # place is a th
            if len(cells) >= 3:
                rows.append((cells[0].text.strip(), cells[1].text.strip(), cells[-1].text.strip()))
        return rows

    # ---- page layout ----

    def test_scoreboard_page_opens(self):
        self.open_scoreboard()
        self.assertEqual("Scoreboard", self.driver.find_element(By.TAG_NAME, "h1").text.strip())

    @data("Place", "User", "Score")
    def test_table_has_column(self, column):
        self.open_scoreboard()
        headers = self.read_headers()
        self.assertIn(column.lower(), headers)

    # ---- score boundary: 0 points and 100 points ----

    def test_user_without_solves_is_not_listed(self):
        self.open_scoreboard()
        names = [row[1] for row in self.read_rows()]
        self.assertNotIn(self.username, names)

    def test_user_appears_after_solving(self):
        self.solve_challenge()
        self.open_scoreboard()
        rows = {name: score for place, name, score in self.read_rows()}
        self.assertTrue(rows, "no rows read from the scoreboard")
        self.assertIn(self.username, rows)
        self.assertEqual(CHALLENGE_VALUE, rows[self.username])

    # ---- ordering ----

    def test_scores_are_in_descending_order(self):
        self.solve_challenge()
        self.open_scoreboard()
        scores = [int(score) for place, name, score in self.read_rows()]
        self.assertTrue(scores, "no rows read from the scoreboard")
        self.assertEqual(sorted(scores, reverse=True), scores)

    def test_places_are_numbered_from_one(self):
        self.solve_challenge()
        self.open_scoreboard()
        places = [int(place) for place, name, score in self.read_rows()]
        self.assertTrue(places, "no rows read from the scoreboard")
        self.assertEqual(list(range(1, len(places) + 1)), places)

    # ---- navigation ----

    def test_username_link_opens_profile(self):
        self.solve_challenge()
        self.open_scoreboard()
        link = self.driver.find_element(By.LINK_TEXT, self.username)
        # the user is at the bottom of a long table, scroll to the link first
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
        time.sleep(1)
        link.click()
        WebDriverWait(self.driver, 10).until(EC.url_contains("/users/"))
        time.sleep(DELAY)
        self.assertIn(self.username, self.driver.find_element(By.TAG_NAME, "body").text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
