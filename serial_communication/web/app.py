from flask import Flask, render_template, request
import serial
import serial.tools.list_ports

app = Flask(__name__)

# Function to get a list of available serial ports
def get_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

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
    # Get a list of available serial ports
    available_ports = get_serial_ports()

    return render_template('index.html', default_port=default_serial_port, available_ports=available_ports)


@app.route('/read_serial')
def read_serial():
    if ser:
        data = ser.readline().decode('utf-8')
        return {'data': data}
    else:
        return {'error': 'Serial port not accessible'}


@app.route('/send_serial', methods=['POST'])
def send_serial():
    if ser:
        data_to_send = request.form['data']
        ser.write(data_to_send.encode('utf-8'))
        return {'status': 'success'}
    else:
        return {'error': 'Serial port not accessible'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6677, debug=True)
