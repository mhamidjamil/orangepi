"""Script to manage Motion files on Orange Pi.

This script moves files from the Motion directory to a mounted HDD and
manages storage by deleting old files if the directory exceeds a set limit.
"""

import os
import shutil
import time
import threading
import subprocess
from dotenv import load_dotenv
from ntfy import motion_status

# Load environment variables from .env file
DOTENV_PATH = '/home/orangepi/Desktop/projects/orangepi/serial_communication/web/.env'
load_dotenv(DOTENV_PATH)

# Global variables for configuration
SOURCE_DIR = "/var/lib/motion"
DEST_DIR = "/mnt/wd/motion"
MAX_SIZE_GB = 10  # Maximum size in GB
CHECK_INTERVAL = 600  # Time interval in seconds (10 minutes)
LOG_FILE = "/var/log/motion_file_manager.log"  # Log file path
MAX_RETRIES = 3  # Maximum number of retries for accessing DEST_DIR
RETRY_DELAY = 300  # Delay between retries in seconds (5 minutes)
MY_PASSWORD = os.getenv("MY_PASSWORD")  # Get password from .env file


def logger(message, send_alert=True):
    """Logs messages and sends alerts if needed."""
    print(message)
    if send_alert:
        motion_status(message)


def run_with_sudo(command):
    """Executes a command with sudo privileges."""
    try:
        with subprocess.Popen(
            ["sudo", "-S"] + command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        ) as process:
            _, stderr = process.communicate(input=MY_PASSWORD + "\n")

        if process.returncode != 0:
            logger(f"Error executing command: {stderr.strip()}")
            return False
        return True
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger(f"Exception occurred: {error}")
        return False


def move_files():
    """Moves files from source to destination directory."""
    retries = 0
    while retries < MAX_RETRIES:
        if not os.path.exists(DEST_DIR):
            retries += 1
            logger(
                "Destination folder not found. Waiting for 5 minutes."
                f"{MAX_RETRIES - retries} attempts left.",
                False,
            )
            time.sleep(RETRY_DELAY)
        else:
            break

    if retries == MAX_RETRIES:
        logger("Unable to access destination folder."
        "Stopping file movement. Only managing storage of SOURCE_DIR.")
        return

    if not os.path.exists(SOURCE_DIR):
        return

    files = os.listdir(SOURCE_DIR)
    for file in files:
        src_file = os.path.join(SOURCE_DIR, file)
        dest_file = os.path.join(DEST_DIR, file)

        if not os.path.isfile(src_file):
            continue

        try:
            shutil.copy2(src_file, dest_file)
            if run_with_sudo(["rm", src_file]):
                logger(f"Moved: {src_file} to {dest_file}")
            else:
                logger(f"Failed to delete {src_file}.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger(f"Error moving {src_file}: {e}")



def manage_storage():
    """Checks storage usage and deletes old files if necessary."""
    while True:
        if os.path.exists(SOURCE_DIR):
            total_size = sum(
                os.path.getsize(os.path.join(SOURCE_DIR, file))
                for file in os.listdir(SOURCE_DIR)
                if os.path.isfile(os.path.join(SOURCE_DIR, file))
            )
            total_size_gb = total_size / (1024 ** 3)

            if total_size_gb > MAX_SIZE_GB:
                logger(f"Storage size exceeded: {total_size_gb:.2f} GB")
                files = [
                    os.path.join(SOURCE_DIR, file)
                    for file in os.listdir(SOURCE_DIR)
                    if os.path.isfile(os.path.join(SOURCE_DIR, file))
                ]
                files.sort(key=os.path.getctime)

                while total_size_gb > MAX_SIZE_GB and files:
                    oldest_file = files.pop(0)
                    file_size = os.path.getsize(oldest_file) / (1024 ** 3)
                    if not run_with_sudo(["rm", oldest_file]):
                        logger(f"Failed to delete {oldest_file}.")
                    else:
                        total_size_gb -= file_size
                        logger(f"Deleted: {oldest_file} to free up space."
                               f"Current size: {total_size_gb:.2f} GB")

        time.sleep(CHECK_INTERVAL)


def main():
    """Main function to start the script."""
    logger("Starting script to manage motion files.")
    if MY_PASSWORD is None:
        logger("MY_PASSWORD environment variable is not set. Exiting.")
        return

    if not os.path.exists(SOURCE_DIR):
        logger(f"Source directory {SOURCE_DIR} does not exist. Exiting.")
        return

    move_thread = threading.Thread(target=move_files, daemon=True)
    manage_thread = threading.Thread(target=manage_storage, daemon=True)

    move_thread.start()
    manage_thread.start()

    move_thread.join()
    manage_thread.join()


if __name__ == "__main__":
    main()
