import os, time, re
import utils.utils as utils
import constants as CONSTANTS
from dotenv import load_dotenv
from db.supabase import Supabase
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from error_logging.error_logging import ErrorLogging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

class ScrapeSong:
    def __init__(self, driver):
        self.driver = driver
        self.supabase = Supabase()
        load_dotenv()  # Load environment variables once during initialization

    def scrape_song(self, start_time, song_creation_data, downloads_dir):
        """Main method to scrape a song."""
        if not song_creation_data or not downloads_dir:
            print("SCRAPE_SONG: Invalid song creation data or downloads directory.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Invalid song creation data or downloads directory.")
            return False

        try:
            use_instrumental, use_custom_mode = self.supabase.get_creation_modes()

            if use_instrumental == None or use_custom_mode == None:
                print("SCRAPE_SONG: Could not fetch the song creation modes.")
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not fetch the song creation modes.")
                return False

            switch_to_correct_creation_mode = self.switch_to_correct_creation_mode(use_instrumental, use_custom_mode)
            if not switch_to_correct_creation_mode:
                print("SCRAPE_SONG: Could not switch to the correct creation mode.")
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not switch to the correct creation mode.")
                return False

            create_song_elements = self.get_main_ui_elements(use_instrumental, use_custom_mode)
            if not create_song_elements:
                print("SCRAPE_SONG: Could not find the main UI elements on the Create page.")
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not find the main UI elements on the Create page.")
                return False
            
            print("SCRAPE_SONG: Found the main UI elements.")
            
            # Get rid of the intro tutorial on the Create page
            dismiss_tutorial_result = self.dismiss_intro_tutorial()
            if not dismiss_tutorial_result:
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not dismiss the intro tutorial.")
                return False

            print("SCRAPE_SONG: Got rid of the Suno tutorial popup.")

            main_text_field = ""
            if not use_custom_mode:
                main_text_field = create_song_elements["song_description_field"]
                create_song_elements["song_description_field"].click()
            else:
                if not use_instrumental: 
                    main_text_field = create_song_elements["custom_lyrics_field"]
                    create_song_elements["custom_lyrics_field"].click()
                else: 
                    main_text_field = create_song_elements["custom_genre_field"]
                    create_song_elements["custom_genre_field"].click()
            utils.random_micro_sleep()

            if not self.still_have_time(start_time):
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Did not have any more time after getting rid of the Suno tutorial popup.")
                return False
            
            if not self.delete_invalid_songs(main_text_field):
                print("SCRAPE_SONG: Could not delete invalid and pending songs before creating a new one.")
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not delete invalid and pending songs before creating a new one.")
                return False
            
            print("SCRAPE_SONG: Deleted any invalid and pending songs.")
            
            if not self.still_have_time(start_time):
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Did not have any more time after deleting any invalid or pending songs prior to creating a song.")
                return False
            
            return self.fetch_song(start_time, create_song_elements, song_creation_data, downloads_dir, main_text_field, use_instrumental, use_custom_mode)
        except Exception as e:
            print(f"SCRAPE_SONG: Unexpected error encountered while scraping the song. Details: {e}")
            return False
    
    def switch_to_correct_creation_mode(self, use_instrumental, use_custom_mode):
        """Switch to custom more or instrumental only, depending on the settings chosen by the user."""
        print("SCRAPE_SONG: Getting the song creation settings...")
        current_instrumental_setting = self.get_current_instrumental_setting()
        current_mode_setting = self.get_current_custom_mode_setting()

        if current_instrumental_setting == None or current_mode_setting == None:
            print("SCRAPE_SONG: Could not find the current instrumental or mode settings.")
            return False
        
        print("SCRAPE_SONG: Start to switch to the correct settings...")
        if current_instrumental_setting != use_instrumental:
            instrumental_button = (CONSTANTS.SUNO_INSTRUMENTAL_ENABLED_BUTTON if 
                                   current_instrumental_setting == True else 
                                   CONSTANTS.SUNO_INSTRUMENTAL_DISABLED_BUTTON)
            
            clicked_button = self.click_button(instrumental_button)
            if not clicked_button: 
                print("SCRAPE_SONG: Could not click the current instrumental mode button.")
                return False
            
            print("SCRAPE_SONG: Toggled instrumental on/off.")

        if current_mode_setting != use_custom_mode:
            mode_button = (CONSTANTS.SUNO_CUSTOM_SONG_ENABLED_BUTTON if 
                           current_mode_setting == True else 
                           CONSTANTS.SUNO_CUSTOM_SONG_DISABLED_BUTTON)
            
            clicked_button = self.click_button(mode_button)
            if not clicked_button: 
                print("SCRAPE_SONG: Could not click the current song creation mode button.")
                return False
            
            print("SCRAPE_SONG: Toggled custom mode on/off.")

            dismiss_custom_mode_intro_flow = self.dismiss_entire_custom_mode_intro_flow()
            if not dismiss_custom_mode_intro_flow:
                print("SCRAPE_SONG: Could not dismiss the custom mode intro flow.")
                return False
            
        return True

    def get_current_instrumental_setting(self):
        """Get the current instrumental setting from the UI."""
        print("SCRAPE_SONG: Getting the current instrumental setting...")
        enabled_instrumental = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_INSTRUMENTAL_ENABLED_BUTTON)
        disabled_instrumental = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_INSTRUMENTAL_DISABLED_BUTTON)

        if (not enabled_instrumental and not disabled_instrumental) or (enabled_instrumental and disabled_instrumental):
            return None

        if enabled_instrumental and not disabled_instrumental:
            return True
        
        return False
    
    def get_current_custom_mode_setting(self):
        """Get the current custom mode setting from the UI."""
        print("SCRAPE_SONG: Getting the current custom mode setting...")
        enabled_custom = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_CUSTOM_SONG_ENABLED_BUTTON)
        disabled_custom = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_CUSTOM_SONG_DISABLED_BUTTON)

        if (not enabled_custom and not disabled_custom) or (enabled_custom and disabled_custom):
            return None
        
        if enabled_custom and not disabled_custom:
            return True
        
        return False
    
    def click_button(self, button_id):
        """Click a designated button."""
        button = self.find_one_in_page(By.XPATH, button_id)
        if not button:
            return False
        
        button.click()
        utils.random_short_sleep()
        print("SCRAPE_SONG: Clicked a button")
        return True

    def dismiss_intro_tutorial(self):
        """Dismiss the intro tutorial for Suno."""
        tutorial_overlay = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_TUTORIAL_OVERLAY)
        if not tutorial_overlay:
            return True

        tutorial_overlay.click()
        utils.random_micro_sleep()
        return True

    def get_main_ui_elements(self, use_instrumental, use_custom_mode):
        """Retrieve main UI elements for song creation."""
        elements = {
            "model_list_toggle": self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_MODEL_VERSION_SPAN),
            "create_action_button": self.find_one_in_page(By.XPATH, CONSTANTS.CREATE_SCREEN_CREATE_BUTTON)
        }

        if not use_custom_mode:
            elements["song_description_field"] = self.find_one_in_page(By.XPATH, CONSTANTS.SONG_DESCRIPTION_INPUT_FIELD)
        else:
            elements["custom_genre_field"] = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_CUSTOM_GENRE_INPUT_FIELD)
            elements["custom_title_field"] = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_CUSTOM_TITLE_INPUT_FIELD)

            if not use_instrumental:
                elements["custom_lyrics_field"] = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_CUSTOM_LYRICS_INPUT_FIELD)

        return elements if all(elements.values()) else None

    def fetch_song(self, start_time, create_song_elements, song_creation_data, downloads_dir, main_text_field, use_instrumental, use_custom_mode):
        """Create a song based on the song creation data."""
        picked_correct_model = False

        for _ in range(3):
            if self.pick_suno_model(create_song_elements["model_list_toggle"]):
                picked_correct_model = True
                break
            else:
                utils.random_short_sleep
        
        if not picked_correct_model:
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not pick the desired Suno model.")
            return False

        print("SCRAPE_SONG: Trying to start the song creation process...")
        if not use_custom_mode:
            create_song_elements["song_description_field"].click()
            utils.random_micro_sleep()
            create_song_elements["song_description_field"].clear()
            create_song_elements["song_description_field"].send_keys(song_creation_data["song_prompt"])
            utils.random_micro_sleep()
        else:
            if not use_instrumental:
                create_song_elements["custom_lyrics_field"].click()
                utils.random_micro_sleep()
                create_song_elements["custom_lyrics_field"].clear()
                create_song_elements["custom_lyrics_field"].send_keys(song_creation_data["song_input_custom_lyrics"])
                utils.random_short_sleep()

            create_song_elements["custom_genre_field"].click()
            utils.random_micro_sleep()
            create_song_elements["custom_genre_field"].clear()
            create_song_elements["custom_genre_field"].send_keys(
                self.create_custom_genre_prompt(song_creation_data["song_input_genre"], song_creation_data["second_song_input_genre"], song_creation_data["song_input_vibe"])
            )
            utils.random_short_sleep()

            create_song_elements["custom_title_field"].click()
            utils.random_micro_sleep()
            create_song_elements["custom_title_field"].clear()
            create_song_elements["custom_title_field"].send_keys(song_creation_data["song_input_custom_title"])
            utils.random_micro_sleep()

        if not self.still_have_time(start_time):
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Did not have any more time after entering the song description.")
            return False

        create_song_elements["create_action_button"].click()

        print("SCRAPE_SONG: Waiting for the songs to initialize...")
        utils.sleep_custom(CONSTANTS.TIME_SLEPT_WHILE_SONGS_INITIALIZE)
        song_list = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_CREATE_SONG_LIST)
        if not song_list:
            utils.random_normal_sleep()
            song_list = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_CREATE_SONG_LIST)
        if not song_list:
            print("SCRAPE_SONG: Could not find the song list after sending a song generation request.")
            self.get_and_save_leftover_credit_amount()
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not find the song list after sending a song generation request.")
            return False

        target_song = None
        if self.still_have_time(start_time - CONSTANTS.MAX_SONG_CREATION_WAIT_TIME):
            target_song = self.pick_first_finished_song()
        else:
            print("SCRAPE_SONG: Not enough time left to wait for song creation.")
            self.get_and_save_leftover_credit_amount()
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Not enough time left to wait for song creation.")
            return False

        if not target_song:
            print(f"SCRAPE_SONG: Could not find a song even after waiting for {CONSTANTS.MAX_SONG_CREATION_WAIT_TIME} seconds.")
            if not self.delete_invalid_songs(main_text_field):
                print("SCRAPE_SONG: Could not delete created songs before exiting.")
            return False
        
        suno_song_title, suno_song_genre = self.get_song_title_and_genre(target_song)
        if not suno_song_title or not suno_song_genre:
            print("SCRAPE_SONG: Exiting because I couldn't fetch the song title or genre.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Exiting because I couldn't fetch the song title or genre.")
            return False
        
        print(f"SCRAPE_SONG: The target song title is '{suno_song_title}' and the song genre is '{suno_song_genre}'.")

        get_leftover_credit_result = self.get_and_save_leftover_credit_amount()
        if not get_leftover_credit_result:
            print("SCRAPE_SONG: Failed to get the leftover Suno credits and save them on Supabase.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Failed to get the leftover Suno credits and save them on Supabase.")
            return False

        if not self.still_have_time(start_time):
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Did not have any more time after fetching the song title and genre.")
            return False

        print("SCRAPE_SONG: Trying to download the song...")
        downloaded_song_path = self.download_song_audio(target_song, downloads_dir)
        if not downloaded_song_path:
            print("SCRAPE_SONG: Could not download the song.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not download the song.")
            return False

        print(f"SCRAPE_SONG: Successfully downloaded the song and stored it at {downloaded_song_path}.")

        suno_song_lyrics = ""
        if not use_instrumental and not use_custom_mode:
            if not self.go_to_song_details_screen(target_song):
                print(f"SCRAPE_SONG: Have to abort given that I'm not on the song details page.")
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Have to abort given that I'm not on the song details page.")
                return False
            
            print("SCRAPE_SONG: Landed on the song details page.")

            if not self.still_have_time(start_time):
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Did not have any more time after landing on the song details page.")
                return False

            suno_song_lyrics = self.get_lyrics()
            if not suno_song_lyrics:
                print("SCRAPE_SONG: Exiting early because the song lyrics are invalid or couldn't be found.")
                ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Exiting early because the song lyrics are invalid or couldn't be found.")
                return False
        else:
            if use_instrumental: suno_song_lyrics = "[Instrumental]"
            else: suno_song_lyrics = song_creation_data["song_input_custom_lyrics"]

        print("SCRAPE_SONG: The song lyrics are:\n\n" + str(suno_song_lyrics) + "\n")

        if not self.supabase.save_song_data(suno_song_title, suno_song_genre, suno_song_lyrics, downloaded_song_path):
            print("SCRAPE_SONG: Could not save the song data on Supabase.")
            ErrorLogging().save_error_and_send_email("SCRAPER - SCRAPE_SONG: Could not save the song data on Supabase.")
            return False

        return True
    
    def dismiss_entire_custom_mode_intro_flow(self):
        """Click on the right buttons to dismiss the popups you get when you first try custom mode."""
        dismissed_custom_mode_get_started_popup = self.dismiss_get_started_custom_mode()
        if not dismissed_custom_mode_get_started_popup:
            print("SCRAPE_SONG: Could not dismiss the custom mode get started popup.")
            return False
        
        accept_custom_mode_terms = self.accept_custom_mode_terms()
        if not accept_custom_mode_terms:
            print("SCRAPE_SONG: Could not accept the custom mode terms.")
            return False
        
        return True

    def dismiss_get_started_custom_mode(self):
        """Dismiss the get started popup for the custom mode."""
        dismiss_get_started = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_CUSTOM_MODE_GET_STARTED_BUTTON)
        if not dismiss_get_started:
            return True
        
        dismiss_get_started.click()
        utils.random_micro_sleep()
        utils.random_micro_sleep()

        return True

    def accept_custom_mode_terms(self):
        """Accept the custom mode terms."""
        custom_mode_accept_btn = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_ACCEPT_CUSTOM_SONG_TERMS_BUTTON)
        if not custom_mode_accept_btn:
            return True
        
        custom_mode_accept_btn.click()
        utils.random_micro_sleep()
        utils.random_micro_sleep()

        return True

    def create_custom_genre_prompt(self, first_genre, second_genre, vibe):
        """Create a genre when in custom mode."""
        if ((not first_genre and not second_genre and not vibe) or (first_genre == "" and second_genre == "" and vibe == "")):
            return None
        
        custom_genre_prompt = ""
        if (vibe and vibe != None and vibe != "" and vibe != "none"): custom_genre_prompt += vibe + " "
        if (first_genre and 
            first_genre != None and 
            first_genre != "" and 
            first_genre != "none"): custom_genre_prompt += first_genre + " "
        if (second_genre and 
            second_genre != None and 
            second_genre != "" and 
            second_genre != "none" and 
            second_genre.lower() != first_genre.lower()): custom_genre_prompt += second_genre + " "

        return custom_genre_prompt

    def pick_suno_model(self, current_model_span):
        """Pick the desired Suno model."""
        if current_model_span.text == CONSTANTS.SUNO_DESIRED_MODELS[0]:
            return True
        
        print("SCRAPE_SUNO: Trying to pick the desired Suno model...")

        dismiss_custom_mode_intro_flow = self.dismiss_entire_custom_mode_intro_flow()
        if not dismiss_custom_mode_intro_flow:
            print("SCRAPE_SONG: Could not dismiss the custom mode intro flow.")
            return False

        current_model_span.click()
        utils.random_short_sleep()

        suno_model_options = self.find_many_in_page(By.XPATH, CONSTANTS.SUNO_MODEL_LIST_VERSION_DIV)
        if not suno_model_options:
            print("SCRAPE_SONG: Could not find the array of Suno models.")
            return False

        for desired_model in CONSTANTS.SUNO_DESIRED_MODELS:
            for option in suno_model_options:
                if desired_model == option.text:
                    print(f"SCRAPE_SONG: Selecting the {desired_model} Suno model...")
                    option.click()
                    utils.random_micro_sleep()
                    return True

        print("SCRAPE_SONG: None of the desired Suno models were found.")
        return False

    def pick_first_finished_song(self):
        """Pick the first finished song from the list."""
        print("SCRAPE_SONG: Waiting for songs to generate and picking the first finished one...")
        all_songs = self.find_many_in_page(By.XPATH, CONSTANTS.SUNO_SONG_ELEMENT)
        if not all_songs:
            utils.random_short_sleep()
            all_songs = self.find_many_in_page(By.XPATH, CONSTANTS.SUNO_SONG_ELEMENT)

        if not all_songs:
            ErrorLogging().save_error_and_send_email(f"SCRAPER - SCRAPE_SONG: Could not find any songs in the song list.")
            return None

        unfinished_songs = [song for song in all_songs if not self.get_song_duration(self.find_element_in_element(song, By.XPATH, "." + CONSTANTS.SONG_DURATION_SPAN))]

        if not 0 < len(unfinished_songs) <= CONSTANTS.SUNO_MAX_SONGS_PER_GENERATION:
            if len(unfinished_songs) == 0:
                utils.random_short_sleep()
                unfinished_songs = [song for song in all_songs if not self.get_song_duration(self.find_element_in_element(song, By.XPATH, "." + CONSTANTS.SONG_DURATION_SPAN))]
            
        if not 0 < len(unfinished_songs) <= CONSTANTS.SUNO_MAX_SONGS_PER_GENERATION:
            print(f"SCRAPE_SONG: Invalid number of unfinished songs: {len(unfinished_songs)}")
            ErrorLogging().save_generation_error_and_send_email(f"SCRAPER - SCRAPE_SONG: Invalid number of unfinished songs: {len(unfinished_songs)}.")
            return None
        
        print(f"SCRAPE_SONG: The length of the unfinished_songs array is {len(unfinished_songs)}.")

        max_duration = 0
        target_song = None

        start_time = time.time()
        end_time = start_time + CONSTANTS.MAX_SONG_CREATION_WAIT_TIME

        all_songs_done_generating = True

        while time.time() < end_time:
            all_songs_done_generating = True
            for song in unfinished_songs:
                song_duration_span = self.find_element_in_element(song, By.XPATH, "." + CONSTANTS.SONG_DURATION_SPAN)
                if not song_duration_span:
                    all_songs_done_generating = False
                    continue

                song_duration_seconds = self.get_song_duration(song_duration_span)
                if song_duration_seconds and song_duration_seconds > max_duration and song_duration_seconds >= CONSTANTS.MIN_SONG_LENGTH:
                    max_duration = song_duration_seconds
                    target_song = song
                elif not song_duration_seconds:
                    all_songs_done_generating = False

            print(f"SCRAPE_SONG: Max song duration is {max_duration}.")

            if all_songs_done_generating:
                break

            utils.sleep_custom(CONSTANTS.SONG_CREATION_SLEEP_TIME)

        if target_song and max_duration > 0:
            print(f"SCRAPE_SONG: Picked a song that's {max_duration} seconds in length. Took {time.time() - start_time} seconds to find the song.")
        else:
            ErrorLogging().save_generation_error_and_send_email(f"SCRAPER - SCRAPE_SONG: Did not find a suitable song.")

        return target_song

    def get_song_duration(self, song_duration_span):
        """Get the duration of a song in seconds."""
        if not song_duration_span:
            return None

        try:
            duration = song_duration_span.text
            if duration and \
               len(duration) <= CONSTANTS.SUNO_SONG_DURATION_STRING_LENGTH and \
               duration != CONSTANTS.UNFINISHED_SONG_LENGTH_PLACEHOLDER and \
               self.is_valid_time_format(duration):
                return self.time_to_seconds(duration)
        except Exception as e:
            print(f"SCRAPE_SONG: Got an error while trying to get a song duration: {e}")
        return None

    def get_song_title_and_genre(self, target_song):
        """Get the title and genre of a song."""
        if not target_song:
            return (None, None)

        try:
            title_span = self.find_element_in_element(target_song, By.XPATH, "." + CONSTANTS.CREATE_SCREEN_SONG_TITLE_SPAN)
            genre_a = self.find_element_in_element(target_song, By.XPATH, "." + CONSTANTS.CREATE_SCREEN_SONG_GENRE)
            
            if not title_span or not title_span.text or "Loading" in title_span.text or \
               not genre_a or not genre_a.text or "Loading" in genre_a.text:
                return (None, None)
    
            return (title_span.text, genre_a.text)
        except Exception as e:
            print(f"SCRAPE_SONG: Could not fetch the title and/or the genre of the target song. Details: {e}")
            return (None, None)

    def get_lyrics(self):
        """Get the lyrics of a song."""
        if not self.driver.current_url.startswith(CONSTANTS.SONG_DETAILS_URL):
            utils.sleep_custom(CONSTANTS.EXTRA_SONG_DETAILS_PAGE_WAIT_TIME)

        lyrics_text_area = self.find_one_in_page(By.XPATH, CONSTANTS.SONG_SCREEN_LYRICS_TEXT_AREA)
        if not lyrics_text_area or not self.driver.current_url.startswith(CONSTANTS.SONG_DETAILS_URL):
            print("SCRAPE_SONG: Could not find the lyrics text area.")
            return None
        
        song_lyrics = lyrics_text_area.text
        if not song_lyrics or len(song_lyrics) < CONSTANTS.MIN_LYRICS_LENGTH:
            print("SCRAPE_SONG: Invalid song lyrics.")
            return None
        
        return song_lyrics
        
    def go_to_song_details_screen(self, target_song, max_retries=5):
        """Navigate to the song details screen with retries and full page load check."""
        if not target_song:
            print("SCRAPE_SONG: Null target song provided to go_to_song_details_screen.")
            return False
        
        try:
            title_span = self.find_element_in_element(target_song, By.XPATH, "." + CONSTANTS.CREATE_SCREEN_SONG_TITLE_SPAN)
            if not title_span:
                print("SCRAPE_SONG: Could not find the target song's title span.")
                return False
            
            print("SCRAPE_SONG: Clicking on the song title span...")
            title_span.click()
            utils.random_micro_sleep()
        except Exception as e:
            print(f"SCRAPE_SONG: Could not click on the song title to go to the details page. Details: {e}")
            return False

        for attempt in range(max_retries):
            try:                
                # Wait for the page to load
                if self.wait_for_page_load():
                    print("SCRAPE_SONG: Loading the song detail page worked")
                    if self.driver.current_url.startswith(CONSTANTS.SONG_DETAILS_URL):
                        print("SCRAPE_SONG: The page URL is correct!")
                        return True
                    print("SCRAPE_SONG: The page URL is incorrect")
                    return False
                
                print(f"SCRAPE_SONG: Attempt {attempt + 1} failed. Reloading page...")
                self.driver.refresh()
                utils.random_short_sleep()
            except Exception as e:
                print(f"SCRAPE_SONG: Error during attempt {attempt + 1}. Details: {e}")
    
        print(f"SCRAPE_SONG: Failed to go to song details after {max_retries} attempts.")
        return False

    def wait_for_page_load(self, timeout=CONSTANTS.TIME_SLEPT_STEP_GOING_TO_SONG_DETAILS):
        """Wait for the page to fully load and have the correct URL."""
        try:           
            # Wait for the DOM to be ready
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            return True
        except TimeoutException:
            return False

    def download_song_audio(self, target_song, downloads_dir):
        """Download the audio of a song."""
        if not target_song: 
            print("SCRAPE_SONG: Null target song passed to the download method.")
            return None
        menu_toggle = self.find_element_in_element(target_song, By.XPATH, "." + CONSTANTS.SONG_MENU_TOGGLE_BUTTON)
        if not menu_toggle:
            print("SCRAPE_SONG: Could not find the target song menu toggle inside the download method.")
            return None
        
        menu_toggle.click()
        utils.random_short_sleep()

        download_option = self.find_one_in_page(By.XPATH, CONSTANTS.SONG_DOWNLOAD_BUTTON)
        if not download_option:
            print("SCRAPE_SONG: Could not find the download button for the song.")
            return None
        
        download_option.click()
        utils.random_short_sleep()

        audio_option = self.find_one_in_page(By.XPATH, CONSTANTS.SONG_MP3_DOWNLOAD_OPTION)
        if not audio_option:
            print("SCRAPE_SONG: Found too many or not enough audio download options for the song.")
            return None

        # Focus on the audio option div
        self.driver.execute_script("var event = new MouseEvent('mouseover', {'bubbles': true, 'cancelable': true}); arguments[0].dispatchEvent(event);", audio_option)
        utils.random_micro_sleep()

        # Now try to click
        audio_option.send_keys(Keys.ENTER)
        utils.random_short_sleep()

        # Wait for the download to end
        end_time = time.time() + CONSTANTS.MAX_SONG_DOWNLOAD_WAIT_TIME
        while time.time() < end_time:
            downloaded_song_path = self.get_song_name_from_directory(downloads_dir)
            if downloaded_song_path == None:
                return None
            elif downloaded_song_path == False:
                utils.sleep_custom(CONSTANTS.SONG_DOWNLOAD_STEP_WAIT_TIME)
            else:
                return os.path.join(downloads_dir, downloaded_song_path)

        return None

    def get_and_save_leftover_credit_amount(self):
        """Fetch and save the remaining credit amount."""
        print("SCRAPE_SONG: Fetching and saving the latest number of credits...")
        remaining_credits_number = self.get_leftover_credit_amount()
        if not remaining_credits_number:
            print(f"SCRAPE_SONG: Got an error fetching the credits number for {os.getenv('PHONE_NUMBER')}.")
            return False
        
        if int(remaining_credits_number) <= CONSTANTS.MIN_SUNO_CREDIT_BALANCE:
            ErrorLogging().send_email("SCRAPER - SCRAPE_SONG: This account's Suno credit balance is at or below the minimum. Please top up the account soon.")

        print(f"SCRAPE_SONG: Saving the latest number of credits for {os.getenv('PHONE_NUMBER')} in the scraper_stats table...")
        self.supabase.update_credit_number(remaining_credits_number)
        return True

    def get_leftover_credit_amount(self):
        """Get the remaining credit amount."""
        try:
            leftover_credits_span = self.find_one_in_page(By.XPATH, CONSTANTS.SUNO_ACCOUNT_LEFTOVER_CREDITS)
            if not leftover_credits_span or not leftover_credits_span.text or not self.is_valid_credits_text(leftover_credits_span.text):
                return None
            
            return self.extract_credit_number(leftover_credits_span.text)
        except Exception as e:
            print(f"SCRAPE_SONG: {e}")
            return None

    def delete_invalid_songs(self, text_field):
        """Delete invalid songs from the list."""
        songs = self.find_many_in_page(By.XPATH, CONSTANTS.SUNO_SONG_ELEMENT)
        if not songs:
            return True

        song_menu_toggles = []
        for song in songs:
            song_duration_span = self.find_element_in_element(song, By.XPATH, "." + CONSTANTS.SONG_DURATION_SPAN)
            if not self.get_song_duration(song_duration_span):
                menu_toggle = self.find_element_in_element(song, By.XPATH, "." + CONSTANTS.SONG_MENU_TOGGLE_BUTTON)
                if not menu_toggle:
                    print("SCRAPE_SONG: Could not find a song's menu toggle.")
                    return False
                song_menu_toggles.append(menu_toggle)
        
        if not song_menu_toggles:
            return True

        deleted_songs = 0
        for menu_toggle in song_menu_toggles:
            if deleted_songs >= CONSTANTS.MAX_SONGS_TO_DELETE: 
                print("SCRAPE_SONG: There are too many songs to delete.")
                return False
            
            menu_toggle.click()
            utils.random_micro_sleep()

            song_options_menu = self.find_one_in_page(By.XPATH, CONSTANTS.SONG_OPTIONS_MENU)
            if not song_options_menu:
                print("SCRAPE_SONG: Couldn't find a song's menu so that I can delete it.")
                return False

            song_delete_button = self.find_element_in_element(song_options_menu, By.XPATH, "." + CONSTANTS.SONG_AUDIO_DELETE)
            if not song_delete_button:
                print("SCRAPE_SONG: Couldn't find a song's delete button.")
                return False
            
            song_delete_button.click()
            utils.random_micro_sleep()
            text_field.click()
            utils.random_micro_sleep()
            deleted_songs += 1

        return True

    def still_have_time(self, start_time):
        """Check if there's still time left in the scraping process."""
        return int(time.time()) - start_time < int(os.getenv('MAX_RUNTIME', CONSTANTS.RUNTIME_ERROR_MARGIN)) - CONSTANTS.RUNTIME_ERROR_MARGIN

    def is_valid_time_format(self, time_string):
        """Check if the time string is in a valid format."""
        pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        return bool(re.match(pattern, time_string))
    
    def is_valid_credits_text(self, text):
        """Check if the credits text is in a valid format."""
        if not text:
            return False

        pattern = re.compile(r"^(?:0|[1-9]\d{0,4}(?:,\d{3})?|50,?000) Credits$", re.IGNORECASE)
        match = pattern.match(text)

        if match:
            numeric_part = match.group().split()[0].replace(',', '')
            return 0 <= int(numeric_part) <= CONSTANTS.MAX_CREDITS_NUMBER

        return False
    
    def extract_credit_number(self, text):
        """Extract the credit number from the text."""
        if not text:
            raise Exception("Null text passed to extract the credits number from.")

        pattern = re.compile(r"^(\d{1,3}(?:,\d{3})*|\d+)\s*Credits$", re.IGNORECASE)
        match = pattern.match(text)
        
        if match:
            number_str = match.group(1).replace(',', '')
            number = int(number_str)
            
            if 0 <= number <= CONSTANTS.MAX_CREDITS_NUMBER:
                return number
            else:
                raise ValueError(f"SCRAPE_SONG: Credits number is out of the valid range (0-{CONSTANTS.MAX_CREDITS_NUMBER}).")
        else:
            raise ValueError("SCRAPE_SONG: No valid credits number found.")
        
    def get_song_name_from_directory(self, directory_path):
        """Get the name of the downloaded song from the directory."""
        if not os.path.isdir(directory_path):
            print(f"SCRAPE_SONG: The song downloads directory {directory_path} does not exist.")
            return None

        files = [item for item in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, item))]

        if len(files) == 1:
            print("SCRAPE_SONG: Found a file in the song downloads dir. Checking its extension...")

            file_path = os.path.join(directory_path, files[0])
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension in CONSTANTS.ACCEPTED_SONG_FILE_TYPES:
                print(f"SCRAPE_SONG: The downloaded song has a valid extension.")
                return files[0]
            
            print("SCRAPE_SONG: The downloaded song has an invalid extension.")
            return None
        elif len(files) == 0:
            print("SCRAPE_SONG: The song downloads directory is empty.")
            return False
        else:
            print(f"SCRAPE_SONG: There are too many files in the song downloads dir.")
            return None
    
    def time_to_seconds(self, time_str):
        """Convert time string to seconds."""
        minutes, seconds = map(int, time_str.split(':'))
        return minutes * 60 + seconds

    def find_one_in_page(self, by_method, identifier):
        """Find a single element on the page."""
        elements = self.driver.find_elements(by_method, identifier)
        return elements[0] if len(elements) == 1 else None
    
    def find_element_in_element(self, ui_element, by_method, identifier):
        """Find a single element within another element."""
        elements = ui_element.find_elements(by_method, identifier)
        return elements[0] if len(elements) == 1 else None
    
    def find_many_in_page(self, by_method, identifier):
        """Find multiple elements on the page."""
        elements = self.driver.find_elements(by_method, identifier)
        return elements if len(elements) > 0 else None