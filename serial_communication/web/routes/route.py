"""Api and routes handler"""
import random
from flask import jsonify, request
from .serial_handler import send_custom_message  #pylint: disable=relative-beyond-top-level
from .communication.ntfy import send_api_info  #pylint: disable=relative-beyond-top-level
import time
import subprocess
import os


def restart_jellyfin():
    # Run the mount command
    print("jellyfin restarting")
    try:
        subprocess.run(['sudo', '-S', 'mount', '-a'], input=b'orangepi\n', text=True, check=True)
        print("Mount command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing mount command: {e}")
        return
    # time.sleep(2)
    # Restart the Jellyfin Docker container
    try:
        subprocess.run(['docker-compose', 'restart', 'jellyfin'], check=True)
        print("Jellyfin Docker container restarted.")
        return jsonify({'status': 'success', 'message': "Jellyfin restarted successfully"})
    except subprocess.CalledProcessError as e:
        print(f"Error restarting Jellyfin Docker container: {e}")
        return jsonify({'status': 'Fail', 'message': "Error while restarting server"})


def send_auth():
    """Send authentication message."""
    phone_number = request.args.get('phone_number', '')
    otp = request.args.get('otp', '')

    OTP_code = otp if otp else str(random.randint(100000, 999999))

    print(f"Received phone number: {phone_number}")
    print(f"Generated OTP code: {OTP_code}")

    send_api_info(f"send_auth is called for number: {phone_number} sending OTP: {OTP_code}")
    send_custom_message("Your 2FA pin is: " + OTP_code + " don't share it with anyone ;)", phone_number)

    return jsonify({'status': 'success', 'message': f"OTP [{OTP_code}] sent successfully"})
