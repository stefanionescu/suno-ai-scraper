import os
import boto3
import shutil
import zipfile
from dotenv import load_dotenv
import utils.utils as utils

class AWS:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Initialize AWS S3 client
        self.s3 = boto3.client('s3', 
                               aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
                               aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                               region_name=os.getenv("AWS_REGION"))
        self.aws_bucket_name = os.getenv("AWS_BUCKET_NAME")

    def check_object_exists(self, phone_number):
        """Check if a Chrome profile exists in S3 for the given phone number."""
        try:
            self.s3.head_object(Bucket=self.aws_bucket_name, Key=phone_number)
            print(f"AWS: Chrome profile exists: s3://{self.aws_bucket_name}/{phone_number}")
            return True
        except Exception as e:
            print(f"AWS: Chrome profile does not exist: s3://{self.aws_bucket_name}/{phone_number}")
            print(e)
            return False

    def compress_chrome_profile(self, chrome_profile_dir, zip_file):
        """Compress the Chrome profile directory into a zip file."""
        try:
            shutil.make_archive(zip_file, 'zip', chrome_profile_dir)
            print(f"AWS: Compressed the Chrome profile located at {chrome_profile_dir}")
            return True
        except Exception as e:
            print(f"AWS: Failed to compress the Chrome profile located at {chrome_profile_dir}")
            print(e)
            return False

    def save_profile_in_bucket(self, zip_file, s3_key):
        """Save the Chrome profile zip file to S3, replacing any existing profile."""
        try:
            # Check and delete old profile if it exists
            self._delete_old_profile(s3_key)

            # Upload the new profile
            self.s3.upload_file(zip_file, self.aws_bucket_name, s3_key)
            print(f"AWS: Uploaded the new Chrome profile from {zip_file} to s3://{self.aws_bucket_name}/{s3_key}")
            return True
        except Exception as e:
            print(f"AWS: Could not save the Chrome profile located at {zip_file} to s3://{self.aws_bucket_name}/{s3_key}")
            print(e)
            return False

    def _delete_old_profile(self, s3_key):
        """Helper method to delete old profile if it exists."""
        try:
            self.s3.head_object(Bucket=self.aws_bucket_name, Key=s3_key)
            print(f"AWS: Old profile found at s3://{self.aws_bucket_name}/{s3_key}")
            self.s3.delete_object(Bucket=self.aws_bucket_name, Key=s3_key)
            print(f"AWS: Deleted old profile at s3://{self.aws_bucket_name}/{s3_key}")
        except self.s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"AWS: No existing profile found at s3://{self.aws_bucket_name}/{s3_key}")
            else:
                raise

    def download_chrome_profile(self, chrome_profiles_directory, phone_number):
        """Download and extract the Chrome profile for the given phone number."""
        print(f"AWS: Downloading the Chrome profile for {phone_number}...")
        utils.ensure_directory_exists(chrome_profiles_directory)

        try:
            if self.check_object_exists(phone_number):
                zip_file_path = os.path.join(chrome_profiles_directory, f"{phone_number}_chrome_profile.zip")
                chrome_profile_dir = os.path.join(chrome_profiles_directory, f"{phone_number}_chrome_profile")

                # Download the file from S3
                self.s3.download_file(self.aws_bucket_name, phone_number, zip_file_path)
                print(f"AWS: Downloaded s3://{self.aws_bucket_name}/{phone_number} to {zip_file_path}")

                # Extract the downloaded zip file
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(chrome_profile_dir)
                print(f"AWS: Extracted {zip_file_path} to {chrome_profile_dir}")

                # Clean up the zip file
                utils.delete_file(zip_file_path)

            return True
        except Exception as e:
            print(f"AWS: Error downloading a Chrome profile: s3://{self.aws_bucket_name}/{phone_number}")
            print(e)
            return False