# serial_handler.py
"""This script is will communicate with Watcher"""
import time
import serial
import serial.tools.list_ports
from communication.ntfy import send_warning, send_error, send_info #pylint: disable=relative-beyond-top-level

SERIAL_PORT = None

def initialize_port():
    """This part will initialize serial port for watcher"""
    global SERIAL_PORT # pylint: disable=global-statement
    SERIAL_PORT = update_serial_port("/dev/ttyUSB")

def update_serial_port(device):
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
                    send_info("Watcher port initialized")
                    return temp_ser
                except serial.SerialException:
                    print(f"Port {port} not available. Trying the next one.")

            print(f"No available ports (tried up to {max_port_number}). Retrying in 10 seconds...")
            time.sleep(10)
            send_warning("watcher port not initialized retry in 10 seconds")
            update_serial_port("/dev/ttyUSB")
    except Exception as usp_e: # pylint: disable=broad-except
        send_error("Some thing bad happened in: update_serial_port: error: " + usp_e)
        return None

def send_to_serial_port(serial_data):
    """Will send string as it is to TTGO-TCall"""
    try:
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

def flash():
    """to flash led"""
    led_on()
    time.sleep(5)
    led_off()

# Buzzer related functionality =>

def buzzer_on():
    "to turn Buzzer on"
    send_to_serial_port("buzzer on")

def buzzer_off():
    "to turn Buzzer off"
    send_to_serial_port("buzzer off")

def beep():
    """to beep"""
    buzzer_on()
    time.sleep(3)
    buzzer_off()

# def beep(number_of_beeps, beep_for):
if __name__ == '__main__':
    initialize_port()
    time.sleep(5)
    # flash()
    beep()
