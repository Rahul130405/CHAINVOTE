"""
Page Object Model for CHAINVOTE SOC Threat Dashboard (/security/threat-dashboard/).
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class SOCPage(BasePage):
    """Encapsulates Security Operations Center (SOC) dashboard interactions."""

    PATH = "/security/threat-dashboard/"

    # Locators
    PAGE_HEADING = (By.XPATH, "//h1[contains(text(), 'Threat Operations')]")
    PREVENTED_ATTACKS_COUNTER = (By.XPATH, "//p[contains(text(), 'Total Prevented Attacks')]/following-sibling::p")
    INCIDENT_ROWS = (By.CSS_SELECTOR, "table tbody tr")
    NETWORK_SECURE_BANNER = (By.XPATH, "//p[contains(text(), 'Network is Secure')]")

    def navigate(self):
        """Navigates to the SOC threat dashboard."""
        self.driver.get(f"{self.base_url}{self.PATH}")
        self.wait_for_visible(self.PAGE_HEADING)
        return self

    def get_prevented_attacks_count(self) -> int:
        """Returns the integer count from the 'Total Prevented Attacks' counter."""
        raw_text = self.get_text(self.PREVENTED_ATTACKS_COUNTER)
        return int(raw_text)

    def get_incident_count(self) -> int:
        """Returns the number of incident rows currently displayed in the event table."""
        if self.is_network_secure_banner_visible():
            return 0
        rows = self.find_elements(self.INCIDENT_ROWS)
        return len(rows)

    def is_network_secure_banner_visible(self) -> bool:
        """Checks if the empty state ('Network is Secure') banner is shown."""
        return self.is_visible(self.NETWORK_SECURE_BANNER, timeout=2)

    def get_latest_incident_details(self) -> dict:
        """
        Parses and returns details from the top row of the security incident table.
        Columns: [0] Timestamp, [1] Severity, [2] Origin IP, [3] Action Triggered, [4] Trace Details.
        """
        rows = self.find_elements(self.INCIDENT_ROWS)
        if not rows or self.is_network_secure_banner_visible():
            return {}

        top_row = rows[0]
        cols = top_row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 5:
            return {}

        return {
            "timestamp": cols[0].text.strip(),
            "severity": cols[1].text.strip(),
            "ip_address": cols[2].text.strip(),
            "action": cols[3].text.strip(),
            "details": cols[4].text.strip(),
        }
