import os
import re
import jwt
import time
import json
import constants as CONSTANTS
from dotenv import load_dotenv
from unidecode import unidecode
from supabase import create_client, Client, ClientOptions

class Supabase:
    def __init__(self):
        load_dotenv()

    def stringify_if_json(self, obj):
        """Convert object to JSON string if possible, otherwise return as is."""
        if isinstance(obj, str):
            return obj
        try:
            return json.dumps(obj)
        except (TypeError, ValueError):
            return obj

    def generate_scraper_jwt(self):
        """Generate a JWT for Supabase authentication."""
        payload = {
            "aud": "authenticated",
            "role": "authenticated",
            "app_role": CONSTANTS.SUPABASE_SCRAPER_ROLE,
            "exp": int(time.time()) + CONSTANTS.MAX_JWT_LIFETIME
        }
        return jwt.encode(payload, os.getenv("SUPABASE_JWT_SECRET"), algorithm='HS256')

    def get_supabase_client(self, token):
        """Create and return a Supabase client."""
        options = ClientOptions(
            schema=CONSTANTS.SUPABASE_SCHEMA,
            headers={"Authorization": f"Bearer {token}"}
        )
        return create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY"),
            options
        )
    
    def is_valid_song_generation(self):
        """Check if the Supabase song generation entry is valid."""
        bearer_token = self.generate_scraper_jwt()
        client: Client = self.get_supabase_client(bearer_token)
        generation_id = os.getenv('GENERATION_ID')

        try:
            generation_response = client.table(CONSTANTS.SUPABASE_DISCORD_SONG_GENERATIONS_TABLE).select(
                "song_prompt, "
                "use_custom_mode, "
                "song_input_genre, "
                "use_instrumental_only, "
                "song_input_custom_lyrics, "
                "song_input_custom_title, "
                "error_message, "
                "user_id, "
                "replies_guild, "
                "initial_reply_id, "
                "output_song, "
                "output_reply_id, "
                "song_output_genre, "
                "song_output_title, "
                "song_output_lyrics, "
                "song_output_cover"
            ).eq("generation_id", generation_id).execute()
            
            if not generation_response.data:
                print('SUPABASE: Could not find the generation ID on Supabase.')
                return False
            
            generation_data = generation_response.data[0]

            # Check for various error conditions
            if generation_data["error_message"] is not None:
                print("SUPABASE: The song generation encountered an error before the scrape process started.")
                return False
            
            if generation_data["output_reply_id"] is None:
                print("SUPABASE: There's no output reply ID saved for this song generation.")
                return False
            
            if any(generation_data[field] is not None for field in ["song_output_genre", "song_output_title", "song_output_lyrics", "song_output_cover", "output_song"]):
                print("SUPABASE: The song generation already has output data.")
                return False
            
            if any(generation_data[field] is None for field in ["user_id", "replies_guild", "initial_reply_id"]):
                print("SUPABASE: There's no user ID, guild ID or initial reply ID saved for this song generation.")
                return False
            
            if generation_data["use_custom_mode"] == True:
                if (
                    not generation_data["song_input_genre"] or 
                    generation_data["song_input_genre"] == "" or
                    len(generation_data["song_input_genre"]) < CONSTANTS.MIN_GENRE_LENGTH
                ):
                    print("SUPABASE: The song_input_genre is invalid.")
                    return False

                custom_string_pattern = r'^[a-zA-Z0-9!?=.$;\'"\-\t\s\[\]()]+$'
                custom_title = generation_data["song_input_custom_title"]

                if (
                    not custom_title or 
                    custom_title == "" or 
                    len(custom_title) == 0 or
                    len(custom_title) > CONSTANTS.MAX_CUSTOM_TITLE_LENGTH
                ):
                    print("SUPABASE: The song's custom title is invalid.")
                    return False
                
                for word in CONSTANTS.FORBIDDEN_WORDS:
                    if word in custom_title.lower():
                        print(f"SUPABASE: Forbidden word found in the custom song title: {word}")
                        return False
                
                if not (re.match(custom_string_pattern, custom_title) and any(c.isalnum() for c in custom_title)):
                    print("SUPABASE: The song's custom title doesn't match the regex pattern or doesn't have at least one letter/digit.")
                    return False

                if generation_data["use_instrumental_only"] and generation_data["use_instrumental_only"] == False:
                    custom_lyrics = generation_data["song_input_custom_lyrics"]

                    if (
                        not custom_lyrics or 
                        len(custom_lyrics) < CONSTANTS.MIN_CUSTOM_LYRICS_LENGTH or
                        len(custom_lyrics) > CONSTANTS.MAX_CUSTOM_LYRICS_LENGTH
                    ):
                        print("SUPABASE: The song's custom lyrics are invalid.")
                        return False
                    
                    for word in CONSTANTS.FORBIDDEN_WORDS:
                        if word in custom_lyrics.lower():
                            print(f"SUPABASE: Forbidden word found in the custom song lyrics: {word}")
                            return False
                    
                    if not (re.match(custom_string_pattern, custom_lyrics)):
                        print("SUPABASE: The song's custom lyrics don't match the regex pattern.")
                        return False
            else:
                song_prompt = generation_data["song_prompt"]
                if not song_prompt or len(song_prompt) == 0 or song_prompt == "":
                    print("SUPABASE: Instrumental mode is activated but the song prompt is invalid.")
                    return False

            user_response = client.table(CONSTANTS.SUPABASE_USERS_TABLE).select("platform_user_id").eq("user_id", generation_data["user_id"]).execute()
            if not user_response.data or not user_response.data[0]["platform_user_id"]:
                print("SUPABASE: Could not find the user associated with this generation or user has no platform specific ID.")
                return False
            
            # Check if song already exists in the output audio bucket
            platform_user_id = user_response.data[0]["platform_user_id"]
            audio_bucket_song_path = f"user-id:{platform_user_id}/guild-id:{generation_data['replies_guild']}/output-reply-id:{generation_data['output_reply_id']}/"
            bucket_query_response = client.storage.from_(CONSTANTS.SUPABASE_SONG_OUTPUT_AUDIO_BUCKET).list(path=audio_bucket_song_path)
            if bucket_query_response:
                print("SUPABASE: There's a song already saved in the output audio bucket and linked to this generation.")
                return False

            return True
        except Exception as error:
            print(f'SUPABASE: Error in generation validation process: {str(error)}')
            return None

    def get_song_creation_data(self):
        """Fetch the song prompt for Suno."""
        bearer_token = self.generate_scraper_jwt()
        client: Client = self.get_supabase_client(bearer_token)
        generation_id = os.getenv('GENERATION_ID')

        try:
            response = client.table(CONSTANTS.SUPABASE_DISCORD_SONG_GENERATIONS_TABLE).select(
                       "song_prompt, song_input_custom_lyrics, song_input_custom_title, song_input_genre, song_input_vibe, second_song_input_genre"
                       ).eq("generation_id", generation_id).execute()
            
            if not response.data:
                print('SUPABASE: Could not get a valid song prompt.')
                return None

            return response.data[0]
        except Exception as error:
            print(f'SUPABASE: Error in fetching the song prompt: {str(error)}')
            return None

    def get_creation_modes(self):
        """Check if the Supabase song generation entry is valid."""
        bearer_token = self.generate_scraper_jwt()
        client: Client = self.get_supabase_client(bearer_token)
        generation_id = os.getenv('GENERATION_ID')

        try:
            generation_response = client.table(CONSTANTS.SUPABASE_DISCORD_SONG_GENERATIONS_TABLE).select(
                "use_custom_mode, "
                "use_instrumental_only"
            ).eq("generation_id", generation_id).execute()

            if not generation_response.data:
                print('SUPABASE: Could not find the generation ID on Supabase.')
                return False
                
            generation_data = generation_response.data[0]

            return generation_data["use_instrumental_only"], generation_data["use_custom_mode"]
        except Exception as e:
            print(f"SUPABASE: Error trying to fetch the song generation modes: {e}")
            return None, None

    def scraper_can_create_song(self):
        """Check if the scraper can create a song (no errors and enough credits)."""
        bearer_token = self.generate_scraper_jwt()
        client: Client = self.get_supabase_client(bearer_token)
        phone_number = os.getenv('PHONE_NUMBER')

        try:
            response = client.table(CONSTANTS.SUPABASE_SCRAPER_STATUS_TABLE).select("latest_error, remaining_credits").eq("phone_number", phone_number).execute()
            
            if not response.data:
                print('SUPABASE: Could not find the phone number on Supabase.')
                return False

            scraper_data = response.data[0]
            if scraper_data["latest_error"]:
                print('SUPABASE: The scraper had an error in a previous run.')
                return False
            
            if scraper_data["remaining_credits"] is None or scraper_data["remaining_credits"] <= CONSTANTS.MIN_SUNO_CREDIT_BALANCE:
                print("SUPABASE: The scraper's Suno account doesn't have enough credits.")
                return False

            return True
        except Exception as error:
            print(f'SUPABASE: Error when checking if the scraper can create a song: {str(error)}')
            return None
        
    def update_credit_number(self, credits):
        """Update the remaining credit number for the current PHONE_NUMBER."""
        if not credits or credits > CONSTANTS.MAX_CREDITS_NUMBER or credits < 0:
            print("SUPABASE: Invalid new Suno credits number.")
            return False

        bearer_token = self.generate_scraper_jwt()
        client: Client = self.get_supabase_client(bearer_token)
        phone_number = os.getenv('PHONE_NUMBER')

        try:
            client.table(CONSTANTS.SUPABASE_SCRAPER_STATUS_TABLE).update({"remaining_credits": int(credits)}).eq("phone_number", phone_number).execute()
            return True
        except Exception as e:
            print(f"SUPABASE: Got an error trying to update the credits number for {phone_number}. Details: {e}")
            return False
        
    def update_scraper_latest_error(self, errorDetails):
        """Update the latest error for the current PHONE_NUMBER."""
        error = self.stringify_if_json(errorDetails)

        if not error:
            print("SUPABASE: Invalid error message.")
            return False

        bearer_token = self.generate_scraper_jwt()
        client: Client = self.get_supabase_client(bearer_token)
        phone_number = os.getenv('PHONE_NUMBER')

        try:
            scraper_status = client.table(CONSTANTS.SUPABASE_SCRAPER_STATUS_TABLE).select("latest_error").eq("phone_number", phone_number).execute()
            if scraper_status.data and scraper_status.data[0] and scraper_status.data[0]["latest_error"] is not None:
                return True

            client.table(CONSTANTS.SUPABASE_SCRAPER_STATUS_TABLE).update({"latest_error": error}).eq("phone_number", phone_number).execute()
            return True
        except Exception as e:
            print(f"SUPABASE: Got an error trying to update the latest error for {phone_number}. Details: {e}")
            return False
        
    def update_generation_error_message(self, errorDetails):
        """Update the error message for the current GENERATION_ID."""
        error = self.stringify_if_json(errorDetails)

        if not error:
            print("SUPABASE: Invalid error message.")
            return False

        bearer_token = self.generate_scraper_jwt()
        client: Client = self.get_supabase_client(bearer_token)
        generation_id = os.getenv('GENERATION_ID')

        try:
            song_generation = client.table(CONSTANTS.SUPABASE_DISCORD_SONG_GENERATIONS_TABLE).select("*").eq("generation_id", generation_id).execute()
            if song_generation.data and song_generation.data[0] and song_generation.data[0]["error_message"] is not None:
                return True

            client.table(CONSTANTS.SUPABASE_DISCORD_SONG_GENERATIONS_TABLE).update({"error_message": error}).eq("generation_id", generation_id).execute()
            return True
        except Exception as e:
            print(f"SUPABASE: Got an error trying to update the error message for the generation with ID {generation_id}. Details: {e}")
            return False
        
    def save_song_data(self, song_title, song_genre, song_lyrics, downloaded_song_path):
        """Save the song data on Supabase."""
        if not all([song_title, song_genre, song_lyrics, downloaded_song_path]):
            print("SUPABASE: Invalid input for saving the song data.")
            return False

        bearer_token = self.generate_scraper_jwt()
        client: Client = self.get_supabase_client(bearer_token)
        generation_id = os.getenv('GENERATION_ID')

        try:
            if not os.path.exists(downloaded_song_path):
                print(f"SUPABASE: Song not found at {downloaded_song_path}.")
                return False
            
            generation_response = client.table(CONSTANTS.SUPABASE_DISCORD_SONG_GENERATIONS_TABLE).select("user_id, replies_guild, output_reply_id").eq("generation_id", generation_id).execute()

            if not generation_response.data:
                print("SUPABASE: Could not find the generation ID info while saving song data.")
                return False
            
            generation_data = generation_response.data[0]
            if not all([generation_data["user_id"], generation_data["replies_guild"], generation_data["output_reply_id"]]):
                print("SUPABASE: Got an invalid user ID, replies guild ID or initial reply ID while saving the song data.")
                return False

            user_response = client.table(CONSTANTS.SUPABASE_USERS_TABLE).select("platform_user_id").eq("user_id", generation_data["user_id"]).execute()
            if not user_response.data or not user_response.data[0]["platform_user_id"]:
                print("SUPABASE: Could not find the user associated with this generation or user has no platform specific ID.")
                return False
            
            platform_user_id = user_response.data[0]["platform_user_id"]
            song_file_name = unidecode(os.path.basename(downloaded_song_path))
            audio_bucket_song_path = f"user-id:{platform_user_id}/guild-id:{generation_data['replies_guild']}/output-reply-id:{generation_data['output_reply_id']}/{song_file_name}"

            print(f"SUPABASE: Saving the song file in the bucket called {CONSTANTS.SUPABASE_SONG_OUTPUT_AUDIO_BUCKET} at {audio_bucket_song_path}")

            with open(downloaded_song_path, 'rb') as audio_file:
                song_upload_response = client.storage.from_(CONSTANTS.SUPABASE_SONG_OUTPUT_AUDIO_BUCKET).upload(
                    path=audio_bucket_song_path,
                    file=audio_file,
                    file_options={"content-type": f"audio/{song_file_name.split('.')[-1]}"}
                )

            if not song_upload_response.status_code or song_upload_response.status_code != 200:
                print("SUPABASE: Failed to upload the song to the Supabase bucket.")
                return False
            
            client.table(CONSTANTS.SUPABASE_DISCORD_SONG_GENERATIONS_TABLE).update({
                "output_song": {"song": audio_bucket_song_path},
                "song_output_genre": song_genre,
                "song_output_title": unidecode(song_title),
                "song_output_lyrics": song_lyrics
            }).eq("generation_id", generation_id).execute()

            return True
        except Exception as e:
            print(f"SUPABASE: Error saving the song data on Supabase. Details: {e}")
            return False