# serial_handler.py
"""Module for handling serial communication."""
import datetime
import re
import time
import subprocess
import threading
import os
from bs4 import BeautifulSoup
from pyngrok import ngrok
from dotenv import load_dotenv
import serial
import requests
from .communication.ntfy import send_warning, send_error, send_info #pylint: disable=relative-beyond-top-level

load_dotenv()
CURRENT_NGROK_LINK = None
LOGS_RECEIVING = False
LOG_DATA = ""
SERIAL_PORT = None
NGROK_LINK_SENT = False
EXCEPTION_LOGGER_FILE_NAME = "exception_logs"
EXTENSION_TYPE = ".txt"
DEFAULT_PORT = 8069
SECONDARY_NUMBER_FOR_NGROK = os.getenv("_SECONDARY_NUMBER_FOR_NGROK_")
SEND_MESSAGE_TO_SECONDARY_NUMBER = os.getenv("_SEND_MESSAGE_TO_SECONDARY_NUMBER_")
MESSAGE_SEND_TO_CUSTOM_NUMBER = False


def is_ngrok_link_sent():
    """method to know if the NGROK link is send or not"""
    return NGROK_LINK_SENT


def set_serial_object(serial_object):
    """Define serial port for this file"""
    global SERIAL_PORT # pylint: disable=global-statement
    SERIAL_PORT = serial_object


def reboot_system():
    """Used to reboot the system on message"""
    password = os.getenv("MY_PASSWORD")
    if not password:
        raise ValueError("Password not set in the .env file")

    command = "sudo -S reboot"

    try:
        send_to_serial_port("sms Rebooting OP system...")
        subprocess.run(command, shell=True,
                       input=f"{password}\n", text=True, check=True)
    except subprocess.CalledProcessError as e:
        exception_logger("reboot_system", e)


def send_ngrok_link(target_port=None):
    """Will send NGROK link via message"""
    try:
        global CURRENT_NGROK_LINK, NGROK_LINK_SENT # pylint: disable=global-statement
        if CURRENT_NGROK_LINK is None or target_port is not None:
            #if function is called first time or with custom targer_port number
            stop_ngrok()
            time.sleep(2)
            ngrok.set_auth_token(os.getenv("NGROK_TOKEN"))

            # Open a Ngrok tunnel to your local development server
            ngrok_port = target_port if target_port is not None else DEFAULT_PORT
            tunnel = ngrok.connect(ngrok_port)

            # Extract the public URL from the NgrokTunnel object
            public_url = tunnel.public_url
            CURRENT_NGROK_LINK = public_url

            # Print the Ngrok URL
            print("Ngrok URL:", public_url)
        else:
            time.sleep(3)

        if CURRENT_NGROK_LINK:
            print(f"Ngrok URL is available: {CURRENT_NGROK_LINK}")
            time.sleep(5)
            send_message(CURRENT_NGROK_LINK)
            send_info(f"ngrok link: {CURRENT_NGROK_LINK}")
            NGROK_LINK_SENT = True
            def send_to_secondary():
                global MESSAGE_SEND_TO_CUSTOM_NUMBER # pylint: disable=global-statement
                if SEND_MESSAGE_TO_SECONDARY_NUMBER is True and not MESSAGE_SEND_TO_CUSTOM_NUMBER:
                    time.sleep(10)
                    print("Sending ngrok link to secondary number"
                        f"\t ? allowed: {SEND_MESSAGE_TO_SECONDARY_NUMBER}")
                    send_custom_message(CURRENT_NGROK_LINK, SECONDARY_NUMBER_FOR_NGROK)
                    MESSAGE_SEND_TO_CUSTOM_NUMBER = True

            # Start a new thread to send the message to the secondary number
            thread = threading.Thread(target=send_to_secondary)
            thread.start()

            # Wait for the thread to finish before proceeding with the main thread
            thread.join()

            # Perform other tasks with ngrok_url
        else:
            print("Failed to obtain Ngrok URL.")
            send_to_serial_port("sms Failed to obtain Ngrok URL.")
    except Exception as e: # pylint: disable=broad-except
        print("NGROK not initialized")
        write_in_file("ngrok_logger", "\nERROR:\n" + str(e))


def update_namaz_time():
    """Will update update namaz time on TTGO-TCall"""
    try:
        current_time = ""
        # Replace this URL with the actual URL of the prayer times for Lahore
        url = os.getenv("LAHORE_NAMAZ_TIME")

        # Fetch the HTML content of the webpage
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Fetch the current time online
        try:
            response = requests.get(
                'http://worldtimeapi.org/api/timezone/Asia/Karachi', timeout=10)
            data = response.json()
            current_time = datetime.datetime.fromisoformat(data['datetime'])
            current_time = current_time.strftime("%I:%M %p")
            # return "10:00 AM"
        except requests.exceptions.RequestException as e:
            exception_logger("part_of_update_namaz_time", e)
            return None

        if not current_time:
            print("Failed to fetch current time online.")
            return None

        # Find the prayer time row that corresponds to the next prayer after the current time
        prayer_times = soup.find_all('td', {'data-label': True})
        next_prayer_name = None #refer to prayer name
        next_prayer_time = None

        for prayer_time in prayer_times:
            next_prayer_time = prayer_time.text.strip()
            if (datetime.datetime.strptime(next_prayer_time, '%I:%M %p') >
                    datetime.datetime.strptime(current_time, '%I:%M %p')):

                next_prayer_name = prayer_time['data-label']
                break

        # Print and send the next prayer time to the SERIAL_PORT terminal
        if next_prayer_name:
            print(f"{next_prayer_name}: {next_prayer_time}")
            say_to_serial(f"{next_prayer_name}: {next_prayer_time}")
        else:
            fajr_element = soup.find('td', {'data-label': 'Fajr'})
            if fajr_element:
                fajr_time = fajr_element.text.strip()
                fajr_time_obj = datetime.datetime.strptime(
                    fajr_time, '%I:%M %p') - datetime.timedelta(minutes=2)
                print(f"Fajr: {fajr_time_obj.strftime('%I:%M %p')} (?)")
                say_to_serial("Fajr: "+fajr_time_obj.strftime('%I:%M %p'))
            else:
                print("Failed to find Fajr time.")
        return None
    except Exception as e: # pylint: disable=broad-except
        exception_logger("update_namaz_time", e)
        return None


def read_serial_data(data):
    """read TTGO-Tcall serial data"""
    global LOGS_RECEIVING, LOG_DATA # pylint: disable=global-statement
    try:
        if "{hay orange-pi!" in data or LOGS_RECEIVING:
            if "[#SaveIt]:" in data or LOGS_RECEIVING:
                LOGS_RECEIVING = True
                print("receiving logs...")
                LOG_DATA += data
                if "end_of_file" in data:
                    LOGS_RECEIVING = False
                    print("logs received saving them")
                    write_in_file("logs.txt", LOG_DATA)
                    LOG_DATA = ""
            elif "send time" in data or "update time" in data or "send updated time" in data:
                update_time()
            elif "send ip" in data or "update ip" in data or "my ip" in data:
                ip = requests.get('https://api.ipify.org', timeout=10).text
                msg = '{hay ttgo-tcall! here is the ip: ' + ip + '.}'
                print(f"sending : {msg}")
                send_to_serial_port(msg)
            elif "untrained_message:" in data:
                temp_str = re.search(
                    r'untrained_message:(.*?) from', data).group(1).strip()
                sender_number = re.search(r'from : {_([^_]*)_', data).group(1)
                new_message_number = re.search(r'<_(\d+)_>', data).group(1)

                print(f"Extracted message: {temp_str}")
                print(f"Extracted sender_number: {sender_number}")
                print(f"Extracted new_message_number: {new_message_number}")
                process_untrained_message(temp_str, new_message_number)
            elif "send bypass key" in data:
                say_to_serial("bypass key: " + os.getenv("BYPASS_KEY"))
            else:
                print(f"unknown keywords in command: {data}")
    except Exception as e: # pylint: disable=broad-except
        exception_logger("read_serial_data", e)

def process_untrained_message(temp_str, new_message_number):
    """Untrained messages will be executed and deleted from stack"""
    try:
        send_warning(f"untrained message received from {new_message_number} working on it.")
        if "restart op" in temp_str or "restart" in temp_str:
            print(
                f"Asking TTGO to delete the message "
                f"{new_message_number} and rebooting the system...")
            send_to_serial_port("delete " + new_message_number)
            time.sleep(3)
            reboot_system()
        elif "send ngrok link" in temp_str:
            print(
                f"Asking TTGO to delete the message "
                f"{new_message_number} and sending ngrok link...")
            send_to_serial_port("delete " + new_message_number)
            time.sleep(2)
            send_ngrok_link()
            print(f"ngrok link: {CURRENT_NGROK_LINK}")
        elif "send new ngrok link" in temp_str:
            print(
                f"Asking TTGO to delete the message "
                f"{new_message_number} and sending ngrok link...")
            send_to_serial_port("delete " + new_message_number)
            time.sleep(2)
            send_ngrok_link(DEFAULT_PORT)
            print(f"ngrok link: {CURRENT_NGROK_LINK}")
        elif "ngrok on" in temp_str:
            match = re.search(r'ngrok on (\d+)', temp_str)
            custom_port_number = int(match.group(1))
            print(
                f"Asking TTGO to delete the message "
                f"{new_message_number} and sending ngrok link"
                f" for port {custom_port_number}...")
            send_to_serial_port("delete " + new_message_number)
            time.sleep(3)
            send_ngrok_link(custom_port_number)
            print(f"ngrok link: {CURRENT_NGROK_LINK}")
    except Exception as e: # pylint: disable=broad-except
        exception_logger("process_untrained_message", e)

def fetch_current_time_online():
    # TODO: need to separate this part from py_time # pylint: disable=fixme
    """Return current time after fetching from online source for TTGO-TCall"""
    try:
        response = requests.get(
            'http://worldtimeapi.org/api/timezone/Asia/Karachi', timeout=10)

        data = response.json()
        current_time = datetime.datetime.fromisoformat(data['datetime'])
        formatted_time = current_time.strftime("%y/%m/%d,%H:%M:%S")
        return f"py_time:{formatted_time}+20"
    except requests.exceptions.RequestException as e:
        exception_logger("fetch_current_time_online", e)
        return None


def say_to_serial(serial_data):
    """This will convert the incoming string to the proper message so 
    ttgo can understand that orange pi is communicating with it"""
    try:
        serial_data = "{hay ttgo-tcall!"+serial_data+"}"
        print(f"sending : {serial_data}")
        send_to_serial_port(serial_data)
    except Exception as e: # pylint: disable=broad-except
        exception_logger("say_to_serial", e)


def send_to_serial_port(serial_data):
    """Will send string as it is to TTGO-TCall"""
    try:
        print(f"Sending data to serial port: {serial_data}")
        SERIAL_PORT.write(serial_data.encode())
    except serial.SerialException as e: # pylint: disable=broad-except
        exception_logger("send_to_serial_port", e)


def update_time():
    """Will send updated time to TTGO-TCall"""
    try:
        current_time = fetch_current_time_online()
        if current_time:
            print(f"Current time in Karachi: {current_time}")
            send_to_serial_port(current_time)
        else:
            print("Failed to fetch current time.")
    except Exception as e: # pylint: disable=broad-except
        exception_logger("update_time", e)


def stop_ngrok():
    """Need to kill NGROK if it is already running"""
    try:
        print("killing ngrok server (if running)...")
        subprocess.run(['pkill', '-f', 'ngrok'], check=False)
    except Exception as e: # pylint: disable=broad-except
        exception_logger("stop_ngrok", e)


def send_custom_message(message, number):
    """Used to send message to custom number"""
    try:
        print("Sending custom message request from orange-pi!")
        send_to_serial_port("smsTo [" + message + "]{" + number + "}")
    except Exception as e: # pylint: disable=broad-except
        exception_logger("send_message", e)


def send_message(message):
    """Used to send sms to defined number"""
    try:
        print("Sending message request from orange-pi")
        send_to_serial_port("sms " + message)
    except Exception as e: # pylint: disable=broad-except
        exception_logger("send_message", e)


def write_in_file(file_name, content):
    # return False
    """Will write data in file"""
    file_name = os.path.join(os.environ['LOG_FILE_PATH'], file_name + EXTENSION_TYPE)
    content = "\n\n------------------------------>\n" + content + "\n" + \
        "{time: " + fetch_current_time_online() + "}\n<--------------------------------\n"
    try:
        with open(file_name, 'a', encoding='utf-8') as file:
            file.write(content)
            file.flush()  # Ensure the data is written to the file immediately
        return True
    except Exception as ex: # pylint: disable=broad-except
        # Handle other exceptions if needed
        print(f"An error occurred: {ex}")
        return False


def connected_with_internet():
    """If module is not connected with internet it will try to connect"""
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
    """Work as a logger (additional logging with function name)"""
    if connected_with_internet():
        send_error(f"Error in {function_name}"
                 f"Error message: {error} at: {fetch_current_time_online()}")
        msg = f"\n------------>\n Exception occur in {function_name} function." + \
                "\n Error message: " + str(error) + "\n<--------------\n"
        print(msg)

        if not write_in_file(EXCEPTION_LOGGER_FILE_NAME, msg):
            send_error(f"Unable to write error of {function_name} in logs")
            print("Issue in file writing")
    else:
        send_error("Not connected with internet!")

def sync_company_numbers():
    """This function will sync company numbers from ttgo module with local file"""
    # this part ill be completed after watcher will sync with SECO
