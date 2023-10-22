from flask import Flask, render_template, request
import serial

app = Flask(__name__)
# Replace with your actual serial port
@app.route('/get_serial_ports', methods=['GET'])
def get_serial_ports():
    try:
        # Execute the command and capture its output
        ignore_ subprocess.check_output("cd", shell=True, text=True)
        result = subprocess.check_output("ls /dev", shell=True, text=True)

        # Split the output by lines to get individual ports
        ports = result.split('\n')

        # Filter for serial-like port names
        serial_ports = [port for port in ports if 'tty' in port]

        return jsonify({'serial_ports': serial_ports})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
