import os
import zipfile
import platform
import tempfile
import constants as CONSTANTS
from dotenv import load_dotenv
import proxy_profiles as PROXIES
from proxy.extension import proxies
import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def setup_chrome_driver(aws, chrome_profiles_dir, downloads_dir):
    """
    Sets up and returns a Chrome WebDriver with configured options.
    """
    if not chrome_profiles_dir or not downloads_dir:
        print("DRIVER: Downloads or Chrome Profiles dir is null.")
        return None

    operating_system = is_macos_or_linux()
    if not operating_system or (operating_system != "macOS" and operating_system != "Linux"):
        print("DRIVER: Invalid operating system for this scraper.")
        return None
    
    user_agent = ""
    if operating_system == "macOS":
        user_agent = CONSTANTS.HEADERS_MACOS
        print("DRIVER: Picked the macOS user-agent.")
    else:
        user_agent = CONSTANTS.HEADERS_LINUX
        print("DRIVER: Picked the Linux user-agent.")

    load_dotenv()

    try:
        os.makedirs(downloads_dir, exist_ok=True)

        uc.TARGET_VERSION = get_os_chrome_version(operating_system)
        chrome_options = uc.ChromeOptions()

        aws.download_chrome_profile(chrome_profiles_dir, os.getenv('PHONE_NUMBER'))

        profile_dir = f"{chrome_profiles_dir}/{os.getenv('PHONE_NUMBER')}_chrome_profile"
        add_chrome_options(chrome_options, profile_dir, downloads_dir, user_agent, PROXIES.proxy_profiles[str(os.getenv('PHONE_NUMBER'))]["proxy_address"], operating_system)
        config_proxy_result = configure_proxy(chrome_options)
        if not config_proxy_result:
            return None
    
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "none"

        driver = uc.Chrome(version_main=int(uc.TARGET_VERSION.split(".")[0]), options=chrome_options, suppress_welcome=True, desired_capabilities=caps)

        # Apply stealth settings
        apply_stealth_settings(driver, operating_system)

        return driver
    except Exception as e:
        print(f"DRIVER: Got an error trying to instantiate the Selenium driver. Details: {e}")
        return None

def add_chrome_options(chrome_options, profile_dir, downloads_dir, user_agent, proxy_host, operating_system):
    """
    Adds necessary Chrome options for the browser.
    """
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": downloads_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--no-service-autorun')
    chrome_options.add_argument('--password-store=basic')
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument('--disable-features=PrivacySandboxSettings4')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--v=1')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument("--user-agent=" + user_agent)

    if proxy_host and proxy_host != "":
        chrome_options.add_argument('--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE %s"' % proxy_host)

    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--page-load-strategy=normal')
    chrome_options.page_load_strategy = 'normal'

    # OS-specific options
    if operating_system == "macOS":
        chrome_options.add_argument('--enable-quic')
    elif operating_system == "Linux":
        chrome_options.add_argument('--disable-setuid-sandbox')

def configure_proxy(chrome_options):
    """
    Configures a proxy for Chrome
    """
    load_dotenv()

    temp_dir = None
    proxy_details = get_proxy_details(str(os.getenv('PHONE_NUMBER')))
    if None not in proxy_details.values():
        proxy_extension = proxies(**proxy_details)

        # Create a temporary directory to extract the extension
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(proxy_extension, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        chrome_options.add_argument(f'--load-extension={temp_dir}')
        print("DRIVER: Proxy setup complete.")

        return True
    else:
        print("DRIVER: Incomplete proxy configuration. Check environment variables.")
        return False

def apply_stealth_settings(driver, operating_system):
    """
    Applies stealth settings to make the browser behave more like a regular user's.
    """
    if operating_system == "macOS":
        vendor = "Apple Inc."
        platform = "MacIntel"
        webgl_vendor = "Intel Inc."
        renderer = "Intel Iris OpenGL Engine"
    else:  # Linux
        vendor = "Google Inc."
        platform = "Linux x86_64"
        webgl_vendor = "Mesa/X.org"
        renderer = "Mesa DRI Intel(R) UHD Graphics (CML GT2)"

    stealth(driver,
        languages=["en-US", "en"],
        vendor=vendor,
        platform=platform,
        webgl_vendor=webgl_vendor,
        renderer=renderer,
        fix_hairline=True,
    )

def get_proxy_details(number):
    """
    Retrieves proxy configuration details from environment variables.
    """
    load_dotenv()
    formatted_index = str(number)

    return {
        'username': PROXIES.proxy_profiles[formatted_index]["username"],
        'password': PROXIES.proxy_profiles[formatted_index]["password"],
        'endpoint': PROXIES.proxy_profiles[formatted_index]["proxy_address"],
        'port': PROXIES.proxy_profiles[formatted_index]["port"]
    }

def get_os_chrome_version(operating_system):
    if operating_system == "macOS":
        return "128.0.6613.119"
    else:  # Linux
        return "126.0.6478.114"
    
def is_macos_or_linux():
    system = platform.system().lower()
    
    if system == "darwin":
        return "macOS"
    
    elif system == "linux":
        return "Linux"
    
    elif system == "":
        # Some Linux distributions might return an empty string
        # Check for common Linux-specific directories
        return "Linux" if os.path.isdir("/etc/") and os.path.isdir("/proc/") else None
    
    else:
        # Additional check for Linux using os.uname()
        try:
            uname = os.uname()
            if uname.sysname.lower() == "linux":
                return "Linux"
        except AttributeError:
            # os.uname() is not available on Windows
            pass
    
    return None