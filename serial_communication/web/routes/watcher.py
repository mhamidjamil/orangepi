# serial_handler.py
"""This script is will communicate with Watcher"""
import time
import threading
import serial
import serial.tools.list_ports
from .communication.ntfy import send_warning, send_error, send_info #pylint: disable=relative-beyond-top-level

SERIAL_PORT = None
MAX_RETRIES = 2
MAX_RETRY_TIME = 30

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


def led_on():
    "to turn LED on"
    send_to_serial_port("led on")

def led_off():
    "to turn LED off"
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

def buzzer_on():
    "to turn Buzzer on"
    send_to_serial_port("buzzer on")

def buzzer_off():
    "to turn Buzzer off"
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
