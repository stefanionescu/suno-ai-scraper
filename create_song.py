import os
import time
from aws.aws import AWS
import utils.utils as utils
import constants as CONSTANTS
from dotenv import load_dotenv
import proxy_profiles as PROXIES
from db.supabase import Supabase
from sign_in.sign_in import SignIn
import driver.driver as SELENIUM_DRIVER
import login_profiles as LOGIN_PROFILES
from selenium.webdriver.common.by import By
from scrape_song.scrape_song import ScrapeSong
from error_logging.error_logging import ErrorLogging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

def page_has_loaded(driver):
    return driver.execute_script("return document.readyState") == "complete"

def navigate_with_refresh(driver, url, max_attempts=CONSTANTS.MAX_PAGE_RELOAD_TRIES, timeout=CONSTANTS.PAGE_LOAD_RETRY_SESSION):
    for attempt in range(max_attempts):
        try:
            print(f"CREATE_SONG: Attempting to navigate to {url} (Attempt #{attempt + 1})")
            driver.get(url)
            WebDriverWait(driver, timeout).until(page_has_loaded)
            print("CREATE_SONG: Page loaded successfully.")
            return True
        except TimeoutException:
            if attempt < max_attempts - 1:
                print(f"CREATE_SONG: Page load timed out. Refreshing...")
                driver.refresh()
            else:
                print(f"CREATE_SONG: Page at {url} failed to load after {max_attempts} attempts.")
                return False

def check_suno_creds():
    """Checks Suno credentials availability and validity."""
    if len(LOGIN_PROFILES.login_profiles) != len(PROXIES.proxy_profiles):
        print("CREATE_SONG: Login profiles and proxy profiles lengths differ.")
        return False
    
    if set(LOGIN_PROFILES.login_profiles.keys()) != set(PROXIES.proxy_profiles.keys()):
        print("CREATE_SONG: The phone number and proxy keys do not match.")
        return False

    login_required_keys = {"phone_provider", "phone", "country", "country_code"}
    proxy_required_keys = {"proxy_address", "port", "username", "password"}

    for key, login_profile in LOGIN_PROFILES.login_profiles.items():
        if not login_required_keys.issubset(login_profile):
            print(f"CREATE_SONG: Incorrect structure for the login profile with key {key}")
            return False
        
        if any(not login_profile[k] for k in login_required_keys):
            print(f"CREATE_SONG: Empty or None value in login profile with key {key}")
            return False

    for key, proxy_profile in PROXIES.proxy_profiles.items():
        if not proxy_required_keys.issubset(proxy_profile):
            print(f"CREATE_SONG: Incorrect structure for the proxy profile with key {key}")
            return False
        
        if any(not proxy_profile[k] for k in proxy_required_keys):
            print(f"CREATE_SONG: Empty or None value in proxy profile with key {key}")
            return False

    return True

def check_general_vars():
    """Validate general bot settings from environment variables."""
    env_vars = {
        "TWILIO_ACCOUNT_SID": "Twilio",
        "TWILIO_AUTH_TOKEN": "Twilio",
        "MESSAGE_BIRD_API_KEY": "MessageBird",
        "AWS_REGION": "AWS",
        "AWS_ACCESS_KEY": "AWS",
        "AWS_SECRET_ACCESS_KEY": "AWS",
        "AWS_BUCKET_NAME": "AWS",
        "SUPABASE_JWT_SECRET": "Supabase",
        "SUPABASE_URL": "Supabase",
        "SUPABASE_ANON_KEY": "Supabase"
    }

    for var, service in env_vars.items():
        if not os.getenv(var):
            print(f"CREATE_SONG: Invalid {service} params.")
            return False
    
    return True

def check_os_params():
    """Checks OS parameters for validity."""
    try:
        generation_id = os.getenv('GENERATION_ID')
        phone_number = os.getenv('PHONE_NUMBER')
        max_runtime = int(os.getenv('MAX_RUNTIME', 0))

        if not generation_id or len(generation_id) > CONSTANTS.MAX_GENERATION_ID_LENGTH:
            print("CREATE_SONG: Invalid generation ID.")
            return False
        
        if not phone_number or phone_number not in LOGIN_PROFILES.login_profiles:
            print("CREATE_SONG: Inexistent phone number.")
            return False
        
        if not CONSTANTS.MIN_RUNTIME <= max_runtime <= CONSTANTS.MAX_RUNTIME:
            print("CREATE_SONG: Invalid max runtime.")
            return False
        
        return True
    except Exception as e:
        print(f"CREATE_SONG: An error occurred: {e}.")
        return False
    
def check_ip(driver):
    print("CREATE_SONG: Checking the IP I'm using...")

    if navigate_with_refresh(driver, CONSTANTS.IP_CHECKER_URL):
        utils.random_short_sleep()

    current_ip = driver.find_element(By.TAG_NAME, "body").text
    if str(current_ip) in CONSTANTS.VALID_IPS:
        print("CREATE_SONG: The IP used by this scraper is valid")
        return True

    print("CREATE_SONG: The IP used by this scraper is invalid.")
    return False

def make_supabase_checks():
    """Performs Supabase-related checks."""
    supabase = Supabase()

    if not supabase.is_valid_song_generation():
        print("CREATE_SONG: The generation ID doesn't exist on Supabase, the generation data is invalid or there's an existing song file associated with the generation.")
        return False

    if not supabase.scraper_can_create_song():
        print("CREATE_SONG: The scraper cannot create a song with the provided phone number.")
        return False

    return True

def get_song_creation_data():
    """Retrieves the song creation data from Supabase."""
    return Supabase().get_song_creation_data()

def log_into_account(driver):
    """Log into a Suno account using provided WebDriver and credentials."""
    sign_in = SignIn(driver)
    phone_number = os.getenv('PHONE_NUMBER')
    if not sign_in.sign_in(LOGIN_PROFILES.login_profiles[phone_number]):
        print("CREATE_SONG: Failed to sign in with a phone number.")
        return False
    return True

def scrape_song(driver, start_time, song_prompt, downloads_dir):
    """Initiates song scraping process."""
    scrape_song = ScrapeSong(driver)
    return scrape_song.scrape_song(start_time, song_prompt, downloads_dir)

def main(start_time):
    """Main execution routine."""
    checks = [
        ("OS params", check_os_params),
        ("Suno credential", check_suno_creds),
        ("general vars", check_general_vars),
        ("Supabase", make_supabase_checks)
    ]

    for check_name, check_func in checks:
        print(f"CREATE_SONG: Checking {check_name}...")
        if not check_func():
            ErrorLogging().save_error_and_send_email("SCRAPER - CREATE_SONG: Could not pass initial checks before scraping.")
            return
        print(f"CREATE_SONG: Passed {check_name} checks.")

    song_creation_data = get_song_creation_data()
    if not song_creation_data:
        print("CREATE_SONG: Invalid song creation data fetched from Supabase.")
        ErrorLogging().save_error_and_send_email("SCRAPER - CREATE_SONG: Invalid song creation data fetched from Supabase.")
        return
    
    print("CREATE_SONG: Fetched the song creation data from Supabase.")

    print("CREATE_SONG: Setting up AWS utils...")
    aws = AWS()
    chrome_profiles_dir = os.path.abspath(CONSTANTS.CHROME_PROFILES_DIR_PATH)
    downloads_dir = os.path.abspath(CONSTANTS.DOWNLOADS_DIR_PATH)
    phone_number = os.getenv('PHONE_NUMBER')

    print("CREATE_SONG: Setting up the Chrome driver...")

    driver = SELENIUM_DRIVER.setup_chrome_driver(aws, chrome_profiles_dir, downloads_dir)

    try:
        if not driver:
            print("CREATE_SONG: Could not instantiate the Selenium driver.")
            ErrorLogging().save_error_and_send_email("SCRAPER - CREATE_SONG: Could not instantiate the Selenium driver.")
            return

        driver.set_page_load_timeout(CONSTANTS.PAGE_LOAD_TIMEOUT)
        driver.maximize_window()

        if not check_ip(driver):
            ErrorLogging().save_error_and_send_email("SCRAPER - CREATE_SONG: This scraper tried to use an invalid IP.")
            return

        print("CREATE_SONG: Navigating to Suno's website...")
        if navigate_with_refresh(driver, CONSTANTS.BASE_URL):
            utils.random_long_sleep()
        else:
            ErrorLogging().save_error_and_send_email("SCRAPER - CREATE_SONG: Could not navigate to Suno even after several retries.")
            return

        if driver.current_url.startswith(CONSTANTS.SIGN_IN_URL):
            print("CREATE_SONG: Logging into Suno...")
            if not log_into_account(driver):
                print("CREATE_SONG: Could not log into Suno.")
                ErrorLogging().save_error_and_send_email("SCRAPER - CREATE_SONG: Could not log into Suno.")
                return
        elif driver.current_url.startswith(CONSTANTS.BASE_URL):
            print("CREATE_SONG: Skipped the login flow because I'm already on the Create page.")
        else:
            print("CREATE_SONG: Could not get into the Suno dashboard.")
            ErrorLogging().save_error_and_send_email("SCRAPER - CREATE_SONG: Could not get into the Suno dashboard.")
            return

        if not scrape_song(driver, start_time, song_creation_data, downloads_dir):
            print("CREATE_SONG: Could not create and download the song.")
        else:
            print("CREATE_SONG: Finished downloading and saving the song.")
    except Exception as e:
        print(f"CREATE_SONG: An unexpected error occurred: {e}.")
        ErrorLogging().save_error_and_send_email(f"SCRAPER - CREATE_SONG: An unexpected error occurred: {e}.")
    finally:
        print("CREATE_SONG: Finished the scraping job.")
        if driver:
            print("CREATE_SONG: Closing the driver...")
            driver.quit()

        utils.delete_directory(downloads_dir)

        if driver:
            print("CREATE_SONG: Saving the Chrome profile to s3...")
            profile_dir = f"{chrome_profiles_dir}/{phone_number}_chrome_profile"
            zip_dir = f"{chrome_profiles_dir}/{phone_number}_chrome_profile"

            if aws.compress_chrome_profile(profile_dir, zip_dir):
                aws.save_profile_in_bucket(zip_dir + ".zip", phone_number)
                
            utils.delete_file(zip_dir + ".zip")
            utils.delete_directory(chrome_profiles_dir)

            end_timestamp = int(time.time())
            print(f"CREATE_SONG: End timestamp is {end_timestamp}")
            print(f"CREATE_SONG: Spent {end_timestamp - start_time} seconds on scraping the song.")

if __name__ == '__main__':
    start_time = int(time.time())
    print(f"CREATE_SONG: Start timestamp is {start_time}")
    load_dotenv()
    main(start_time)