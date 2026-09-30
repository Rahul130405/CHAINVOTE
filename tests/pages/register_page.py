"""
Page Object Model for CHAINVOTE User Registration (/register/).
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class RegisterPage(BasePage):
    """Encapsulates interactions with the registration page."""

    PATH = "/register/"

    # Locators
    PAGE_HEADING = (By.XPATH, "//h1[contains(text(), 'Create Account') or contains(text(), 'खाता')]")
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    PASSWORD2_INPUT = (By.ID, "password2")
    SUBMIT_BTN = (By.CSS_SELECTOR, "form button[type='submit']")
    SIGN_IN_LINK = (By.XPATH, "//a[contains(@href, 'login')]")
    ERROR_ALERT = (By.CSS_SELECTOR, "div.p-3.rounded-xl, div[role='alert']")
    PASSWORD_TOGGLE_BTN = (By.ID, "togglePasswordBtn")
    PASSWORD2_TOGGLE_BTN = (By.ID, "togglePassword2Btn")

    def navigate(self):
        """Navigates directly to the registration page."""
        self.driver.get(f"{self.base_url}{self.PATH}")
        self.wait_for_visible(self.PAGE_HEADING)
        return self

    def enter_username(self, username: str):
        """Types username into #username field."""
        self.enter_text(self.USERNAME_INPUT, username)

    def enter_password(self, password: str):
        """Types password into #password field."""
        self.enter_text(self.PASSWORD_INPUT, password)

    def enter_confirm_password(self, password2: str):
        """Types confirmation password into #password2 field."""
        self.enter_text(self.PASSWORD2_INPUT, password2)

    def click_submit(self):
        """Clicks the Create Account submit button."""
        self.click(self.SUBMIT_BTN)

    def register(self, username: str, password: str, password2: str):
        """Helper to fill out registration form and submit."""
        self.enter_username(username)
        self.enter_password(password)
        self.enter_confirm_password(password2)
        self.click_submit()

    def get_error_message(self) -> str:
        """Retrieves text from the error flash banner."""
        return self.get_text(self.ERROR_ALERT)

    def has_error_alert(self) -> bool:
        """Checks if an error alert is currently visible."""
        return self.is_visible(self.ERROR_ALERT, timeout=3)

    def click_sign_in(self):
        """Clicks the 'Sign in here' link navigating to /login/."""
        self.click(self.SIGN_IN_LINK)

    def toggle_password_visibility(self):
        """Clicks the show/hide password toggle button for #password."""
        self.click(self.PASSWORD_TOGGLE_BTN)

    def toggle_password2_visibility(self):
        """Clicks the show/hide password toggle button for #password2."""
        self.click(self.PASSWORD2_TOGGLE_BTN)

    def get_password_input_type(self) -> str:
        """Returns the type attribute ('password' or 'text') of the password input."""
        elem = self.find_element(self.PASSWORD_INPUT)
        return elem.get_attribute("type")

    def get_password2_input_type(self) -> str:
        """Returns the type attribute ('password' or 'text') of the password2 input."""
        elem = self.find_element(self.PASSWORD2_INPUT)
        return elem.get_attribute("type")
