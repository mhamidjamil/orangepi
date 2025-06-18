"""In this script we will be updating GPIOs state via API"""
import subprocess
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔧 Constants
DEFAULT_OUTPUT_PINS = [21, 11]  # Output pins
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
    'orange': (255, 165, 0),
    'pink': (255, 105, 180),
    'purple': (128, 0, 128),
    'lime': (191, 255, 0),
    'teal': (0, 128, 128),
    'skyblue': (135, 206, 235),
    'brown': (139, 69, 19),
    'gray': (128, 128, 128),
    'off': (0, 0, 0)
}
configured_pins = set()


def run_gpio_command(cmd_list):
    """Run a GPIO command safely."""
    subprocess.run(cmd_list, check=True)


def setup_gpio_outputs():
    """Initialize default GPIO output pins and blink LED."""
    for pin in DEFAULT_OUTPUT_PINS:
        setup_pin(pin, 'out')

    for _, pin in PWM_PINS.items():
        setup_pin(pin, 'pwm')
        set_pwm(pin, 0)

    # Blink LED on pin 21 five times
    for _ in range(5):
        run_gpio_command(['gpio', 'write', '21', '1'])
        time.sleep(0.1)
        run_gpio_command(['gpio', 'write', '21', '0'])
        time.sleep(0.1)


def setup_pin(pin, mode):
    """Configure a GPIO pin to a specific mode."""
    if pin not in configured_pins:
        run_gpio_command(['gpio', 'mode', str(pin), mode])
        configured_pins.add(pin)


def set_pwm(pin, value):
    """Clamp value 0-100 and set PWM."""
    clamped = max(0, min(1000, value))
    run_gpio_command(['gpio', 'pwm', str(pin), str(clamped)])


def parse_color_input(color_input):
    """Convert color name or hex code to RGB."""
    color_input = color_input.strip().lower()

    if color_input in COLOR_MAP:
        return COLOR_MAP[color_input]

    if color_input.startswith('#') and len(color_input) == 7:
        try:
            r = int(color_input[1:3], 16)
            g = int(color_input[3:5], 16)
            b = int(color_input[5:7], 16)
            return r, g, b
        except ValueError as exc:
            raise ValueError("Invalid hex color") from exc

    raise ValueError("Unknown color name or hex")


def apply_color(red_val, green_val, blue_val, brightness=100):
    """Apply scaled RGB values to PWM pins."""
    def scale(val):
        return int((val / 255.0) * 1000 * (brightness /100.0))

    set_pwm(PWM_PINS['red'], scale(red_val))
    set_pwm(PWM_PINS['green'], scale(green_val))
    set_pwm(PWM_PINS['blue'], scale(blue_val))


@app.route('/color', methods=['GET', 'POST'])
def set_color():
    """API endpoint to control LED color and effects."""
    args = request.args if request.method == 'GET' else request.json or {}

    color = args.get('color', 'off')
    style = args.get('style', 'direct')
    duration = args.get('time', '2s').lower().replace('s', '')
    brightness = int(args.get('brightness', 100))

    try:
        r_val, g_val, b_val = parse_color_input(color)
    except ValueError as err:
        return jsonify({'error': str(err)}), 400

    try:
        if style == 'fade':
            count = int(duration)
            for _ in range(count):
                for level in range(0, 101, 5):
                    apply_color(r_val, g_val, b_val, level)
                    time.sleep(0.01)
                for level in range(100, -1, -5):
                    apply_color(r_val, g_val, b_val, level)
                    time.sleep(0.01)
        elif style == 'blink':
            count = int(duration)
            for _ in range(count):
                apply_color(r_val, g_val, b_val, brightness)
                time.sleep(0.5)
                apply_color(0, 0, 0, 0)
                time.sleep(0.5)
        elif style == 'solid':
            apply_color(r_val, g_val, b_val, brightness)
            time.sleep(int(duration))
            apply_color(0, 0, 0, 0)
        else:
            apply_color(r_val, g_val, b_val, brightness)

        return jsonify({'success': True, 'color': color, 'style': style, 'brightness': brightness})

    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({'error': str(exc)}), 500


if __name__ == '__main__':
    setup_gpio_outputs()
    app.run(host='0.0.0.0', port=3011)
