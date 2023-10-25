#version: 1.0.1
#Version notes: app.py will now start communicating with module
from flask import Flask, render_template, request
import serial
import serial.tools.list_ports

app = Flask(__name__)

# Function to get a list of available serial ports
# Modify the get_serial_ports function
def get_serial_ports():
    return [{'port': port.device, 'baud_rate': 115200} for port in serial.tools.list_ports.comports() if port.device.startswith('/dev/tty')]

# Replace with the default serial port
default_serial_port = '/dev/ttyACM0'
ser = None

# Attempt to open the default serial port
try:
    ser = serial.Serial(default_serial_port, 115200)
except serial.SerialException:
    pass  # Handle the exception if the default port is not accessible

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6677, debug=True)
    schedule.run_pending()
