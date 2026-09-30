"""
Page Object Model for CHAINVOTE Digital Voting Booth (/election/<id>/).
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class VotingBoothPage(BasePage):
    """Encapsulates digital voting booth form interaction and receipt modal states."""

    # Locators
    ELECTION_TITLE_H1 = (By.CSS_SELECTOR, "h1")
    VOTE_FORM = (By.ID, "voteForm")
    AADHAAR_INPUT = (By.ID, "aadhaar")
    SUBMIT_BTN = (By.ID, "submitBtn")
    BTN_TEXT = (By.ID, "btnText")
    ABORT_LINK = (By.LINK_TEXT, "Abort & Return")

    # Review Modal Locators (Phase 2 Review-and-Confirm step)
    REVIEW_MODAL = (By.ID, "reviewModal")
    REVIEW_CANDIDATE_NAME = (By.ID, "reviewCandidateName")
    REVIEW_CANDIDATE_INITIAL = (By.ID, "reviewCandidateInitial")
    REVIEW_VOTER_ID_MASKED = (By.ID, "reviewVoterIdMasked")
    CHANGE_SELECTION_BTN = (By.ID, "changeSelectionBtn")
    CONFIRM_SUBMIT_BTN = (By.ID, "confirmSubmitBtn")
    VALIDATION_ALERT = (By.ID, "validationAlert")
    VALIDATION_ALERT_MSG = (By.ID, "validationAlertMsg")
    AADHAAR_TOGGLE_BTN = (By.ID, "toggleAadhaarBtn")
    REVIEW_BADGE = (By.XPATH, "//*[@id='reviewModal']//span[@data-i18n='badge_masked' or @data-i18n='badge_encrypted']")

    # Receipt Modal Locators (Rendered upon successful vote commit)
    RECEIPT_MODAL = (By.ID, "receiptModal")
    RECEIPT_STATUS_TEXT = (By.XPATH, "//*[@id='receiptModal']//*[contains(text(), 'Block Mined Successfully')]")
    RECEIPT_TIME_TEXT = (By.ID, "receiptTime")
    RECEIPT_RETURN_BTN = (By.XPATH, "//*[@id='receiptModal']//a[contains(@href, '/') or contains(text(), 'Return to Network') or contains(text(), 'लौटें')]")
    RECEIPT_PRINT_BTN = (By.XPATH, "//*[@id='receiptModal']//button[contains(text(), 'Print Receipt') or contains(text(), 'प्रिंट')]")

    # Security Alert / Rejection Banner
    SECURITY_ALERT_BANNER = (By.XPATH, "//*[contains(@class, 'bg-red-50') or contains(@class, 'dark:bg-red-950') or contains(@class, 'bg-red-950')][contains(., 'SECURITY_ALERT') or contains(., 'already voted')]")

    def navigate(self, election_id: int):
        """Navigates to the voting booth for a specific election."""
        self.driver.get(f"{self.base_url}/election/{election_id}/")
        self.wait_for_visible(self.VOTE_FORM)
        return self

    def get_election_title(self) -> str:
        """Returns the election heading text."""
        return self.get_text(self.ELECTION_TITLE_H1)

    def enter_voter_id(self, identity: str):
        """Enters voter identity (Aadhaar/Roll No) into #aadhaar field."""
        self.enter_text(self.AADHAAR_INPUT, identity)

    def select_candidate(self, candidate_id: int):
        """
        Selects a candidate by clicking the visible <label for='candidate_<id>'>
        associated with the hidden 'sr-only' radio input.
        """
        label_locator = (By.CSS_SELECTOR, f"label[for='candidate_{candidate_id}']")
        self.click(label_locator)

    def select_candidate_by_name(self, candidate_name: str):
        """
        Selects a candidate by matching the candidate name in the visible card label.
        """
        label_locator = (By.XPATH, f"//label[.//h3[contains(text(), '{candidate_name}')]]")
        self.click(label_locator)

    def is_candidate_selected(self, candidate_id: int) -> bool:
        """Verifies if the candidate radio input is in a checked state."""
        radio_locator = (By.ID, f"candidate_{candidate_id}")
        radio_elem = self.find_element(radio_locator)
        return radio_elem.is_selected()

    def click_submit_vote(self):
        """Clicks the review/submit button on the voting form."""
        self.click(self.SUBMIT_BTN)

    def click_review_vote(self):
        """Clicks the 'Review Your Vote' button on the voting form."""
        self.click(self.SUBMIT_BTN)

    def wait_for_review_modal(self, timeout: int = 10):
        """Waits for the Review-and-Confirm modal to be visible in the DOM."""
        return self.wait_for_visible(self.REVIEW_MODAL, timeout=timeout)

    def is_review_modal_visible(self) -> bool:
        """Checks if the Review-and-Confirm modal is currently visible."""
        return self.is_visible(self.REVIEW_MODAL, timeout=3)

    def get_review_candidate_name(self) -> str:
        """Returns the candidate name displayed inside the Review Modal."""
        return self.get_text(self.REVIEW_CANDIDATE_NAME)

    def get_review_voter_id_masked(self) -> str:
        """Returns the masked voter ID displayed inside the Review Modal."""
        return self.get_text(self.REVIEW_VOTER_ID_MASKED)

    def get_review_badge_text(self) -> str:
        """Returns the badge text (e.g. 'Masked') displayed next to the voter ID."""
        return self.get_text(self.REVIEW_BADGE)

    def click_change_selection(self):
        """Clicks 'Change Selection' inside the Review Modal to return to the ballot."""
        self.click(self.CHANGE_SELECTION_BTN)

    def click_confirm_and_submit(self):
        """Clicks 'Confirm & Submit Vote' inside the Review Modal."""
        self.click(self.CONFIRM_SUBMIT_BTN)

    def submit_ballot(self, voter_id: str, candidate_id: int):
        """
        Complete flow helper:
        1. Enters voter ID
        2. Selects candidate
        3. Clicks 'Review Your Vote'
        4. Waits for Review Modal
        5. Clicks 'Confirm & Submit Vote'
        """
        self.enter_voter_id(voter_id)
        self.select_candidate(candidate_id)
        self.click_review_vote()
        self.wait_for_review_modal()
        self.click_confirm_and_submit()

    def has_validation_alert(self) -> bool:
        """Checks if the client-side validation warning banner is visible."""
        return self.is_visible(self.VALIDATION_ALERT, timeout=2)

    def get_validation_alert_text(self) -> str:
        """Returns the validation warning banner message text."""
        return self.get_text(self.VALIDATION_ALERT_MSG)

    def toggle_voter_id_visibility(self):
        """Clicks the show/hide password toggle on the Voter ID input."""
        self.click(self.AADHAAR_TOGGLE_BTN)

    def get_voter_id_input_type(self) -> str:
        """Returns the current type attribute ('password' or 'text') of #aadhaar."""
        elem = self.find_element(self.AADHAAR_INPUT)
        return elem.get_attribute("type")

    def get_voter_id_minlength(self) -> str:
        """Returns the minlength attribute of #aadhaar."""
        return self.find_element(self.AADHAAR_INPUT).get_attribute("minlength")

    def get_voter_id_maxlength(self) -> str:
        """Returns the maxlength attribute of #aadhaar."""
        return self.find_element(self.AADHAAR_INPUT).get_attribute("maxlength")

    def get_voter_id_pattern(self) -> str:
        """Returns the pattern attribute of #aadhaar."""
        return self.find_element(self.AADHAAR_INPUT).get_attribute("pattern")

    def get_voter_id_value(self) -> str:
        """Returns the current entered value of #aadhaar."""
        return self.find_element(self.AADHAAR_INPUT).get_attribute("value")

    def wait_for_receipt_modal(self, timeout: int = 15):
        """
        Waits for the post-submission receipt modal to appear in DOM.
        Accommodates the 1.5s client-side mining delay and page reload.
        """
        return self.wait_for_visible(self.RECEIPT_MODAL, timeout=timeout)

    def is_receipt_modal_visible(self) -> bool:
        """Checks if the receipt modal is currently visible."""
        return self.is_visible(self.RECEIPT_MODAL, timeout=3)

    def get_receipt_status_message(self) -> str:
        """Returns the status text ('Block Mined Successfully') from the receipt modal."""
        return self.get_text(self.RECEIPT_STATUS_TEXT)

    def get_receipt_timestamp(self) -> str:
        """Returns the local timestamp rendered in the receipt modal."""
        return self.get_text(self.RECEIPT_TIME_TEXT)

    def click_return_to_network(self):
        """Clicks 'Return to Network' button inside the receipt modal."""
        self.click(self.RECEIPT_RETURN_BTN)

    def wait_for_security_alert(self, timeout: int = 15):
        """Waits for the duplicate vote security alert banner to render."""
        return self.wait_for_visible(self.SECURITY_ALERT_BANNER, timeout=timeout)

    def has_security_alert(self) -> bool:
        """Checks if a security alert banner is displayed."""
        return self.is_visible(self.SECURITY_ALERT_BANNER, timeout=3)

    def get_security_alert_text(self) -> str:
        """Returns the text content of the security alert banner."""
        return self.get_text(self.SECURITY_ALERT_BANNER)

    def click_abort_and_return(self):
        """Clicks the 'Abort & Return' link."""
        self.click(self.ABORT_LINK)
