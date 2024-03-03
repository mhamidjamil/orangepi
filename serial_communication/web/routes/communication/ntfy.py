"""This script will be used to send notification to android"""
import subprocess
import sys
import logging
import os
from dotenv import load_dotenv

# Specify the path to your .env file
DOTENV_PATH = '/home/orangepi/Desktop/projects/orangePi/serial_communication/web/.env'
load_dotenv(DOTENV_PATH)
SAVE_LOGS = True

file = os.getenv("DEFAULT_LOGGER")
logging.basicConfig(filename=file, level=logging.INFO)

NTFY_URL = os.getenv("_NTFY_URL_")

def send_to_android(endpoint, message):
    """Function to send data to Android using specified endpoint"""
    if not SAVE_LOGS:
        return
    message = message.replace(' ', '_')
    if NTFY_URL is None:
        print("Make sure you env file is on Write location.")
    else:
        command = f"curl -d {message} {NTFY_URL}/{endpoint}"
        # curl -d testing 192.168.1.239:9999/warnings
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print("Command output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Error executing command:", e)
            print("Command output (stderr):", e.stderr)


def send_info(message):
    """to send muted infos"""
    send_to_android("infos", message)
    log_message("info", message)

def send_warning(message):
    """to send warnings"""
    send_to_android("warnings", message)
    log_message("warning", message)

def send_error(message):
    """to send errors"""
    send_to_android("errors", message)
    log_message("error", "\n" + message + "\n")

def log_message(level, msg):
    """Log a message with the specified log level."""
    if not SAVE_LOGS:
        return
    if level == 'info':
        logging.info(msg)
    elif level == 'warning':
        logging.warning(msg)
    elif level == 'error':
        logging.error(msg)
    else:
        raise ValueError(f"Invalid log level: {level}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        send_warning("no args send test message")
    else:
        ARGS = ' '.join(sys.argv[1:])
        if "info" in ARGS:
            send_info(ARGS)
        elif "warning" in ARGS:
            send_warning(ARGS)
        elif "error" in ARGS:
            send_error(ARGS)
        else:
            send_warning("else case: " + ARGS)
        # send_error("test message")
