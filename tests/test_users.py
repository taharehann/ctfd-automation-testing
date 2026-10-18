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
from selenium.webdriver.support.ui import WebDriverWait, Select

BASE_URL = "http://localhost:4000"
DELAY = float(os.environ.get("STEP_DELAY", "2"))
CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "users_data.csv")


def read_csv():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_click(driver, element):
    """Scroll element into center view and click it cleanly."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.3)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


@ddt
class UsersTests(unittest.TestCase):

    def setUp(self):
        opts = webdriver.ChromeOptions()
        opts.add_argument("--force-device-scale-factor=1")
        opts.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=opts)
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)
        self.username = self.register_new_user()

    def tearDown(self):
        self.driver.quit()

    def register_new_user(self):
        d = self.driver
        username = "usr_" + uuid.uuid4().hex[:8]
        d.get(BASE_URL + "/register")
        d.find_element(By.NAME, "name").send_keys(username)
        d.find_element(By.NAME, "email").send_keys(username + "@test.com")
        d.find_element(By.NAME, "password").send_keys("Pass@123")
        submit_btn = d.find_element(By.CSS_SELECTOR, "form [type='submit']")
        safe_click(d, submit_btn)
        WebDriverWait(d, 10).until(EC.url_contains("/challenges"))
        return username

    def page_text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text

    def get_user_profile_url(self, username):
        d = self.driver
        d.get(f"{BASE_URL}/users?field=name&q={username}")
        WebDriverWait(d, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table tbody tr"))
        )
        row = d.find_element(By.CSS_SELECTOR, "table.table tbody tr")
        link = row.find_element(By.TAG_NAME, "a")
        return link.get_attribute("href")

    # ---- Structural & Scenario Tests ----

    def test_users_directory_page_structure(self):
        """Verify the Users directory page renders table headers and search inputs properly."""
        d = self.driver
        d.get(BASE_URL + "/users")
        time.sleep(DELAY)

        self.assertIn("TestCTF", d.title)
        heading = d.find_element(By.CSS_SELECTOR, "h1").text
        self.assertIn("Users", heading)

        # Verify search form elements
        field_select = d.find_element(By.NAME, "field")
        q_input = d.find_element(By.NAME, "q")
        self.assertTrue(field_select.is_displayed())
        self.assertTrue(q_input.is_displayed())

        # Verify table headers
        headers = [th.text.strip() for th in d.find_elements(By.CSS_SELECTOR, "table.table thead th")]
        self.assertIn("User", headers)
        self.assertIn("Website", headers)
        self.assertIn("Affiliation", headers)
        self.assertIn("Country", headers)

    def test_directory_to_profile_navigation(self):
        """USR-UC1: Navigate from the users directory to the user's public profile page."""
        d = self.driver
        d.get(f"{BASE_URL}/users?field=name&q={self.username}")
        time.sleep(DELAY)

        user_link = d.find_element(By.CSS_SELECTOR, "table.table tbody tr td a")
        self.assertEqual(user_link.text.strip(), self.username)
        safe_click(d, user_link)

        WebDriverWait(d, 10).until(EC.url_contains("/users/"))
        time.sleep(DELAY)

        profile_h1 = d.find_element(By.CSS_SELECTOR, "h1").text.strip()
        self.assertEqual(profile_h1, self.username)

    def test_user_profile_solve_reflection(self):
        """USR-UC2 & USR-BVA2: Solving a challenge immediately updates points and Solves table on profile."""
        d = self.driver
        profile_url = self.get_user_profile_url(self.username)

        # Before solve: no Solves heading or table
        d.get(profile_url)
        time.sleep(DELAY)
        self.assertNotIn("Solves", self.page_text())

        # Solve challenge
        d.get(BASE_URL + "/challenges#Test%20Challenge-1")
        d.refresh()
        WebDriverWait(d, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder='Flag']"))
        )
        flag_box = d.find_element(By.CSS_SELECTOR, "input[placeholder='Flag']")
        flag_box.clear()
        flag_box.send_keys("flag{test123}")
        time.sleep(DELAY)
        flag_box.send_keys(Keys.ENTER)
        WebDriverWait(d, 10).until(lambda drv: "Correct" in drv.find_element(By.TAG_NAME, "body").text)
        time.sleep(DELAY)

        # After solve: profile displays score and Solves table
        d.get(profile_url)
        time.sleep(DELAY)
        body = self.page_text()
        self.assertIn("100 points", body)
        self.assertIn("Solves", body)
        self.assertIn("Test Challenge", body)
        self.assertIn("Web", body)

    def test_user_profile_metadata_display(self):
        """Verify affiliation, country, and website from settings render on public profile."""
        d = self.driver
        d.get(BASE_URL + "/settings")
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.NAME, "affiliation")))

        aff_input = d.find_element(By.NAME, "affiliation")
        aff_input.clear()
        aff_input.send_keys("Security Lab")

        country_select = Select(d.find_element(By.NAME, "country"))
        country_select.select_by_value("US")

        web_input = d.find_element(By.NAME, "website")
        web_input.clear()
        web_input.send_keys("https://ctfd.io")

        submit_btn = d.find_element(By.CSS_SELECTOR, "#profile form [type='submit']")
        safe_click(d, submit_btn)
        WebDriverWait(d, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#results .alert-success"))
        )
        time.sleep(DELAY)

        # Inspect public profile
        profile_url = self.get_user_profile_url(self.username)
        d.get(profile_url)
        time.sleep(DELAY)

        body = self.page_text()
        self.assertIn("Security Lab", body)
        self.assertIn("United States", body)
        web_link = d.find_element(By.CSS_SELECTOR, "a[href='https://ctfd.io']")
        self.assertTrue(web_link.is_displayed())

    # ---- Data-Driven Tests from CSV ----

    @data(*read_csv())
    def test_users_data_driven(self, row):
        """Execute parameterized tests for ECP, BVA, and Error Guessing from users_data.csv."""
        d = self.driver
        test_id = row["test_id"]
        category = row["category"]
        expected = row["expected_result"]

        if category == "directory":
            d.get(BASE_URL + "/users")
            time.sleep(DELAY)
            rows = d.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
            self.assertGreater(len(rows), 0, f"{test_id}: Users table should contain registered users")

        elif category == "profile":
            user_id = row["user_id_param"]
            d.get(f"{BASE_URL}/users/{user_id}")
            time.sleep(DELAY)
            body = self.page_text()
            self.assertTrue(
                "404 Not Found" in body or "File not found" in body,
                f"{test_id}: Expected 404 error page for user ID {user_id}"
            )

        elif category == "search":
            field = row["field"]
            raw_query = row["query"]
            query = self.username if raw_query == "{user_name}" else raw_query

            d.get(f"{BASE_URL}/users?field={field}&q={query}")
            time.sleep(DELAY)

            if expected == "match_found":
                rows = d.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
                self.assertGreater(len(rows), 0, f"{test_id}: Search should return matching user")
                self.assertIn(query, rows[0].text)
            elif expected == "no_results":
                rows = d.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
                # When no results match, either tbody has 0 rows or rows don't contain query
                matching_rows = [r for r in rows if query in r.text]
                self.assertEqual(len(matching_rows), 0, f"{test_id}: Search should yield 0 results for {query}")

        elif category == "zero_score":
            # USR-BVA1: Check that a user with 0 points appears in the Users directory
            d.get(f"{BASE_URL}/users?field=name&q={self.username}")
            time.sleep(DELAY)
            rows = d.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
            self.assertGreater(len(rows), 0, f"{test_id}: 0-point user must be listed in /users directory")
            self.assertIn(self.username, rows[0].text)

        elif category == "pagination":
            page = row["page"]
            d.get(f"{BASE_URL}/users?page={page}")
            time.sleep(DELAY)

            if expected == "page_loaded":
                rows = d.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
                self.assertGreater(len(rows), 0, f"{test_id}: Page 1 should contain user rows")
            elif expected == "empty_page":
                rows = d.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
                self.assertEqual(len(rows), 0, f"{test_id}: Out of bounds page should have 0 rows")


if __name__ == "__main__":
    unittest.main()
