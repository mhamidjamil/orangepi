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

# Logger function to print and log messages
def logger(message):
    print(message)
    motion_status(message)


# Function to run a command with sudo
def run_with_sudo(command):
    try:
        process = subprocess.Popen(
            ["sudo", "-S"] + command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        stdout, stderr = process.communicate(input=MY_PASSWORD + "\n")
        if process.returncode != 0:
            logger(f"Error executing command: {stderr.strip()}")
            return False
        return True
    except Exception as e:
        logger(f"Exception occurred: {e}")
        return False

# Function to move files from source to destination directory
def move_files():
    retries = 0
    while retries < MAX_RETRIES:
        if not os.path.exists(DEST_DIR):
            retries += 1
            logger(f"Destination folder not found. Waiting for 5 minutes. {MAX_RETRIES - retries} attempts left.")
            time.sleep(RETRY_DELAY)
        else:
            break

    if retries == MAX_RETRIES:
        logger("Unable to access destination folder. Stopping file movement. Only managing storage of SOURCE_DIR.")
        return

    while True:
        if os.path.exists(SOURCE_DIR):
            files = os.listdir(SOURCE_DIR)
            for file in files:
                src_file = os.path.join(SOURCE_DIR, file)
                dest_file = os.path.join(DEST_DIR, file)
                if os.path.isfile(src_file):
                    try:
                        # Copy the file to the destination
                        shutil.copy2(src_file, dest_file)
                        # Remove the source file using sudo
                        if not run_with_sudo(["rm", src_file]):
                            logger(f"Failed to delete {src_file}.")
                        else:
                            logger(f"Moved: {src_file} to {dest_file}")
                    except Exception as e:
                        logger(f"Error moving {src_file}: {e}")
        time.sleep(CHECK_INTERVAL)

# Function to check the size of the source directory and delete oldest files if necessary
def manage_storage():
    while True:
        if os.path.exists(SOURCE_DIR):
            total_size = sum(os.path.getsize(os.path.join(SOURCE_DIR, f)) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f)))
            total_size_gb = total_size / (1024 ** 3)  # Convert size to GB

            if total_size_gb > MAX_SIZE_GB:
                logger(f"Storage size exceeded: {total_size_gb:.2f} GB")
                files = [os.path.join(SOURCE_DIR, f) for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
                files.sort(key=os.path.getctime)  # Sort files by creation time

                while total_size_gb > MAX_SIZE_GB and files:
                    oldest_file = files.pop(0)
                    file_size = os.path.getsize(oldest_file) / (1024 ** 3)
                    if not run_with_sudo(["rm", oldest_file]):
                        logger(f"Failed to delete {oldest_file}.")
                    else:
                        total_size_gb -= file_size
                        logger(f"Deleted: {oldest_file} to free up space. Current size: {total_size_gb:.2f} GB")

        time.sleep(CHECK_INTERVAL)

# Main function to start the threads
def main():
    logger("Staring script to manage motion files.")
    if not MY_PASSWORD:
        logger("MY_PASSWORD environment variable is not set. Exiting.")
        return

    if not os.path.exists(SOURCE_DIR):
        logger(f"Source directory {SOURCE_DIR} does not exist. Exiting.")
        return

    move_thread = threading.Thread(target=move_files)
    manage_thread = threading.Thread(target=manage_storage)

    move_thread.start()
    manage_thread.start()

    move_thread.join()
    manage_thread.join()

if __name__ == "__main__":
    main()
