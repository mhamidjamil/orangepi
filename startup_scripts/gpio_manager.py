from flask import Flask, request, jsonify
import subprocess
import time

app = Flask(__name__)

LED_PIN = 10  # Define the LED pin

def initialize_gpio():
    """Blink the LED on pin 10 three times when the server starts."""
    for _ in range(5):
        subprocess.run(['gpio', 'write', str(LED_PIN), '1'], check=True)
        time.sleep(0.1)
        subprocess.run(['gpio', 'write', str(LED_PIN), '0'], check=True)
        time.sleep(0.1)

@app.route('/gpio', methods=['GET'])
def control_gpio():
    """Control GPIO via API"""
    pin = request.args.get('pin', type=int)
    state = request.args.get('state', type=int)

    if pin is None or state not in [0, 1]:
        return jsonify({"error": "Invalid pin or state. Pin must be an integer, and state must be 0 or 1."}), 400

    try:
        subprocess.run(['gpio', 'write', str(pin), str(state)], check=True)
        return jsonify({"success": True, "message": f"Pin {pin} set to {state}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to set GPIO pin: {str(e)}"}), 500

if __name__ == '__main__':
    initialize_gpio()  # Blink LED on startup
    app.run(host='0.0.0.0', port=3011)
