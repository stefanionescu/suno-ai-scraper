import os
import stat
import shutil
from time import sleep
from random import randint
import constants as CONSTANTS

def random_micro_sleep(min=CONSTANTS.MICRO_MIN_SECONDS_TO_WAIT, max=CONSTANTS.MICRO_MAX_SECONDS_TO_WAIT):
    """Sleeps for a random minuscule duration."""
    sleep(randint(min, max))

def random_short_sleep(min=CONSTANTS.SHORT_MIN_SECONDS_TO_WAIT, max=CONSTANTS.SHORT_MAX_SECONDS_TO_WAIT):
    """Sleeps for a random short duration."""
    sleep(randint(min, max))

def random_normal_sleep(min=CONSTANTS.NORMAL_MIN_SECONDS_TO_WAIT, max=CONSTANTS.NORMAL_MAX_SECONDS_TO_WAIT):
    """Sleeps for a random normal duration."""
    sleep(randint(min, max))

def random_long_sleep(min=CONSTANTS.LONG_MIN_SECONDS_TO_WAIT, max=CONSTANTS.LONG_MAX_SECONDS_TO_WAIT):
    """Sleeps for a random long duration."""
    sleep(randint(min, max))

def sleep_custom(time_to_sleep):
    """Sleeps for a custom duration if time_to_sleep is non-zero."""
    if time_to_sleep != 0:
        sleep(time_to_sleep)

def ensure_directory_exists(directory_path):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"UTILS: Directory created: {directory_path}")
    else:
        print(f"UTILS: Directory already exists: {directory_path}")

def force_delete(action, name, exc):
    """Forcibly deletes a file by changing its permissions."""
    try:
        os.chmod(name, stat.S_IWRITE)
        os.remove(name)
    except Exception as e:
        print(f"UTILS: Error forcibly deleting {name}: {e}")

def delete_file(file_path):
    """Deletes a file and returns True if successful, False otherwise."""
    try:
        os.remove(file_path)
        print(f"UTILS: Deleted file: {file_path}")
        return True
    except FileNotFoundError:
        print(f"UTILS: File not found: {file_path}")
        return False
    except Exception as e:
        print(f"UTILS: Error deleting file {file_path}: {e}")
        return False

def delete_directory(dir_path):
    """Deletes a directory and its contents, returns True if successful, False otherwise."""
    try:
        # Ensure the directory and all its contents have write permission
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for dir_name in dirs:
                try:
                    os.chmod(os.path.join(root, dir_name), stat.S_IRWXU)
                except Exception:
                    pass
            for file_name in files:
                try:
                    os.chmod(os.path.join(root, file_name), stat.S_IRWXU)
                except Exception:
                    pass

        # Ensure the main directory itself is writable
        os.chmod(dir_path, stat.S_IRWXU)
       
        # Attempt to delete the directory
        shutil.rmtree(dir_path, onerror=force_delete)
        print(f"UTILS: Deleted directory: {dir_path}")
        return True
    except FileNotFoundError:
        print(f"UTILS: Directory not found during deletion attempt: {dir_path}")
        return False
    except Exception as e:
        print(f"UTILS: Error deleting directory {dir_path}: {e}")
        return False