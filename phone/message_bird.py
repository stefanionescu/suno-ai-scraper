import os
import re
import requests
import constants as CONSTANTS
from dotenv import load_dotenv
from datetime import datetime, timedelta

class MessageBird():
    def __init__(self, client_data):
        load_dotenv()  # Load environment variables once during initialization
        self.client_data = client_data

    def fetch_suno_verification_code(self):
        if not self.client_data["workspace_id"] or not self.client_data["channel_id"]:
            print("MESSAGE_BIRD: Invalid workspace or channel ID.")
            return None

        access_key = os.getenv("MESSAGE_BIRD_API_KEY", "")
        base_url = "https://api.bird.com"
        endpoint = f'/workspaces/{self.client_data["workspace_id"]}/channels/{self.client_data["channel_id"]}/messages'

        # Calculate the start time
        start_time = datetime.now() - timedelta(minutes=CONSTANTS.SMS_MAX_TIME_DELTA_MINUTES)
        
        params = {
            "limit": CONSTANTS.MAX_SMS_TO_READ,
            "direction": "incoming",
            "startAt": start_time.isoformat() + "Z"  # Format as ISO 8601 with UTC indicator
        }
        
        headers = {
            "Authorization": f"AccessKey {access_key}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            for message in data.get('results', []):
                text = message.get('body', {}).get('text', {}).get('text', '')
                if CONSTANTS.SUNO_VERIFICATION_MESSAGE_IDENTIFIER in text:
                    match = re.search(r'\b(\d{6})\b', text)
                    if match:
                        return match.group(1)  # Return the 6-digit code
            
            return None  # Return None if no matching message is found
        except requests.exceptions.RequestException as e:
            print(f"MESSAGE_BIRD: An error occurred: {e}")
            return None