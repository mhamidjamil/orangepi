"""Flask API to control GPIO pins on Orange Pi with PWM and digital output support."""
import subprocess
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔧 Configuration
DIGITAL_OUTPUT_PINS = [21, 11]  # Digital output pins
LED_PIN = 21  # LED pin that blinks on startup

PWM_PINS = {
    'red': 9,
    'green': 10,
    'blue': 6
}

COLOR_MAP = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'yellow': (255, 255, 0),
    'cyan': (0, 255, 255),
    'magenta': (255, 0, 255),
    'white': (255, 255, 255),
    'off': (0, 0, 0)
}

DEFAULT_BRIGHTNESS = 100  # 0–100%
CONFIGURED_PINS = set()


def run_gpio_command(args):
    """Run a GPIO command using subprocess."""
    subprocess.run(['gpio'] + list(map(str, args)), check=True)


def setup_gpio(pin):
    """Initialize a digital pin as output if not already configured."""
    if pin not in CONFIGURED_PINS:
        run_gpio_command(['mode', pin, 'out'])
        CONFIGURED_PINS.add(pin)


def setup_pwm(pin):
    """Initialize a pin in PWM mode if not already configured."""
    if pin not in CONFIGURED_PINS:
        run_gpio_command(['mode', pin, 'pwm'])
        CONFIGURED_PINS.add(pin)


def set_pwm(pin, value):
    """Set PWM value for a pin."""
    run_gpio_command(['pwm', pin, value])


def apply_rgb_color(red_val, green_val, blue_val, brightness=DEFAULT_BRIGHTNESS):
    """Apply scaled RGB values to PWM pins."""
    def scale(val):
        return int((val / 255.0) * 1000 * (brightness / 100.0))

    set_pwm(PWM_PINS['red'], scale(red_val))
    set_pwm(PWM_PINS['green'], scale(green_val))
    set_pwm(PWM_PINS['blue'], scale(blue_val))


def initialize_gpio():
    """Initialize GPIO pins and blink LED 5 times."""
    for pin in DIGITAL_OUTPUT_PINS:
        setup_gpio(pin)

    for pin in PWM_PINS.values():
        setup_pwm(pin)
        set_pwm(pin, 0)

    # Blink LED 5 times
    for _ in range(5):
        run_gpio_command(['write', LED_PIN, 1])
        time.sleep(0.1)
        run_gpio_command(['write', LED_PIN, 0])
        time.sleep(0.1)


@app.route('/gpio', methods=['GET'])
def control_gpio():
    """Control digital GPIO output pins."""
    pin = request.args.get('pin', type=int)
    state = request.args.get('state', type=int)

    if pin is None or state not in [0, 1]:
        return jsonify({"error": "Invalid pin or state. Must be pin=X&state=0|1"}), 400

    try:
        setup_gpio(pin)
        run_gpio_command(['write', pin, state])
        return jsonify({"success": True, "message": f"Pin {pin} set to {state}"})
    except subprocess.CalledProcessError as err:
        return jsonify({"error": f"Failed to control GPIO: {err}"}), 500


@app.route('/color', methods=['GET', 'POST'])
def set_color():
    """Set RGB color via PWM with support for blink, fade, and solid styles."""
    if request.method == 'GET':
        color_name = request.args.get('color', '').lower()
        style = request.args.get('style', 'direct').lower()
        duration = float(request.args.get('duration', 3))
        brightness = int(request.args.get('brightness', DEFAULT_BRIGHTNESS))
    else:
        data = request.get_json()
        color_name = data.get('color', '').lower()
        style = data.get('style', 'direct').lower()
        duration = float(data.get('duration', 3))
        brightness = int(data.get('brightness', DEFAULT_BRIGHTNESS))

    if color_name not in COLOR_MAP:
        return jsonify({"error": "Unknown color name."}), 400

    red_val, green_val, blue_val = COLOR_MAP[color_name]

    try:
        if style == 'fade':
            for _ in range(int(duration)):
                for level in range(0, 101, 5):
                    apply_rgb_color(red_val, green_val, blue_val, level)
                    time.sleep(0.05)
                for level in range(100, -1, -5):
                    apply_rgb_color(red_val, green_val, blue_val, level)
                    time.sleep(0.05)
            apply_rgb_color(0, 0, 0)
        elif style == 'blink':
            for _ in range(int(duration)):
                apply_rgb_color(red_val, green_val, blue_val, brightness)
                time.sleep(0.5)
                apply_rgb_color(0, 0, 0)
                time.sleep(0.5)
        elif style == 'solid':
            apply_rgb_color(red_val, green_val, blue_val, brightness)
            time.sleep(duration)
            apply_rgb_color(0, 0, 0)
        else:
            apply_rgb_color(red_val, green_val, blue_val, brightness)

        return jsonify({
            "success": True,
            "color": color_name,
            "style": style,
            "brightness": brightness
        })
    except Exception as err:
        return jsonify({"error": str(err)}), 500


if __name__ == '__main__':
    initialize_gpio()
    app.run(host='0.0.0.0', port=3011)
