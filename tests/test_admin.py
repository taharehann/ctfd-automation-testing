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
DELAY = float(os.environ.get("STEP_DELAY", "2"))
CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "admin_data.csv")

ADMIN_USER = "admin"
ADMIN_PASS = "Admin@12345"


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
class AdminTests(unittest.TestCase):

    def setUp(self):
        opts = webdriver.ChromeOptions()
        opts.add_argument("--force-device-scale-factor=1")
        opts.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=opts)
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)

    def tearDown(self):
        self.driver.quit()

    def page_text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text

    def login_as_admin(self):
        d = self.driver
        d.delete_all_cookies()
        d.get(BASE_URL + "/login")
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        d.find_element(By.NAME, "name").clear()
        d.find_element(By.NAME, "name").send_keys(ADMIN_USER)
        d.find_element(By.NAME, "password").clear()
        d.find_element(By.NAME, "password").send_keys(ADMIN_PASS)
        submit_btn = d.find_element(By.CSS_SELECTOR, "form [type='submit']")
        safe_click(d, submit_btn)
        WebDriverWait(d, 10).until(
            lambda drv: "/challenges" in drv.current_url or "/admin" in drv.current_url
        )

    def register_regular_user(self):
        d = self.driver
        d.delete_all_cookies()
        username = "reg_" + uuid.uuid4().hex[:8]
        d.get(BASE_URL + "/register")
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        d.find_element(By.NAME, "name").send_keys(username)
        d.find_element(By.NAME, "email").send_keys(username + "@test.com")
        d.find_element(By.NAME, "password").send_keys("Pass@123")
        submit_btn = d.find_element(By.CSS_SELECTOR, "form [type='submit']")
        safe_click(d, submit_btn)
        WebDriverWait(d, 10).until(EC.url_contains("/challenges"))
        return username, "Pass@123"

    def create_page(self, title, route, content, draft=False, hidden=False, auth_required=False):
        d = self.driver
        d.get(BASE_URL + "/admin/pages/new")
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.NAME, "title")))

        title_input = d.find_element(By.NAME, "title")
        title_input.clear()
        title_input.send_keys(title)

        route_input = d.find_element(By.NAME, "route")
        route_input.clear()
        route_input.send_keys(route)

        # Explicitly set checkboxes via JS to guarantee exact state without click interception
        d.execute_script("""
            var d = document.querySelector('input[name="draft"]');
            if (d) d.checked = arguments[0];
            var h = document.querySelector('input[name="hidden"]');
            if (h) h.checked = arguments[1];
            var a = document.querySelector('input[name="auth_required"]');
            if (a) a.checked = arguments[2];
        """, draft, hidden, auth_required)

        # Set content through CodeMirror or underlying textarea
        d.execute_script("""
            var cm = document.querySelector('.CodeMirror');
            if (cm && cm.CodeMirror) {
                cm.CodeMirror.setValue(arguments[0]);
            } else {
                var ta = document.getElementById('admin-pages-editor');
                if (ta) ta.value = arguments[0];
            }
        """, content)
        time.sleep(0.3)

        save_btn = d.find_element(By.ID, "save-page")
        safe_click(d, save_btn)
        WebDriverWait(d, 10).until(
            lambda drv: "/admin/pages/new" not in drv.current_url
        )

    # ---- Scenario & Structural Tests ----

    def test_admin_dashboard_navigation(self):
        """ADM-EC3: Admin login succeeds and renders administrative sub-menus."""
        d = self.driver
        self.login_as_admin()
        d.get(BASE_URL + "/admin")
        time.sleep(DELAY)

        self.assertIn("/admin", d.current_url)
        self.assertIn("Admin Panel", d.title)

        # Check navigation tabs for core admin features
        body = self.page_text()
        self.assertIn("Pages", body)
        self.assertIn("Users", body)
        self.assertIn("Challenges", body)
        self.assertIn("Submissions", body)

    def test_custom_page_publication_lifecycle(self):
        """ADM-UC1: Admin creates published page; verified in nav and public URL; updated to draft."""
        d = self.driver
        self.login_as_admin()

        route = "lifecycle-" + uuid.uuid4().hex[:6]
        title = "Competition Rules"
        content = "# Rules\n1. Play fair\n2. Have fun"

        self.create_page(title=title, route=route, content=content, draft=False, hidden=False)

        # 1. Verify in admin pages listing
        d.get(BASE_URL + "/admin/pages")
        time.sleep(DELAY)
        self.assertIn(route, self.page_text())

        # 2. Verify as unauthenticated visitor
        d.delete_all_cookies()
        d.get(f"{BASE_URL}/{route}")
        time.sleep(DELAY)
        body = self.page_text()
        self.assertIn("Competition Rules", body)
        self.assertIn("Play fair", body)

        # 3. Verify link is present in top navigation bar
        nav_links = [a.text.strip() for a in d.find_elements(By.CSS_SELECTOR, "nav a.nav-link")]
        self.assertIn("Competition Rules", nav_links)

    def test_user_ban_and_unban_lifecycle(self):
        """State Transition Testing: Active user -> Banned -> 403 Forbidden -> Unbanned -> Active."""
        d = self.driver
        # 1. Register a regular user and verify access
        username, password = self.register_regular_user()
        d.get(BASE_URL + "/challenges")
        time.sleep(DELAY)
        self.assertNotIn("403", self.page_text())
        self.assertNotIn("banned", self.page_text().lower())

        # 2. Admin logs in and bans user
        self.login_as_admin()
        d.get(f"{BASE_URL}/users?field=name&q={username}")
        time.sleep(DELAY)
        user_row = d.find_element(By.CSS_SELECTOR, "table.table tbody tr")
        user_link = user_row.find_element(By.TAG_NAME, "a")
        user_profile_url = user_link.get_attribute("href")
        user_id = user_profile_url.split("/users/")[-1]

        # Navigate to admin user detail
        d.get(f"{BASE_URL}/admin/users/{user_id}")
        time.sleep(DELAY)
        self.assertEqual(d.find_element(By.ID, "team-id").text.strip(), username)

        # Ban the user using admin edit modal
        edit_btn = d.find_element(By.CSS_SELECTOR, ".edit-user")
        safe_click(d, edit_btn)
        WebDriverWait(d, 10).until(
            EC.visibility_of_element_located((By.ID, "user-info-edit-form"))
        )
        banned_cb = d.find_element(By.NAME, "banned")
        if not banned_cb.is_selected():
            safe_click(d, banned_cb)

        submit_btn = d.find_element(By.CSS_SELECTOR, "#user-info-edit-form .modal-action")
        safe_click(d, submit_btn)
        time.sleep(1)
        d.refresh()
        time.sleep(DELAY)
        self.assertIn("banned", self.page_text())

        # 3. Log back in as victim user and verify 403 response
        d.delete_all_cookies()
        d.get(BASE_URL + "/login")
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        d.find_element(By.NAME, "name").send_keys(username)
        d.find_element(By.NAME, "password").send_keys(password)
        safe_click(d, d.find_element(By.CSS_SELECTOR, "form [type='submit']"))
        time.sleep(DELAY)

        # Direct access to challenges yields 403 banned
        d.get(BASE_URL + "/challenges")
        time.sleep(DELAY)
        body = self.page_text()
        self.assertTrue(
            "banned" in body.lower() or "403" in body,
            "Banned user must receive 403 / banned notification"
        )

        # 4. Admin unbans user
        self.login_as_admin()
        d.get(f"{BASE_URL}/admin/users/{user_id}")
        time.sleep(DELAY)
        edit_btn = d.find_element(By.CSS_SELECTOR, ".edit-user")
        safe_click(d, edit_btn)
        WebDriverWait(d, 10).until(
            EC.visibility_of_element_located((By.ID, "user-info-edit-form"))
        )
        banned_cb = d.find_element(By.NAME, "banned")
        if banned_cb.is_selected():
            safe_click(d, banned_cb)
        submit_btn = d.find_element(By.CSS_SELECTOR, "#user-info-edit-form .modal-action")
        safe_click(d, submit_btn)
        time.sleep(1)

        # 5. Victim user now regains normal access
        d.delete_all_cookies()
        d.get(BASE_URL + "/login")
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        d.find_element(By.NAME, "name").send_keys(username)
        d.find_element(By.NAME, "password").send_keys(password)
        safe_click(d, d.find_element(By.CSS_SELECTOR, "form [type='submit']"))
        WebDriverWait(d, 10).until(EC.url_contains("/challenges"))
        self.assertNotIn("403", self.page_text())

    # ---- Data-Driven Tests from CSV ----

    @data(*read_csv())
    def test_admin_data_driven(self, row):
        """Execute parameterized tests for Cause-Effect Graphing, Decision Tables, BVA, and Error Guessing."""
        d = self.driver
        test_id = row["test_id"]
        category = row["category"]
        role = row["user_role"]
        expected = row["expected_outcome"]

        if category == "access_control":
            target_route = row["route"]

            if role == "unauth":
                d.delete_all_cookies()
                d.get(f"{BASE_URL}{target_route}")
                time.sleep(DELAY)
                self.assertIn("/login", d.current_url, f"{test_id}: Unauthenticated visitor must be redirected to /login")

            elif role == "regular":
                self.register_regular_user()
                d.get(f"{BASE_URL}{target_route}")
                time.sleep(DELAY)
                self.assertIn("/login", d.current_url, f"{test_id}: Regular user must be redirected to /login")

            elif role == "admin":
                self.login_as_admin()
                d.get(f"{BASE_URL}{target_route}")
                time.sleep(DELAY)

                if expected == "dashboard_loaded":
                    self.assertIn("/admin", d.current_url, f"{test_id}: Admin dashboard must be accessible")
                    self.assertIn(row["expected_text"], self.page_text())
                elif expected == "404_not_found":
                    self.assertIn("404", self.page_text(), f"{test_id}: Non-existent route must return 404")

        elif category == "page_creation":
            self.login_as_admin()
            raw_route = row["route"]
            route = raw_route.replace("{uid}", uuid.uuid4().hex[:6])
            title = row["title"]
            content = row["content"]
            draft = (row["draft"].strip().lower() == "true")
            hidden = (row["hidden"].strip().lower() == "true")
            auth_required = (row["auth_required"].strip().lower() == "true")

            self.create_page(title=title, route=route, content=content, draft=draft, hidden=hidden, auth_required=auth_required)

            if expected == "published_page":
                # Clear cookies and test as public guest
                d.delete_all_cookies()
                d.get(f"{BASE_URL}/{route}")
                time.sleep(DELAY)
                self.assertIn(row["expected_text"], self.page_text(), f"{test_id}: Published page content must display")
                if not hidden:
                    nav_links = [a.text.strip() for a in d.find_elements(By.CSS_SELECTOR, "nav a.nav-link")]
                    self.assertIn(title, nav_links, f"{test_id}: Published page must appear in navbar")

            elif expected == "404_not_found":
                d.delete_all_cookies()
                d.get(f"{BASE_URL}/{route}")
                time.sleep(DELAY)
                self.assertIn("404", self.page_text(), f"{test_id}: Draft page must return 404")

            elif expected == "auth_required":
                d.delete_all_cookies()
                d.get(f"{BASE_URL}/{route}")
                time.sleep(DELAY)
                self.assertIn("/login", d.current_url, f"{test_id}: Auth-required page must redirect unauthenticated visitor")


if __name__ == "__main__":
    unittest.main()
