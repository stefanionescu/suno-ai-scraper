# URLs and Endpoint Definitions
BASE_URL = "https://suno.com/create"
SIGN_IN_URL = "https://accounts.suno.com/sign-in"
SONG_DETAILS_URL = "https://suno.com/song/"

# XPaths for Dynamic Elements on Pages
COUNTRY_CODE_BUTTON_SIGN_IN = "//button[contains(@class, 'cl-selectButton')]"
COUNTRY_CODE_SEARCH_FIELD_SIGN_IN = "//input[@placeholder='Search country or code']"
COUNTRY_CODE_LIST_ELEMENT_SIGN_IN = "//div[contains(@class, 'cl-selectOption__countryCode')]"

NUMBER_INPUT_FIELD = "//input[@maxlength='25' and @type='tel']"
CONTINUE_BUTTON_SIGN_IN = "//button[text()='Continue']"
SIGN_IN_CODE_FIRST_DIGIT = "//input[@aria-label='Enter verification code.  Digit 1']"
INCORRECT_CODE_NOTICE_SIGN_IN = "//p[text()='Incorrect code']"
RESEND_CODE_BUTTON_SIGN_IN = "//button[contains(text(), 'Resend')]"

SUNO_ACCOUNT_LEFTOVER_CREDITS = "//a[@href='/account']//div//div//div[contains(translate(., 'CREDITS', 'credits'), 'credits')]"
SONG_DESCRIPTION_INPUT_FIELD = "//textarea[@maxlength and number(@maxlength) >= 180]"
SUNO_MODEL_VERSION_SPAN = "//div[@aria-label='Model Select Dropdown']//span"
SUNO_MODEL_LIST_VERSION_DIV = "//div[contains(@aria-label, 'Model Selection:')]//div/div[1]"
SUNO_CREATE_SONG_LIST = "//div[@role='grid']"
SUNO_SONG_ELEMENT = "//div[@data-testid='song-row']"
SONG_DURATION_SPAN = "//div[@data-testid='song-row-play-button']//div//span"
SONG_MENU_TOGGLE_BUTTON = "//button[@type='button' and @data-state='closed']"
SONG_DOWNLOAD_BUTTON = "//div[@role='menuitem' and text()='Download']"
SONG_MP3_DOWNLOAD_OPTION = "//div[@data-testid='download-audio-menu-item' and @role='menuitem']"
SONG_AUDIO_DELETE = "//div[@role='menuitem']//div//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'trash')]"
SONG_OPTIONS_MENU = "//div[@role='menu' and @data-state='open']"
CREATE_SCREEN_SONG_TITLE_SPAN = "//span[@title and normalize-space(@title) != '']//a//span"
CREATE_SCREEN_SONG_GENRE = "//span[@title and normalize-space(@title) != '']//a[contains(@class, 'hover:underline')]"
SONG_SCREEN_LYRICS_TEXT_AREA = "//section//div//textarea"
CREATE_SCREEN_CREATE_BUTTON = "//button/div/span[text()='Create']"
SUNO_TUTORIAL_OVERLAY = "//div[@data-test-id='overlay' and @role='presentation']"

SUNO_CUSTOM_MODE_GET_STARTED_BUTTON = "//button[contains(translate(text(), 'GETSTARTED', 'getstarted'), 'get started')]"
SUNO_ACCEPT_CUSTOM_SONG_TERMS_BUTTON = "//button[@aria-label='' and contains(translate(span, 'IACCEPT', 'iaccept'), 'i accept')]"
SUNO_CUSTOM_SONG_DISABLED_BUTTON = "//div[@aria-label='Custom' and contains(@class, 'bg-tertiary')][.//span[not(contains(@class, 'translate-x-4'))]]"
SUNO_CUSTOM_SONG_ENABLED_BUTTON = "//div[@aria-label='Custom' and contains(@class, 'bg-primary')][.//span[contains(@class, 'translate-x-4')]]"
SUNO_INSTRUMENTAL_DISABLED_BUTTON = "//div[@aria-label='Instrumental' and contains(@class, 'bg-tertiary')][.//span[not(contains(@class, 'translate-x-4'))]]"
SUNO_INSTRUMENTAL_ENABLED_BUTTON = "//div[@aria-label='Instrumental' and contains(@class, 'bg-primary')][.//span[contains(@class, 'translate-x-4')]]"
SUNO_CUSTOM_LYRICS_INPUT_FIELD = "//textarea[@maxlength > 1000 and contains(translate(@placeholder, 'LYRICS', 'lyrics'), 'lyrics')]"
SUNO_CUSTOM_GENRE_INPUT_FIELD = "//textarea[@maxlength > 100 and @maxlength < 1000 and contains(translate(@placeholder, 'STYLE', 'style'), 'style')]"
SUNO_CUSTOM_TITLE_INPUT_FIELD = "//textarea[@maxlength > 10 and @maxlength < 100 and contains(translate(@placeholder, 'TITLE', 'title'), 'title')]"

# Text for Static Elements on Pages
SIGN_IN_TITLE = "Sign in"
SIGN_IN_CHECK_PHONE = "Check your phone"

# Scraping Params
CHROME_PROFILES_DIR_PATH = "./aws/chrome_profiles/"
DOWNLOADS_DIR_PATH = "./scrape_song/downloaded_songs"
HEADERS_MACOS = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.119 Safari/537.36"
HEADERS_LINUX = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.114 Safari/537.36"
ACCEPTED_SONG_FILE_TYPES = ['.mp3', '.wav', '.mpeg']

# Bot Limitations
RUNTIME_ERROR_MARGIN = 100
MIN_SUNO_CREDIT_BALANCE = 50
MIN_RUNTIME = 420 # 7 minutes
MAX_RUNTIME = 840 # 14 minutes
MAX_SONGS_TO_DELETE = 4
MAX_GENERATION_ID_LENGTH = 50
PAGE_LOAD_RETRY_SESSION = 20
MAX_PAGE_RELOAD_TRIES = 3
PAGE_LOAD_TIMEOUT = 60

# SMS Params
SMS_MAX_TIME_DELTA_MINUTES = 3
MAX_SMS_TO_READ = 3
START_TIME_DELTA = 5 # minutes

# Error Handling
ERROR_EMAIL_TITLE = "Error from the Scraping Bot - Phone Number {phone_number}"

# Supabase params
MAX_JWT_LIFETIME = 120
SUPABASE_SCRAPER_ROLE = "suno_scraper_role"
SUPABASE_SCHEMA = "backpack_bots"
SUPABASE_DISCORD_SONG_GENERATIONS_TABLE = "discord_song_generations"
SUPABASE_SCRAPER_STATUS_TABLE = "scraper_status"
SUPABASE_USERS_TABLE = "users"
SUPABASE_SONG_OUTPUT_AUDIO_BUCKET = "song-output-audio"

# Suno Params
MAX_CUSTOM_TITLE_LENGTH = 60
MIN_CUSTOM_LYRICS_LENGTH = 30
MAX_CUSTOM_LYRICS_LENGTH = 1000
SUNO_MAX_SONGS_PER_GENERATION = 2
MIN_PROMPT_LENGTH = 5
MAX_PROMPT_LENGTH = 190
MIN_GENRE_LENGTH = 3
TIME_SLEPT_WHILE_SONGS_INITIALIZE = 15
MAX_TIME_SLEPT_WHILE_GOING_TO_SONG_DETAILS = 40
TIME_SLEPT_STEP_GOING_TO_SONG_DETAILS = 15
MAX_SONG_CREATION_WAIT_TIME = 270
SONG_CREATION_SLEEP_TIME = 10
EXTRA_SONG_DETAILS_PAGE_WAIT_TIME = 15
MAX_SONG_DOWNLOAD_WAIT_TIME = 50
SONG_DOWNLOAD_STEP_WAIT_TIME = 5
MAX_CREDITS_NUMBER = 50000
MIN_LYRICS_LENGTH = 30
MIN_SONG_LENGTH = 14
SUNO_VERIFICATION_MESSAGE_IDENTIFIER = "Suno"
UNFINISHED_SONG_LENGTH_PLACEHOLDER = "--:--"
SUNO_SONG_DURATION_STRING_LENGTH = 5
SUNO_DESIRED_MODELS = ["v3.5", "v3", "v2"]

# Time Delays and Wait Periods
MICRO_MIN_SECONDS_TO_WAIT = 1
MICRO_MAX_SECONDS_TO_WAIT = 2
SHORT_MIN_SECONDS_TO_WAIT = 2
SHORT_MAX_SECONDS_TO_WAIT = 5
NORMAL_MIN_SECONDS_TO_WAIT = 15
NORMAL_MAX_SECONDS_TO_WAIT = 20
LONG_MIN_SECONDS_TO_WAIT = 25
LONG_MAX_SECONDS_TO_WAIT = 30
DEFAULT_IMPLICIT_WAIT = 5

# Word filtering
FORBIDDEN_WORDS = [
    "suno"
]

# Proxy Params
IP_CHECKER_URL = "http://ipecho.net/plain"
VALID_IPS = [
    "proxyiphere"
]