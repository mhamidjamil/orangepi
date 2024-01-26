import random
from flask import jsonify, request
from .serial_handler import send_to_serial_port


def send_to_serial_from_routes(serial_data):
    send_to_serial_port("smsTo"+serial_data)


def send_auth():
    phone_number = request.args.get('phone_number', '')
    print(f"Received phone number: {phone_number}")

    random_number = random.randint(100000, 999999)
    print(f"Generated random number: {random_number}")

    send_to_serial_from_routes("[Your 2FA pin is: " + str(random_number) +
                               " don't share it with any one ;) ] for phone number: {" + phone_number + "}.")

    return jsonify({'result': 'Function alfa executed successfully', '2FA pin': random_number})
