import csv
import os
import random
import string
import time
import unittest
import uuid

from ddt import ddt, data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "http://localhost:4000"

# Pause in seconds so the viewer can see what happens. Use 0 for fast runs:
#   PowerShell:  $env:STEP_DELAY=0
DELAY = float(os.environ.get("STEP_DELAY", "2"))

CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "register_data.csv")


def read_csv():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def real_value(text):
    """Replace the placeholders used in the CSV with real values."""
    text = text.replace("{uid}", uuid.uuid4().hex[:8])  # unique every run
    text = text.replace("{rc}", random.choice(string.ascii_letters + string.digits))
    text = text.replace("{a127}", "a" * 127)
    text = text.replace("{a128}", "a" * 128)
    text = text.replace("{a129}", "a" * 129)
    return text


@ddt
class RegisterTests(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)

    def tearDown(self):
        self.driver.quit()

    def type_into(self, field_name, text):
        self.driver.find_element(By.NAME, field_name).send_keys(text)
        time.sleep(1)

    @data(*read_csv())
    def test_register(self, row):
        driver = self.driver

        # 1. open the register page and fill the form
        driver.get(BASE_URL + "/register")
        self.type_into("name", real_value(row["username"]))
        self.type_into("email", real_value(row["email"]))
        self.type_into("password", real_value(row["password"]))
        time.sleep(DELAY)

        # 2. submit
        driver.find_element(By.CSS_SELECTOR, "form [type='submit']").click()

        # 3. check the result
        if row["result"] == "created":
            WebDriverWait(driver, 10).until(EC.url_contains("/challenges"))
            time.sleep(DELAY)
            self.assertIn("/challenges", driver.current_url, row["test_id"])
        else:
            # still on the register page
            expected_messages = [m for m in row["messages"].split("|") if m]
            if expected_messages:
                alerts = driver.find_elements(By.CSS_SELECTOR, ".alert-danger")
                shown_text = " ".join(a.text for a in alerts)
                time.sleep(DELAY)
                for message in expected_messages:
                    self.assertIn(message, shown_text, row["test_id"])
            else:
                time.sleep(max(DELAY, 1))  # browser blocked the form, give the page time to react
            self.assertIn("/register", driver.current_url, row["test_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
