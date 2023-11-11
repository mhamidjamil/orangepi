import random
from flask import jsonify, request

def send_auth():
    phone_number = request.args.get('phone_number', '')
    print(f"Received phone number: {phone_number}")

    random_number = random.randint(100000, 999999)
    print(f"Generated random number: {random_number}")

    # Your send_auth logic here

    return jsonify({'result': 'Function alfa executed successfully', '2FA pin': random_number})
