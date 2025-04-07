"""A simple Flask API to control GPIO pins on an Orange Pi."""
import subprocess
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔧 Global Config
DEFAULT_OUTPUT_PINS = [10, 11]  # Easily editable list of pins to initialize as output
LED_PIN = 10  # LED pin (should be included in DEFAULT_OUTPUT_PINS)
configured_pins = set()  # Set to track initialized pins


def initialize_gpio():
    """Initialize default GPIO pins and blink LED on startup."""
    for pin in DEFAULT_OUTPUT_PINS:
        setup_gpio(pin)

    # Blink the LED pin 5 times
    for _ in range(5):
        subprocess.run(['gpio', 'write', str(LED_PIN), '1'], check=True)
        time.sleep(0.1)
        subprocess.run(['gpio', 'write', str(LED_PIN), '0'], check=True)
        time.sleep(0.1)


def setup_gpio(pin):
    """Set up GPIO pin as output if it hasn't been configured yet."""
    if pin not in configured_pins:
        subprocess.run(['gpio', 'mode', str(pin), 'out'], check=True)
        configured_pins.add(pin)


@app.route('/gpio', methods=['GET'])
def control_gpio():
    """Control GPIO via API"""
    pin = request.args.get('pin', type=int)
    state = request.args.get('state', type=int)

    if pin is None or state not in [0, 1]:
        return jsonify({"error": "Invalid pin or state. "
                                 "Pin must be an integer, and state must be 0 or 1."}), 400

    try:
        setup_gpio(pin)  # Ensure the pin is set to output mode
        subprocess.run(['gpio', 'write', str(pin), str(state)], check=True)
        return jsonify({"success": True, "message": f"Pin {pin} set to {state}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to set GPIO pin: {str(e)}"}), 500


if __name__ == '__main__':
    initialize_gpio()  # Set default pins to output and blink LED
    app.run(host='0.0.0.0', port=3011)
