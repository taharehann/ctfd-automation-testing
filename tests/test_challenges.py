import csv
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

# Pause in seconds so the viewer can see what happens. Use 0 for fast runs:
#   PowerShell:  $env:STEP_DELAY=0
DELAY = float(os.environ.get("STEP_DELAY", "2"))

CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "flag_data.csv")


def read_csv():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@ddt
class ChallengeTests(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)
        # A new user for every test, so the challenge is always unsolved at the start
        self.register_new_user()
        self.open_challenge()

    def tearDown(self):
        self.driver.quit()

    def register_new_user(self):
        driver = self.driver
        uid = uuid.uuid4().hex[:8]
        driver.get(BASE_URL + "/register")
        driver.find_element(By.NAME, "name").send_keys("chal_" + uid)
        driver.find_element(By.NAME, "email").send_keys("chal_" + uid + "@test.com")
        driver.find_element(By.NAME, "password").send_keys("Chal@123")
        driver.find_element(By.CSS_SELECTOR, "form [type='submit']").click()
        WebDriverWait(driver, 10).until(EC.url_contains("/challenges"))

    def open_challenge(self):
        driver = self.driver
        driver.get(CHALLENGE_URL)
        driver.refresh()  # makes sure the challenge window opens
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder='Flag']"))
        )
        time.sleep(1)

    def submit_flag(self, flag):
        box = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Flag']")
        box.clear()
        box.send_keys(flag)
        time.sleep(DELAY)
        box.send_keys(Keys.ENTER)

    def page_text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text

    def wait_for_text(self, text):
        WebDriverWait(self.driver, 10).until(lambda d: text in self.page_text())
        time.sleep(DELAY)

    # ---- data driven tests (one test per CSV row) ----

    @data(*read_csv())
    def test_submit_flag(self, row):
        flag = row["flag"].replace("{a1000}", "a" * 1000)
        self.submit_flag(flag)

        self.wait_for_text(row["message"])
        self.assertIn(row["message"], self.page_text(), row["test_id"])

    # ---- state transition tests ----

    def test_wrong_then_correct(self):
        self.submit_flag("wrong")
        self.wait_for_text("Incorrect")
        self.submit_flag(CORRECT_FLAG)
        self.wait_for_text("Correct")

    def test_solved_then_wrong(self):
        self.submit_flag(CORRECT_FLAG)
        self.wait_for_text("Correct")
        self.submit_flag("wrong")
        self.wait_for_text("already solved")
        self.assertIn("Incorrect but you already solved this", self.page_text())

    def test_solved_then_correct_again(self):
        self.submit_flag(CORRECT_FLAG)
        self.wait_for_text("Correct")
        self.submit_flag(CORRECT_FLAG)
        self.wait_for_text("already solved")


if __name__ == "__main__":
    unittest.main(verbosity=2)
