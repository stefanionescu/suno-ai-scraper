import os, re
from zoneinfo import ZoneInfo
import constants as CONSTANTS
from dotenv import load_dotenv
from twilio.rest import Client
from datetime import datetime, timedelta

class Twilio():
    def __init__(self, phone_number):
        load_dotenv()  # Load environment variables once during initialization
        self.phone_number = phone_number

    def fetch_suno_verification_code(self):
        if not self.phone_number or self.phone_number == "":
            print("TWILIO: Cannot search for null receivers on Twilio.")
            return None

        # Load environment variables or replace with your actual Account SID and Auth Token
        ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
        AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')

        # Get the current time
        now = datetime.now(ZoneInfo("UTC"))

        # Initialize the Twilio client
        client = Client(ACCOUNT_SID, AUTH_TOKEN)

        # Fetch the last couple messages
        messages = client.messages.list(to=self.phone_number, limit=CONSTANTS.MAX_SMS_TO_READ)

        # Filter for messages that contain the Suno verification code and start with 6 digits
        pattern = re.compile(r'^\d{6}')  # Regex pattern to check if message starts with 6 digits
        suno_messages = [
            msg for msg in messages 
            if CONSTANTS.SUNO_VERIFICATION_MESSAGE_IDENTIFIER in msg.body 
            and pattern.match(msg.body) 
            and msg.to == self.phone_number
            and (now - msg.date_sent) <= timedelta(minutes=CONSTANTS.SMS_MAX_TIME_DELTA_MINUTES)
        ]

        # Check if there are any messages that meet the criteria and print the latest one
        if suno_messages:
            pattern = re.compile(r'\d{6}')  # Looks for any sequence of 6 digits
            digit_match = pattern.search(suno_messages[0].body)
            return digit_match.group(0)
        
        return None