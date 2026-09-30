"""
Page Object Model for CHAINVOTE Sign In (/login/).
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class LoginPage(BasePage):
    """Encapsulates interactions with the login page."""

    PATH = "/login/"

    # Locators
    PAGE_HEADING = (By.XPATH, "//h1[contains(text(), 'Welcome Back') or contains(text(), 'स्वागत')]")
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BTN = (By.CSS_SELECTOR, "form button[type='submit']")
    REGISTER_LINK = (By.XPATH, "//a[contains(@href, 'register')]")
    ERROR_ALERT = (By.CSS_SELECTOR, "div.p-3.rounded-xl, div[role='alert']")
    PASSWORD_TOGGLE_BTN = (By.ID, "togglePasswordBtn")

    def navigate(self):
        """Navigates directly to the login page."""
        self.driver.get(f"{self.base_url}{self.PATH}")
        self.wait_for_visible(self.PAGE_HEADING)
        return self

    def enter_username(self, username: str):
        """Types username into #username field."""
        self.enter_text(self.USERNAME_INPUT, username)

    def enter_password(self, password: str):
        """Types password into #password field."""
        self.enter_text(self.PASSWORD_INPUT, password)

    def click_submit(self):
        """Clicks the Sign In submit button."""
        self.click(self.SUBMIT_BTN)

    def login(self, username: str, password: str):
        """Helper to fill out credentials and submit."""
        self.enter_username(username)
        self.enter_password(password)
        self.click_submit()

    def get_error_message(self) -> str:
        """Retrieves text from the error flash banner."""
        return self.get_text(self.ERROR_ALERT)

    def has_error_alert(self) -> bool:
        """Checks if an error alert is currently visible."""
        return self.is_visible(self.ERROR_ALERT, timeout=3)

    def click_create_account(self):
        """Clicks the 'Create one' link navigating to /register/."""
        self.click(self.REGISTER_LINK)

    def toggle_password_visibility(self):
        """Clicks the show/hide password toggle button."""
        self.click(self.PASSWORD_TOGGLE_BTN)

    def get_password_input_type(self) -> str:
        """Returns the type attribute ('password' or 'text') of the password input."""
        elem = self.find_element(self.PASSWORD_INPUT)
        return elem.get_attribute("type")
