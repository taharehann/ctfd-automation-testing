import unittest
from selenium import webdriver

class SmokeTest(unittest.TestCase):
    def test_home_page_opens(self):
        driver = webdriver.Chrome()
        driver.get("http://localhost:4000")
        self.assertIn("TestCTF", driver.title)  # use your event name
        driver.quit()

if __name__ == "__main__":
    unittest.main()