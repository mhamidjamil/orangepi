# serial_handler.py

import requests
import datetime
import re
import time
from bs4 import BeautifulSoup
from pyngrok import ngrok
import subprocess
import os
from dotenv import load_dotenv
import serial
ngrok_link_sent = False

EXCEPTION_LOGGER_FILE = "exception_logs"
EXTENSION_TYPE = ".txt"

def is_ngrok_link_sent():
    global ngrok_link_sent
    return ngrok_link_sent

def set_serial_object(serial_object):
    global ser
    ser = serial_object

load_dotenv()
ngrok_link = ""
logs_receiving = False
log_data = ""

ser = None

def reboot_system():
    password = os.getenv("MY_PASSWORD")
    if not password:
        raise ValueError("Password not set in the .env file")

    command = "sudo -S reboot"

    try:
        send_to_serial_port("sms Rebooting OP system...")
        subprocess.run(command, shell=True, input=f"{password}\n", text=True, check=True)
    except subprocess.CalledProcessError as e:
        exception_logger("reboot_system", e)

def send_ngrok_link():
    try:
        global ngrok_link
        stop_ngrok()
        time.sleep(2)
        ngrok.set_auth_token(os.getenv("NGROK_TOKEN"))

        # Open a Ngrok tunnel to your local development server
        tunnel = ngrok.connect(8069)

        # Extract the public URL from the NgrokTunnel object
        public_url = tunnel.public_url

        # Print the Ngrok URL
        print("Ngrok URL:", public_url)
        
        if public_url:
            print(f"Ngrok URL is available: {public_url}")
            send_to_serial_port("sms " + public_url)
            ngrok_link = public_url
            global ngrok_link_sent
            ngrok_link_sent = True
            # Perform other tasks with ngrok_url
        else:
            print("Failed to obtain Ngrok URL.")
            send_to_serial_port("sms Failed to obtain Ngrok URL.")
    except Exception as e:
        print("NGROK not initialized")
        write_in_file("ngrok_logger", "\nERROR:\n" + str(e))

def update_namaz_time():
    try:
        global current_time
        # Replace this URL with the actual URL of the prayer times for Lahore
        url = os.getenv("LAHORE_NAMAZ_TIME")
        
        # Fetch the HTML content of the webpage
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Fetch the current time online
        try:
            response = requests.get('http://worldtimeapi.org/api/timezone/Asia/Karachi')
            data = response.json()
            current_time = datetime.datetime.fromisoformat(data['datetime'])
            current_time = current_time.strftime("%I:%M %p")
            # return "10:00 AM"
        except requests.exceptions.RequestException as e:
            exception_logger("part_of_update_namaz_time", e)
            return
        
        if not current_time:
            print("Failed to fetch current time online.")
            return
        # else:
            # print(f"Current time: {current_time}")

        # Find the prayer time row that corresponds to the next prayer after the current time
        prayer_times = soup.find_all('td', {'data-label': True})
        next_prayer = None

        for time in prayer_times:
            prayer_time = time.text.strip()
            if datetime.datetime.strptime(prayer_time, '%I:%M %p') > datetime.datetime.strptime(current_time, '%I:%M %p'):
                next_prayer = time['data-label']
                break

        # Print and send the next prayer time to the ser terminal
        if next_prayer:
            message = f"{next_prayer}: {prayer_time}"
            print(message)
            say_to_serial (f"{next_prayer}: {prayer_time}")
            # Replace the following line with code to send the message to /dev/ttyUSB1
        else:
            fajr_element = soup.find('td', {'data-label': 'Fajr'})
            if fajr_element:
                fajr_time = fajr_element.text.strip()
                fajr_time_obj = datetime.datetime.strptime(fajr_time, '%I:%M %p') - datetime.timedelta(minutes=2)
                print(f"Fajr: {fajr_time_obj.strftime('%I:%M %p')} (?)")
                say_to_serial("Fajr: "+fajr_time_obj.strftime('%I:%M %p'))
            else:
                print("Failed to find Fajr time.")
                return None
    except Exception as e:
        exception_logger("update_namaz_time", e)

def read_serial_data(data):
    global logs_receiving, log_data
    try:
        global ngrok_link
        if "{hay orange-pi!" in data or logs_receiving:
            if "[#SaveIt]:" in data or logs_receiving:
                logs_receiving = True
                print("receiving logs...")
                log_data += data
                if "end_of_file" in data:
                    logs_receiving = False
                    print("logs received saving them")
                    write_in_file("logs.txt", "\nLogs:\n" + log_data + "\nTime stamp: {"+fetch_current_time_online()+ "}\n")
                    log_data = ""
            elif "send time" in data or "update time" in data or "send updated time" in data:
                update_time()
            elif "send ip" in data or "update ip" in data or "my ip" in data:
                ip = requests.get('https://api.ipify.org').text
                msg = '{hay ttgo-tcall! here is the ip: ' + ip + '.}'
                print(f"sending : {msg}")
                send_to_serial_port(msg)
            elif "untrained_message:" in data:
                temp_str = re.search(r'untrained_message:(.*?) from', data).group(1).strip()
                sender_number = re.search(r'from : {_([^_]*)_', data).group(1)
                new_message_number = re.search(r'<_(\d+)_>', data).group(1)

                print(f"Extracted message: {temp_str}")
                print(f"Extracted sender_number: {sender_number}")
                print(f"Extracted new_message_number: {new_message_number}")
                if "restart op" in temp_str:
                    print(f"Asking TTGO to delete the message {new_message_number} and rebooting the system...")
                    send_to_serial_port("delete " + new_message_number)
                    time.sleep(3)
                    reboot_system()
                elif "send ngrok link" in temp_str:
                    print(f"Asking TTGO to delete the message {new_message_number} and sending ngrok link...")
                    send_to_serial_port("delete " + new_message_number)
                    print(f"ngrok link: {ngrok_link}")
                    send_ngrok_link()
            elif "send bypass key" in data: 
                say_to_serial("bypass key: " + os.getenv("BYPASS_KEY"))
            else:
                print(f"unknown keywords in command: {data}")
    except Exception as e:
        exception_logger("read_serial_data", e)

def fetch_current_time_online(): #TODO: need to separate this part from py_time
    try:
        response = requests.get('http://worldtimeapi.org/api/timezone/Asia/Karachi')
        data = response.json()
        current_time = datetime.datetime.fromisoformat(data['datetime'])
        formatted_time = current_time.strftime("%y/%m/%d,%H:%M:%S")
        return f"py_time:{formatted_time}+20"
    except requests.exceptions.RequestException as e:
        exception_logger("fetch_current_time_online", e)
        return None

def say_to_serial(serial_data):
    try:
        serial_data = "{hay ttgo-tcall!"+serial_data+"}"
        print(f"sending : {serial_data}")
        send_to_serial_port(serial_data)
    except Exception as e:
        exception_logger("say_to_serial", e)

def send_to_serial_port(serial_data):
    # global serial
    try:
        print(f"Sending data to serial port: {serial_data}")
        ser.write(serial_data.encode())
    except serial.SerialException as e:
        exception_logger("send_to_serial_port", e)

def update_time():
    try:
        current_time = fetch_current_time_online()
        if current_time:
            print(f"Current time in Karachi: {current_time}")
            send_to_serial_port(current_time)
        else:
            print("Failed to fetch current time.")
    except Exception as e:
        exception_logger("update_time", e)

def stop_ngrok():
    try:
        print("killing ngrok server...")
        subprocess.run(['pkill', '-f', 'ngrok'])
    except Exception as e:
        exception_logger("stop_ngrok", e)

def send_message(message):
    try:
        send_to_serial_port("sms " + message)
    except Exception as e:
        exception_logger("send_message", e)

def write_in_file(file_path, content):
    file_path += EXTENSION_TYPE
    content ="\n\n------------------------------\n"+content+"\n"+"{time: " + fetch_current_time_online()+"}\n--------------------------------\n"
    try:
        with open(file_path, 'a') as file:
            file.write(content)
            file.flush()  # Ensure the data is written to the file immediately
    except PermissionError as pe:
        # If PermissionError occurs, try to create the file in the current working directory
        current_directory = os.getcwd()
        file_path = os.path.join(current_directory, file_path)

        with open(file_path, 'a') as file:
            file.write(content)
            file.flush()  # Ensure the data is written to the file immediately
    except FileNotFoundError:
        # Handle the case where the file doesn't exist
        with open(file_path, 'w') as file:
            file.write(content)
            file.flush()  # Ensure the data is written to the file immediately
    except Exception as ex:
        # Handle other exceptions if needed
        print(f"An error occurred: {ex}")

def connected_with_internet():
    while True:
        try:
            # Check internet connectivity by pinging Google's public DNS server
            subprocess.run(['ping', '-c', '1', '8.8.8.8'], check=True)
            print("Internet is connected.")
            return True
        except subprocess.CalledProcessError:
            print("No internet connectivity. Retrying in 5 minutes...")
            # Sleep for 5 minutes before checking again
            time.sleep(300)
            connected_with_internet()

def exception_logger(function_name, error):
    if connected_with_internet():
        print(f"\n\t\t-----------------------------------------\nHandled Error:\nError occurred: {error} \nin {function_name} function\n\n")
        write_in_file(EXCEPTION_LOGGER_FILE, "Exception occur in{"+function_name+"} function.\n Error message: " + str(error))
# if __name__ == '__main__':
#     update_namaz_time()