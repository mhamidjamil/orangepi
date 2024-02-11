"""This script continously ping running scripts to check if they are working well"""
import time
import random
import subprocess
import os
from dotenv import load_dotenv
import requests
from serial_handler import exception_logger, fetch_current_time_online
load_dotenv()

def check_flask_service():
    """If our flask service is not orking as expected then it will restart that service"""
    try:
        # Generate a random two-digit number
        random_number = random.randint(10, 99)

        # Make a GET request to the /inspect route with the random number
        response = requests.get(f'http://localhost:6677/inspect?number={random_number}'
                                , timeout = 5)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            data = response.json()
            print(data['message'])
        else:
            print(f"Unexpected response: {response.text}")
            exception_logger("script_inspector: check_flask_service", response.text)
            restart_flask_service()
    except Exception as e: # pylint: disable=broad-except
        print(f"An error occurred: {e}")
        restart_flask_service()
        time.sleep(15) # try to restart script so wait for it then save the logs
        exception_logger("script_inspector: check_flask_service", e)

def restart_flask_service():
    """This will restart Flask service if the response is not as expected"""
    print("Restarting Flask service...")

    # Replace 'serial_monitoring_service' with the actual service name
    service_name = 'serial_monitoring.service'

    try:
        # Get the sudo password from the environment variable
        password = os.getenv("MY_PASSWORD")
        if not password:
            raise ValueError("Password not set in the environment variable MY_PASSWORD")

        # Use subprocess to run the systemctl command to restart the service
        command = ['sudo', '-S', 'systemctl', 'restart', service_name]
        subprocess.run(command, input=f"{password}\n", text=True, check=True)
        print(f"{service_name} restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error restarting {service_name}: {e}")

if __name__ == "__main__":
    # time.sleep(650) # need this delay as app.py will start after 10 minutes
    while True:
        print("\n\n\t loop restarted\n\n")
        check_flask_service() # you can add more inspectore here
        print(f"Last run on: {fetch_current_time_online}")
        print("\n\n\t After inspection\n\n")
        time.sleep(30)  # Wait for 10 minutes before checking again
