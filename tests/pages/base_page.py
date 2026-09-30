"""
Base Page Object for CHAINVOTE Selenium WebDriver test suite.

Encapsulates common WebDriver interactions, explicit waits,
and shared global components (Navbar, theme switcher, alerts).
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BasePage:
    """Base class for all Page Object Models."""

    # Common navigation locators
    NAV_BRAND_LINK = (By.CSS_SELECTOR, "nav a[href='/']")
    THEME_TOGGLE_BTN = (By.ID, "theme-toggle")
    LANG_TOGGLE_BTN = (By.ID, "lang-toggle")
    LANG_TEXT = (By.ID, "lang-text")
    USER_GREETING_SPAN = (By.XPATH, "//nav//*[contains(@class, 'user-greeting-badge') or contains(text(), '👤')]")
    SIGN_OUT_LINK = (By.XPATH, "//nav//a[contains(@href, 'logout') or contains(text(), 'Sign Out') or contains(text(), 'लॉग आउट')]")
    LOG_IN_LINK = (By.XPATH, "//nav//a[contains(@href, 'login') or contains(text(), 'Log In') or contains(text(), 'लॉग इन')]")
    HTML_ROOT = (By.TAG_NAME, "html")

    def __init__(self, driver: WebDriver, base_url: str):
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    def find_element(self, locator: tuple, timeout: int = 10) -> WebElement:
        """Finds and returns a WebElement after waiting for presence."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def find_elements(self, locator: tuple, timeout: int = 10) -> list[WebElement]:
        """Finds and returns a list of WebElements after waiting for presence."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(locator)
            )
        except TimeoutException:
            return []

    def wait_for_visible(self, locator: tuple, timeout: int = 10) -> WebElement:
        """Waits for an element to be visible in the DOM and viewport."""
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_for_clickable(self, locator: tuple, timeout: int = 10) -> WebElement:
        """Waits for an element to be visible and enabled for clicking."""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def click(self, locator: tuple, timeout: int = 10):
        """Clicks an element after ensuring it is clickable."""
        element = self.wait_for_clickable(locator, timeout)
        element.click()

    def js_click(self, locator_or_element, timeout: int = 10):
        """Clicks an element using JavaScript (useful for obscured or animated targets)."""
        if isinstance(locator_or_element, tuple):
            element = self.find_element(locator_or_element, timeout)
        else:
            element = locator_or_element
        self.driver.execute_script("arguments[0].click();", element)

    def enter_text(self, locator: tuple, text: str, timeout: int = 10, clear_first: bool = True):
        """Enters text into an input field after waiting for visibility."""
        element = self.wait_for_visible(locator, timeout)
        if clear_first:
            element.clear()
        element.send_keys(text)

    def get_text(self, locator: tuple, timeout: int = 10) -> str:
        """Returns the text content of an element."""
        element = self.wait_for_visible(locator, timeout)
        return element.text.strip()

    def is_visible(self, locator: tuple, timeout: int = 3) -> bool:
        """Checks if an element is currently visible without raising TimeoutException."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def wait_for_url_contains(self, partial_url: str, timeout: int = 10) -> bool:
        """Waits until the current browser URL contains the given substring."""
        return WebDriverWait(self.driver, timeout).until(
            EC.url_contains(partial_url)
        )

    def get_current_url(self) -> str:
        """Returns the browser's current URL."""
        return self.driver.current_url

    def get_title(self) -> str:
        """Returns the current page title."""
        return self.driver.title

    # ── Shared Navbar Methods ─────────────────────────

    def get_logged_in_username(self) -> str:
        """Extracts the username from the navbar '👤 <username>' span."""
        text = self.get_text(self.USER_GREETING_SPAN)
        return text.replace("👤", "").strip()

    def is_user_logged_in(self) -> bool:
        """Checks if the user greeting or Sign Out link is present in navbar."""
        return self.is_visible(self.SIGN_OUT_LINK, timeout=2)

    def wait_for_user_logged_in(self, timeout: int = 10):
        """Explicitly waits for the Sign Out link confirming authenticated session."""
        return self.wait_for_visible(self.SIGN_OUT_LINK, timeout=timeout)

    def click_sign_out(self):
        """Clicks the Sign Out link in the navbar."""
        self.click(self.SIGN_OUT_LINK)

    def click_log_in(self):
        """Clicks the Log In button in the navbar."""
        self.click(self.LOG_IN_LINK)

    def has_theme_toggle(self) -> bool:
        """Returns True if the theme toggle button exists in the DOM."""
        return len(self.driver.find_elements(*self.THEME_TOGGLE_BTN)) > 0

    def toggle_theme(self):
        """Clicks the theme toggle button in the navbar if present."""
        if self.has_theme_toggle():
            self.click(self.THEME_TOGGLE_BTN)

    def is_dark_mode(self) -> bool:
        """Checks if the <html> tag has the 'dark' CSS class."""
        html_elem = self.find_element(self.HTML_ROOT)
        classes = html_elem.get_attribute("class") or ""
        return "dark" in classes.split()

    def toggle_language(self):
        """Clicks the language switcher in the navbar."""
        self.click(self.LANG_TOGGLE_BTN)

    def get_current_language(self) -> str:
        """Returns the active preferred language code ('en' or 'hi') from localStorage."""
        return self.driver.execute_script("return localStorage.getItem('preferred-lang') || 'en';")

    def get_html_lang(self) -> str:
        """Returns the lang attribute of the <html> element."""
        return self.find_element(self.HTML_ROOT).get_attribute("lang") or "en"

    def set_viewport(self, width: int, height: int):
        """Resizes browser window to test responsive layout."""
        self.driver.set_window_size(width, height)
