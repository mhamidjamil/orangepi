import requests
import datetime
import serial


def fetch_current_time_online():
    try:
        response = requests.get(
            'http://worldtimeapi.org/api/timezone/Asia/Karachi')
        data = response.json()
        current_time = datetime.datetime.fromisoformat(data['datetime'])
        formatted_time = current_time.strftime("%y/%m/%d,%H:%M:%S")
        return f"py_time:{formatted_time}+20"
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def send_to_serial_port(serial_data):
    try:
        ser = serial.Serial('/dev/ttyACM0', 115200)
        ser.write(serial_data.encode())
        ser.close()
    except serial.SerialException as e:
        print(f"An error occurred while sending data to serial port: {e}")


if __name__ == "__main__":
    current_time = fetch_current_time_online()
    if current_time:
        print(f"Current time in Karachi: {current_time}")
        send_to_serial_port(current_time)
    else:
        print("Failed to fetch current time.")
