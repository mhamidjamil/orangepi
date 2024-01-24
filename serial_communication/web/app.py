

#$ last work 25/Jan/24 [01:22 AM]
## version 2.0.4
## Release Note : Boot-up msg and ngrok rework

from flask import Flask, render_template, request
import serial
import serial.tools.list_ports
import schedule
import threading
import time
from routes.serial_handler import set_serial_object, read_serial_data, update_time, update_namaz_time, send_ngrok_link, say_to_serial, is_ngrok_link_sent, send_message, fetch_current_time_online
from routes.routes import send_auth
bg_tasks = True
boot_up_message_send = False

app = Flask(__name__)

# Function to get a list of available serial ports
# Modify the get_serial_ports function
def get_serial_ports():
    return [{'port': port.device, 'baud_rate': 115200} for port in serial.tools.list_ports.comports() if port.device.startswith('/dev/tty')]

# Function to update the serial port dynamically
def update_serial_port():
    global bg_tasks, ser
    max_port_number = 5  # Maximum port number to try
    port_pattern = '/dev/ttyACM{}'
    print("Trying to connect to port!")
    while True:
        for port_number in range(max_port_number):
            port = port_pattern.format(port_number)
            try:
                temp_ser = serial.Serial(port, baudrate=115200, timeout=1)
                ser = temp_ser
                print(f"Connected to {port}")
                set_serial_object(ser)
                bg_tasks = True
                return temp_ser
            except serial.SerialException:
                print(f"Port {port} not available. Trying the next one.")

        print(f"No available ports (tried up to {max_port_number}). Retrying in 10 seconds...")
        time.sleep(10)
        update_serial_port() #TODO: this effect execution flow

# Replace with the default serial port
ser = update_serial_port()

@app.route('/')
def index():
    # Get a list of available serial ports with default baud rate
    available_ports = get_serial_ports()

    # Baud rates to be displayed in the dropdown
    baud_rates = [9600, 115200, 230400, 460800, 921600]

    return render_template('index.html', default_port=ser, available_ports=available_ports, baud_rates=baud_rates)

@app.route('/read_serial')
def read_serial():
    global bg_tasks
    try:
        if ser:
            try:
                data = ser.readline().decode('utf-8')
                read_serial_data(data)

                return {'data': data.strip()}  # Strip whitespace from the data
            except UnicodeDecodeError:
                return {'error': 'Error decoding serial data'}
        else:
            return {'error': 'Serial port not accessible'}
    except serial.SerialException as e:
        print(f"#1: Error reading from serial port: {e}")
        bg_tasks = False
        update_serial_port()
        return {'error': 'Error reading from serial port'}

@app.route('/send_serial', methods=['POST'])
def send_serial():
    data_to_send = request.form['data']
    ser.write(data_to_send.encode('utf-8'))
    return {'status': 'success'}

@app.route('/send_auth', methods=['GET'])
def send_auth_route():
    return send_auth()

if bg_tasks: 
    schedule.every(2).minutes.do(update_time) 
    schedule.every(5).minutes.do(update_namaz_time) #TODO: implement array

def update_schedule():
    while True:
        schedule.run_pending() # run background task after specified delay
        time.sleep(10)

def one_time_task():
    global boot_up_message_send
    # Delay the execution of send_ngrok_link() by 5 minutes
    
    # Check if send_ngrok_link() has not been called yet
    if not is_ngrok_link_sent():
        time.sleep(20)
        if not boot_up_message_send:
            send_message("Orange Pi just boot-up time stamp: "+ fetch_current_time_online())
            boot_up_message_send = True
        time.sleep(200)
        say_to_serial("sms sending?")
        time.sleep(500)
        send_ngrok_link()
# def delayed_execution():
#     # Delay for 5 seconds
#     time.sleep(20)
#     # Call the function after the delay
#     send_ngrok_link()

if __name__ == '__main__':
    thread = threading.Thread(target=update_schedule)
    thread2 = threading.Thread(target=one_time_task)
    thread.start()
    thread2.start()
    # timer_thread = threading.Timer(5, delayed_execution)
    # timer_thread.start()
    app.run(host='0.0.0.0', port=6677, debug=True)
