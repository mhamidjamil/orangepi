
#$ last work 03/Dec/23 [06:07 PM]
## version 1.0.9.6
## Release Note : NGROK part scheduling depreciated

from flask import Flask, render_template, request
import serial
import serial.tools.list_ports
import schedule
import threading
import time
from routes.serial_handler import set_serial_object, read_serial_data, update_time, update_namaz_time, send_ngrok_link
from routes.routes import send_auth

app = Flask(__name__)

# Function to get a list of available serial ports
# Modify the get_serial_ports function
def get_serial_ports():
    return [{'port': port.device, 'baud_rate': 115200} for port in serial.tools.list_ports.comports() if port.device.startswith('/dev/tty')]

# Replace with the default serial port
default_serial_port = '/dev/ttyACM0'
ser = None
try:
    ser = serial.Serial(default_serial_port, 115200)
    set_serial_object(ser)
except serial.SerialException as e:
    print(f"An error occurred while opening the serial port: {e}")
    ser = None

@app.route('/')
def index():
    # Get a list of available serial ports with default baud rate
    available_ports = get_serial_ports()

    # Baud rates to be displayed in the dropdown
    baud_rates = [9600, 115200, 230400, 460800, 921600]

    return render_template('index.html', default_port=default_serial_port, available_ports=available_ports, baud_rates=baud_rates)

@app.route('/read_serial')
def read_serial():
    if ser:
        try:
            data = ser.readline().decode('utf-8')
            read_serial_data(data)

            return {'data': data.strip()}  # Strip whitespace from the data
        except UnicodeDecodeError:
            return {'error': 'Error decoding serial data'}
    else:
        return {'error': 'Serial port not accessible'}

@app.route('/send_serial', methods=['POST'])
def send_serial():
    data_to_send = request.form['data']
    ser.write(data_to_send.encode('utf-8'))
    return {'status': 'success'}

@app.route('/send_auth', methods=['GET'])
def send_auth_route():
    return send_auth()

schedule.every(2).minutes.do(update_time)
schedule.every(1).minutes.do(update_namaz_time)

def update_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# def delayed_execution():
#     # Delay for 5 seconds
#     time.sleep(20)
#     # Call the function after the delay
#     send_ngrok_link()

if __name__ == '__main__':
    thread = threading.Thread(target=update_schedule)
    thread.start()
    # timer_thread = threading.Timer(5, delayed_execution)
    # timer_thread.start()
    app.run(host='0.0.0.0', port=6677, debug=True)
