from flask import Flask, render_template, request
import serial

app = Flask(__name__)
# Replace with your actual serial port
ser = serial.Serial('/dev/ttyUSB0', 9600)


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
