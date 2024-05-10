"""Api and routes handler"""
import random
from flask import jsonify, request
from .serial_handler import send_custom_message #pylint: disable=relative-beyond-top-level
from .communication.ntfy import send_api_info #pylint: disable=relative-beyond-top-level


def send_auth():
    """send auth message to phone number"""
    phone_number = request.args.get('phone_number', '')
    print(f"Received phone number: {phone_number}")

    random_number = random.randint(100000, 999999)
    print(f"Generated random number: {random_number}")

    OTP_code = str(random_number)
    send_api_info(f"send_auth is called for number: {phone_number} sending OTP: {OTP_code}")
    send_custom_message("Your 2FA pin is: " + OTP_code +
        " don't share it with any one ;)", phone_number)

    return jsonify({'result': 'Function alfa executed successfully', '2FA pin': random_number})
