import utils.utils as utils
import constants as CONSTANTS
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from phone.twilio import Twilio
from phone.message_bird import MessageBird
from selenium.webdriver.common.by import By
from error_logging.error_logging import ErrorLogging

class SignIn:
    def __init__(self, driver):
        self.driver = driver
        load_dotenv()  # Load environment variables once during initialization

    def sign_in(self, sign_in_details):
        """Main sign-in method that orchestrates the entire sign-in process."""
        if not self.validate_sign_in_details(sign_in_details):
            return False

        print("SIGN_IN: Validated the sign in details.")

        if not self.ensure_correct_sign_in_page():
            return False
        
        print("SIGN_IN: Ensured that I'm on the Suno sign in page.")

        if not self.set_country_code(sign_in_details['country'], sign_in_details['country_code']):
            return False
        
        print("SIGN_IN: Managed to set the phone country code.")

        if not self.enter_phone_number(sign_in_details['phone']):
            return False
        
        print("SIGN_IN: Wrote the phone number in the input field.")

        if not self.submit_and_verify_phone_number():
            return False
        
        print("SIGN_IN: Submitted and verified the phone number.")

        client = self.get_sms_client(sign_in_details)
        verification_code = client.fetch_suno_verification_code()
        
        if verification_code:
            print("SIGN_IN: Got the verification code without resending. Trying to type it on the sign in page and finish signing in...")
            if self.enter_verification_code(verification_code):
                return self.verify_if_on_create_screen()

        print("SIGN_IN: Resending the verification code for the first time and trying to fetch it...")
        
        verification_code = self.resend_code_and_fetch(client)
        if verification_code:
            print("SIGN_IN: Got the verification code on the first resend. Trying to type it on the sign in page and finish signing in...")
            if self.enter_verification_code(verification_code):
                return self.verify_if_on_create_screen()

        print("SIGN_IN: Resending the verification code for the second time and trying to fetch it...")
        
        verification_code = self.resend_code_and_fetch(client)
        if not verification_code:
            print("SIGN_IN: Could not fetch the sign in code after resending.")
            return False
        
        return self.enter_verification_code_and_verify(verification_code)

    def resend_code_and_fetch(self, client):
        """Resends the verification code and attempts to fetch it."""
        resend_btn = self.find_element(By.XPATH, CONSTANTS.RESEND_CODE_BUTTON_SIGN_IN)
        if not resend_btn:
            print("SIGN_IN: Could not find the Resend button.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Could not find the Resend button.")
            return False
        resend_btn.click()
        
        utils.random_long_sleep()
        utils.random_short_sleep()

        return client.fetch_suno_verification_code()

    def get_sms_client(self, sign_in_details):
        """Returns the appropriate SMS client based on the phone provider."""
        if sign_in_details["phone_provider"] == "twilio":
            return Twilio(sign_in_details["country_code"] + sign_in_details["phone"])
        elif sign_in_details["phone_provider"] == "message_bird":
            return MessageBird(sign_in_details)
        return None

    def validate_sign_in_details(self, details):
        """Validates the sign-in details provided."""
        required_keys = ["phone", "country", "phone_provider", "country_code"]
        if not details or any(key not in details or not details[key] for key in required_keys):
            print("SIGN_IN: Invalid sign in details.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Invalid sign in details.")
            return False
        return True

    def ensure_correct_sign_in_page(self):
        """Checks if the current page is the correct sign-in page."""
        if not self.driver.current_url.startswith(CONSTANTS.SIGN_IN_URL):
            print("SIGN_IN: Not on the phone sign in page.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Not on the phone sign in page.")
            return False
        return True

    def set_country_code(self, country, country_code):
        """Sets the country code for the phone number."""
        return self.select_country_code() and self.search_country_code(country, country_code)

    def enter_phone_number(self, phone):
        """Enters the phone number into the input field."""
        phone_input_field = self.find_element(By.XPATH, CONSTANTS.NUMBER_INPUT_FIELD)
        if not phone_input_field:
            print("SIGN_IN: Could not find the phone input field.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Could not find the phone input field.")
            return False
        phone_input_field.click()
        phone_input_field.send_keys(phone)
        utils.random_short_sleep()
        return True

    def submit_and_verify_phone_number(self):
        """Submits the phone number and verifies if it's successful."""
        continue_btn = self.find_element(By.XPATH, CONSTANTS.CONTINUE_BUTTON_SIGN_IN)
        if not continue_btn:
            print("SIGN_IN: Could not find the Continue button.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Could not find the Continue button.")
            return False
        continue_btn.click()
        utils.random_long_sleep()
        utils.random_normal_sleep()
        return self.check_for_phone_verification_screen()

    def check_for_phone_verification_screen(self):
        """Checks if the current screen is the phone verification screen."""
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        if CONSTANTS.SIGN_IN_CHECK_PHONE not in soup.get_text():
            print("SIGN_IN: Not on the Check your phone screen.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Not on the Check your phone screen.")
            return False
        return True
    
    def enter_verification_code_and_verify(self, code):
        """Enters the verification code and verifies if sign-in is successful."""
        return self.enter_verification_code(code) and self.verify_if_on_create_screen()

    def enter_verification_code(self, code):
        """Enters the verification code into the input field."""
        first_digit_input_field = self.find_element(By.XPATH, CONSTANTS.SIGN_IN_CODE_FIRST_DIGIT)
        if not first_digit_input_field:
            print("SIGN_IN: Could not find the input field for the sign in code.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Could not find the input field for the sign in code.")
            return False
        first_digit_input_field.send_keys(code)
        print("SIGN_IN: Typed the verification code. Waiting before I check if I'm on the Create page...")
        utils.random_long_sleep()
        return True

    def verify_if_on_create_screen(self):
        """Verifies if the current page is the create screen."""
        return self.driver.current_url.startswith(CONSTANTS.BASE_URL)
    
    def select_country_code(self):
        """Selects the country code dropdown."""
        try:
            country_code_selector = self.find_element(By.XPATH, CONSTANTS.COUNTRY_CODE_BUTTON_SIGN_IN)
            if not country_code_selector:
                print("SIGN_IN: Could not find the country code selector.")
                ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Could not find the country code selector.")
                return False
            country_code_selector.click()
            utils.random_short_sleep()
            return True
        except Exception as e:
            print(f"SIGN_IN: Error accessing country code selector: {e}")
            ErrorLogging().save_error_and_send_email(f"SCRAPER - SIGN_IN: Error accessing country code selector: {e}")
            return False
        
    def search_country_code(self, country, country_code):
        """Searches for and selects the specified country code."""
        try:
            country_code_search_field = self.find_element(By.XPATH, CONSTANTS.COUNTRY_CODE_SEARCH_FIELD_SIGN_IN)
            if not country_code_search_field:
                print("SIGN_IN: Could not find the country code search field.")
                ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Could not find the country code search field.")
                return False
            country_code_search_field.send_keys(country)
            utils.random_short_sleep()

            target_countries = self.driver.find_elements(By.XPATH, CONSTANTS.COUNTRY_CODE_LIST_ELEMENT_SIGN_IN)
            for country_element in target_countries:
                country_codes = country_element.find_elements(By.TAG_NAME, "p")

                if len(country_codes) == 1 and country_codes[0].text.lower() == country_code.lower():
                    country_element.click()
                    utils.random_short_sleep()
                    return True
            
            print("SIGN_IN: Could not find the target country.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SIGN_IN: Could not find the target country.")
            return False
        except Exception as e:
            print(f"SIGN_IN: Error while searching for country code: {e}")
            ErrorLogging().save_error_and_send_email(f"SCRAPER - SIGN_IN: Error while searching for country code: {e}")
            return False

    def find_element(self, by_method, identifier):
        """Finds a single element on the page."""
        elements = self.driver.find_elements(by_method, identifier)
        if len(elements) == 1:
            return elements[0]
        print(f"SIGN_IN: Multiple or no elements found for {identifier}")
        return None