"""Api and routes handler"""
import random
from flask import jsonify, request
from .serial_handler import send_custom_message #pylint: disable=relative-beyond-top-level
from .communication.ntfy import send_api_info #pylint: disable=relative-beyond-top-level


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
