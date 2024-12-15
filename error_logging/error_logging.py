import os
import sendgrid
import constants as CONSTANTS
from dotenv import load_dotenv
from db.supabase import Supabase
from sendgrid.helpers.mail import Mail, Email, To, Content

class ErrorLogging():
    def __init__(self):
        load_dotenv()
        self.supabase = Supabase()

    def save_error_and_send_email(self, message):
        self.supabase.update_scraper_latest_error(message)
        self.supabase.update_generation_error_message(message)
        self.send_email(message)

    def save_generation_error_and_send_email(self, message):
        self.supabase.update_generation_error_message(message)
        self.send_email(message)

    def send_email(self, message):
        if not message:
            print("EMAIL_LOGGING: Cannot email a null message.")
            return False

        try:
            sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
            from_email = Email(os.getenv("EMAIL_FROM"))
            to_email = To(os.getenv("EMAIL_TO"))
            subject = CONSTANTS.ERROR_EMAIL_TITLE.replace("{phone_number}", os.getenv('PHONE_NUMBER'))
            content = Content("text/plain", str(message))
            mail = Mail(from_email, to_email, subject, content)

            # Get a JSON-ready representation of the Mail object
            mail_json = mail.get()

            # Send an HTTP POST request to /mail/send
            response = sg.client.mail.send.post(request_body=mail_json)

            if response.status_code and (str(response.status_code) == "200" or str(response.status_code) == "202"):
                print("EMAIL_LOGGING: Sent the error over email!")
                return True
            
            print("EMAIL_LOGGING: Could not email the error")
            return False
        except Exception as e:
            print(f"EMAIL_LOGGING: Got an error trying to send an error over email. Details: {e}")
            return False