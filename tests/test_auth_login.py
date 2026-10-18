import csv
import os
import time
import unittest

from ddt import ddt, data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "http://localhost:4000"

# Pause in seconds so the viewer can see what happens. Use 0 for fast runs:
#   PowerShell:  $env:STEP_DELAY=0
DELAY = float(os.environ.get("STEP_DELAY", "2"))

CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "login_data.csv")

# The account used by the login tests
TEST_USER = "login_user"
TEST_EMAIL = "login_user@test.com"
TEST_PASSWORD = "Login@123"


def read_csv():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@ddt
class LoginTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create the account once. If it already exists (from an earlier run),
        # CTFd just shows an error and the tests can still use the account.
        driver = webdriver.Chrome()
        driver.get(BASE_URL + "/register")
        driver.find_element(By.NAME, "name").send_keys(TEST_USER)
        driver.find_element(By.NAME, "email").send_keys(TEST_EMAIL)
        driver.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "form [type='submit']").click()
        time.sleep(2)
        driver.quit()

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)

    def tearDown(self):
        self.driver.quit()

    def login(self, username, password):
        driver = self.driver
        driver.get(BASE_URL + "/login")
        driver.find_element(By.NAME, "name").send_keys(username)
        time.sleep(1)
        driver.find_element(By.NAME, "password").send_keys(password)
        time.sleep(DELAY)
        driver.find_element(By.CSS_SELECTOR, "form [type='submit']").click()

    @data(*read_csv())
    def test_login(self, row):
        driver = self.driver

        self.login(row["username"], row["password"])

        if row["result"] == "logged_in":
            WebDriverWait(driver, 10).until(EC.url_contains("/challenges"))
            time.sleep(DELAY)
            self.assertIn("/challenges", driver.current_url, row["test_id"])
        else:
            # still on the login page
            if row["message"]:
                alert = driver.find_element(By.CSS_SELECTOR, ".alert-danger")
                time.sleep(DELAY)
                self.assertIn(row["message"], alert.text, row["test_id"])
            else:
                time.sleep(max(DELAY, 1))  # browser blocked the form, give the page time to react
            self.assertIn("/login", driver.current_url, row["test_id"])

    def test_logout(self):
        driver = self.driver

        self.login(TEST_USER, TEST_PASSWORD)
        WebDriverWait(driver, 10).until(EC.url_contains("/challenges"))

        driver.get(BASE_URL + "/logout")
        time.sleep(DELAY)

        # after logout the Login link is shown again
        login_link = driver.find_element(By.CSS_SELECTOR, "a[href='/login']")
        self.assertTrue(login_link.is_displayed())


if __name__ == "__main__":
    unittest.main(verbosity=2)
