import csv
import os
import time
import unittest
import uuid

from ddt import ddt, data
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

BASE_URL = "http://localhost:4000"
DELAY = float(os.environ.get("STEP_DELAY", "2"))
CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "settings_data.csv")


def read_csv():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def real_value(text):
    if not text:
        return ""
    text = text.replace("{uid}", uuid.uuid4().hex[:8])
    return text


def safe_click(driver, element):
    """Scroll element into center view and click it cleanly."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.3)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


@ddt
class SettingsTests(unittest.TestCase):

    def setUp(self):
        opts = webdriver.ChromeOptions()
        # Force standard device scaling so elements stay fully visible in viewport
        opts.add_argument("--force-device-scale-factor=1")
        opts.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=opts)
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)
        # Register fresh user for every test
        self.username = self.register_new_user()
        self.password = "Pass@123"

    def tearDown(self):
        self.driver.quit()

    def register_new_user(self):
        d = self.driver
        username = "set_" + uuid.uuid4().hex[:8]
        d.get(BASE_URL + "/register")
        d.find_element(By.NAME, "name").send_keys(username)
        d.find_element(By.NAME, "email").send_keys(username + "@test.com")
        d.find_element(By.NAME, "password").send_keys("Pass@123")
        submit_btn = d.find_element(By.CSS_SELECTOR, "form [type='submit']")
        safe_click(d, submit_btn)
        WebDriverWait(d, 10).until(EC.url_contains("/challenges"))
        return username

    def open_settings(self):
        d = self.driver
        d.get(BASE_URL + "/settings")
        WebDriverWait(d, 10).until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        time.sleep(DELAY)

    def test_settings_page_opens(self):
        """Verify the Settings page loads properly for a logged-in user."""
        self.open_settings()
        d = self.driver
        self.assertIn("TestCTF", d.title)
        heading = d.find_element(By.CSS_SELECTOR, "h1").text
        self.assertIn("Settings", heading)
        # Verify current username is pre-populated
        name_val = d.find_element(By.NAME, "name").get_attribute("value")
        self.assertEqual(name_val, self.username)

    def test_profile_persistence_on_reload(self):
        """Verify affiliation and country values persist across page reloads."""
        self.open_settings()
        d = self.driver
        aff_input = d.find_element(By.NAME, "affiliation")
        aff_input.clear()
        aff_input.send_keys("Independent Security Researchers")

        country_select = Select(d.find_element(By.NAME, "country"))
        country_select.select_by_value("US")

        submit_btn = d.find_element(By.CSS_SELECTOR, "#profile form [type='submit']")
        safe_click(d, submit_btn)

        WebDriverWait(d, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#results .alert-success"))
        )
        time.sleep(DELAY)

        # Reload page and verify saved values remain
        d.refresh()
        WebDriverWait(d, 10).until(
            EC.presence_of_element_located((By.NAME, "affiliation"))
        )
        time.sleep(DELAY)
        new_aff = d.find_element(By.NAME, "affiliation").get_attribute("value")
        new_country = d.find_element(By.NAME, "country").get_attribute("value")
        self.assertEqual(new_aff, "Independent Security Researchers")
        self.assertEqual(new_country, "US")

    @data(*read_csv())
    def test_settings_data_cases(self, row):
        """Execute CSV-driven test cases covering ECP, BVA, Syntax, and Pairwise testing."""
        self.open_settings()
        d = self.driver

        if row["name"]:
            name_field = d.find_element(By.NAME, "name")
            name_field.clear()
            name_field.send_keys(real_value(row["name"]))

        if row["email"]:
            email_field = d.find_element(By.NAME, "email")
            email_field.clear()
            email_field.send_keys(real_value(row["email"]))

        if row["confirm"]:
            confirm_field = d.find_element(By.NAME, "confirm")
            confirm_field.clear()
            confirm_field.send_keys(row["confirm"])

        if row["password"]:
            pass_field = d.find_element(By.NAME, "password")
            pass_field.clear()
            pass_field.send_keys(row["password"])

        if row["affiliation"]:
            aff_field = d.find_element(By.NAME, "affiliation")
            aff_field.clear()
            aff_field.send_keys(row["affiliation"])

        if row["website"]:
            web_field = d.find_element(By.NAME, "website")
            web_field.clear()
            web_field.send_keys(row["website"])

        if row["country"]:
            country_select = Select(d.find_element(By.NAME, "country"))
            country_select.select_by_value(row["country"])

        time.sleep(DELAY)

        submit_btn = d.find_element(By.CSS_SELECTOR, "#profile form [type='submit']")
        safe_click(d, submit_btn)

        # Check if browser blocked client-side form validation (e.g. invalid URL)
        form_valid = d.execute_script("return arguments[0].checkValidity();", d.find_element(By.CSS_SELECTOR, "#profile form"))
        if not form_valid:
            self.assertEqual(row["result"], "rejected", row["test_id"])
            return

        if row["result"] == "success":
            WebDriverWait(d, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#results .alert-success"))
            )
            time.sleep(DELAY)
            alert_text = d.find_element(By.CSS_SELECTOR, "#results .alert-success").text
            self.assertIn(row["messages"], alert_text, row["test_id"])
        else:
            WebDriverWait(d, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#results .alert-danger"))
            )
            time.sleep(DELAY)
            alerts = d.find_elements(By.CSS_SELECTOR, "#results .alert-danger")
            all_text = " ".join(a.text for a in alerts)
            self.assertIn(row["messages"], all_text, row["test_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
