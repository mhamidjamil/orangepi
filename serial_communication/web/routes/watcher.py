# serial_handler.py
"""This script is will communicate with Watcher"""
import time
import threading
import serial
import serial.tools.list_ports
from flask import jsonify, request
from .communication.ntfy import send_warning, send_error, send_info #pylint: disable=relative-beyond-top-level

SERIAL_PORT = None
MAX_RETRIES = 2
MAX_RETRY_TIME = 30

LED_STATE = False
BUZZER_STATE = False

def initialize_port():
    """This part will initialize serial port for watcher"""
    global SERIAL_PORT # pylint: disable=global-statement
    SERIAL_PORT = update_serial_port("/dev/ttyUSB")

def update_serial_port(device, next_try_after=10, retries=0):
    """Update the serial port dynamically."""
    try:
        max_port_number = 5  # Maximum port number to try
        port_pattern = f'{device}{{}}'
        print("Trying to connect to port!")
        while True:
            for port_number in range(max_port_number):
                port = port_pattern.format(port_number)
                try:
                    temp_ser = serial.Serial(port, baudrate=115200, timeout=1)
                    print(f"Connected to {port}")
                    send_info(device + " port initialized")
                    return temp_ser
                except serial.SerialException:
                    print(f"Port {port} not available. Trying the next one.")
            next_try_after += 10 * (next_try_after < MAX_RETRY_TIME)
            print(f"No available ports, tried up to {max_port_number} port(s)."
                  f" Retry count: {retries}, Next retrying in {next_try_after} seconds...")
            send_warning(f"{device} port not initialized, retry count: {retries},"
                         f" retry in {next_try_after} seconds")
            time.sleep(next_try_after)
            if retries < MAX_RETRIES or "USB" not in device:
                return update_serial_port(device, next_try_after,
                                          retries + (next_try_after == MAX_RETRY_TIME))
            send_warning(f"Skipping port: {device} as max reties reached")
            return "max reties reached!"
    except Exception as usp_e: # pylint: disable=broad-except
        send_error("Some thing bad happened in: update_serial_port: error: " + usp_e)
        return None

def send_to_serial_port(serial_data):
    """Will send string as it is to TTGO-TCall"""
    try:
        if "max reties reached!" in SERIAL_PORT:
            return
        print(f"Sending data to serial port: {serial_data}")
        SERIAL_PORT.write(serial_data.encode())
    except serial.SerialException as e: # pylint: disable=broad-except
        send_error("error in watcher: send_to_SERIAL_PORT"+ e)


#LED related functionality =>

def led(state):
    """Change led state"""
    if state:
        led_on()
    else:
        led_off()


def led_on():
    "to turn LED on"
    global LED_STATE # pylint: disable=global-statement
    LED_STATE = True
    send_to_serial_port("led on")

def led_off():
    "to turn LED off"
    global LED_STATE  # pylint: disable=global-statement
    LED_STATE = False
    send_to_serial_port("led off")

def flash(n=1, delay=1):
    """to flash led"""
    for _ in range(n):
        thread_led_on = threading.Thread(target=led_on)
        thread_led_on.start()
        while thread_led_on.is_alive():
            time.sleep(delay)
        thread_led_off = threading.Thread(target=led_off)
        thread_led_off.start()
        while thread_led_off.is_alive():
            time.sleep(1)


# Buzzer related functionality =>

def buzzer(state):
    "Change buzzer state"
    if state:
        buzzer_on()
    else:
        buzzer_off()

def buzzer_on():
    "to turn Buzzer on"
    global BUZZER_STATE  # pylint: disable=global-statement
    BUZZER_STATE = True
    send_to_serial_port("buzzer on")

def buzzer_off():
    "to turn Buzzer off"
    global BUZZER_STATE  # pylint: disable=global-statement
    BUZZER_STATE = False
    send_to_serial_port("buzzer off")

def blink(n=1, delay=1000):
    """Blink LED for n times."""
    print(f"Blink is called with params: n: {n} and delay: {delay}")
    send_to_serial_port(f"blink for {{{n}}} delay: [{delay}]")

def beep():
    """to beep"""
    t = threading.Thread(target=buzzer_on)
    while t.is_alive():
        time.sleep(2)
    t = threading.Thread(target=buzzer_off)
    while t.is_alive():
        time.sleep(1)

def watcher(): #pylint: disable=too-many-branches
    """Deal with api calls"""
    send_info(f"API called with params: {request.args}")
    variable_value = None

    # print(f"API called received with data: {request.args}")
    # Check if 'led' or 'buzzer' parameter is in the query string
    if 'led' in request.args:
        variable_value = request.args['led']
        print(f"\n\n\tLed power: {variable_value}")
        if "on" in variable_value:
            led_on()
        elif "off" in variable_value:
            led_off()
        elif "toggle" in variable_value:
            if LED_STATE:
                led_off()
            else:
                led_on()
        else:
            print("\t\t!__Unknown input__!")
    elif 'buzzer' in request.args:
        variable_value = request.args['buzzer']
        print(f"\n\n\tBuzzer power: {variable_value}")
        if "on" in variable_value:
            buzzer_on()
        elif "off" in variable_value:
            buzzer_off()
        elif "toggle" in variable_value:
            if BUZZER_STATE:
                buzzer_off()
            else:
                buzzer_on()
        else:
            print("\t\t!__Unknown input__!")
    else:
        # Handle case when no variable is provided in the query string
        if 'status' in request.args:
            return jsonify({'LED': LED_STATE, 'BUZZER': BUZZER_STATE})
        else:
            print(f"Error happens in API call args data: {request.args}")
            return "No variable provided", 400  # Return HTTP status code 400 for Bad Request

    # Return a response indicating the variable name and value
    return jsonify({'LED': LED_STATE, 'BUZZER': BUZZER_STATE})

# def beep(number_of_beeps, beep_for):
if __name__ == '__main__':
    t1 = threading.Thread(target=initialize_port)
    t1.start()
    while t1.is_alive():
        time.sleep(1)

    t2 = threading.Thread(target=blink, args=(2,400))
    t2.start()
    while t2.is_alive():
        time.sleep(1)

    t3 = threading.Thread(target=blink, args=(4,100))
    t3.start()
    while t3.is_alive():
        time.sleep(1)
