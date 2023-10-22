from flask import Flask, render_template, request
import serial

app = Flask(__name__)
# Replace with your actual serial port
def get_serial_ports():
    result = subprocess.run(['ls', '/dev'], capture_output=True, text=True)
    output = result.stdout.split('\n')
    serial_ports = [port for port in output if 'tty' in port]
    return serial_ports

# Set the default serial port
ser = serial.Serial('/dev/ttyACM0', 115200)

# Add a route to handle the serial port selection
@app.route('/get_serial_ports', methods=['POST'])
def select_port():
    selected_port = request.form['port']
    if selected_port in get_serial_ports():
        ser.port = selected_port
    return 'Serial port updated successfully'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/read_serial')
def read_serial():
    data = ser.readline().decode('utf-8')
    return {'data': data}


@app.route('/send_serial', methods=['POST'])
def send_serial():
    data_to_send = request.form['data']
    ser.write(data_to_send.encode('utf-8'))
    return {'status': 'success'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6677, debug=True)
