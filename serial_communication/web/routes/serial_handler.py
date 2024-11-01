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
import requests
from flask import jsonify, request
from .communication.ntfy import send_warning, send_error, send_info, \
    send_api_info  #pylint: disable=relative-beyond-top-level

load_dotenv()
CURRENT_NGROK_LINK = None
LOGS_RECEIVING = False
LOG_DATA = ""
SERIAL_PORT = None
NGROK_LINK_SENT = False
EXCEPTION_LOGGER_FILE_NAME = "exception_logs"
EXTENSION_TYPE = ".txt"
DEFAULT_PORT = os.getenv("_DEFAULT_NGROK_PORT_")

SECONDARY_NUMBER_FOR_NGROK = os.getenv("_SECONDARY_NUMBER_FOR_NGROK_")
SEND_MESSAGE_TO_SECONDARY_NUMBER = os.getenv("_SEND_MESSAGE_TO_SECONDARY_NUMBER_")
MESSAGE_SEND_TO_CUSTOM_NUMBER = False
USE_MODULE_TIME = False

NEXT_PRAYER_TIME = None
NEXT_PRAYER_NAME = None
ESP32_URL = os.getenv("TTGO_TCALL_SERVER")
PRAYER_TIMES = {}


def is_ngrok_link_sent():
    """method to know if the NGROK link is send or not"""
    return NGROK_LINK_SENT


def set_serial_object(serial_object):
    """Define serial port for this file"""
    global SERIAL_PORT  # pylint: disable=global-statement
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
        global CURRENT_NGROK_LINK, NGROK_LINK_SENT  # pylint: disable=global-statement
        if CURRENT_NGROK_LINK is None or target_port is not None:
            #if function is called first time or with custom target_port number
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
                global MESSAGE_SEND_TO_CUSTOM_NUMBER  # pylint: disable=global-statement
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
    except Exception as e:  # pylint: disable=broad-except
        print("NGROK not initialized")
        write_in_file("ngrok_logger", "\nERROR:\n" + str(e))

def update_namaz_time():
    """Update namaz time by comparing with current system time."""

    try:
        current_time = fetch_current_time_online()
        current_time = datetime.datetime.strptime(current_time, "%y/%m/%d,%H:%M:%S")
        current_time_str = current_time.strftime("%I:%M %p")

        time_format = "%I:%M %p"
        datetime.datetime.strptime(current_time_str, time_format)

        # Fetch prayer times if not already fetched or after midnight
        if not PRAYER_TIMES or is_after_midnight(current_time):
            fetch_new_prayer_time()

        # Compare current time with the next prayer time
        find_next_prayer(current_time)
    except Exception as e:  # pylint: disable=broad-except
        exception_logger("update_namaz_time", e)


def fetch_new_prayer_time():
    """Fetch the next prayer time from the website and update global variables."""

    global PRAYER_TIMES  # pylint: disable=W0602

    try:
        url = os.getenv("LAHORE_NAMAZ_TIME")

        # Fetch the HTML content of the webpage
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Clear previous times
        PRAYER_TIMES.clear()

        # Parse the HTML to extract prayer times (based on your HTML structure)
        prayer_times_table = soup.find('table', {'class': 'timer_table'})
        prayer_rows = prayer_times_table.find_all('td')

        # Extract times for each prayer
        for row in prayer_rows:
            prayer_name = row.find('span').text.strip()
            prayer_time = row.text.strip().replace(prayer_name, '').strip()
            PRAYER_TIMES[prayer_name] = prayer_time

        print("Prayer times updated:", PRAYER_TIMES)

    except Exception as e: # pylint: disable=broad-except
        exception_logger("fetch_new_prayer_time", e)


def find_next_prayer(current_time):
    """Find the next upcoming prayer based on the current system time."""
    global NEXT_PRAYER_NAME, NEXT_PRAYER_TIME  # pylint: disable=global-statement

    try:
        time_format = "%I:%M %p"
        current_time_str = current_time.strftime(time_format)
        current_time_obj = datetime.datetime.strptime(current_time_str, time_format)

        # Debug: Show the current prayer times before comparison
        print("Current Prayer Times:", PRAYER_TIMES)

        for prayer_name, prayer_time in PRAYER_TIMES.items():
            # Clean up prayer time by removing any extraneous text and ensuring AM/PM is included
            cleaned_prayer_time = prayer_time.split()[0]  # Take only the time part (first entry)

            # Adding the correct AM/PM based on prayer name
            if prayer_name in ['Fajr', 'Sunrise', 'Dhuhr']:
                cleaned_prayer_time += ' AM'  # Morning prayers
            else:
                cleaned_prayer_time += ' PM'  # Afternoon/evening prayers

            cleaned_prayer_time = cleaned_prayer_time.strip()

            print(f"Checking prayer: {prayer_name}, cleaned time: {cleaned_prayer_time}")

            # Convert the cleaned prayer time to a datetime object
            try:
                prayer_time_obj = datetime.datetime.strptime(cleaned_prayer_time, time_format)
            except ValueError as e:
                print(f"Error parsing prayer time for {prayer_name}: {cleaned_prayer_time} - {e}")
                continue  # Skip to the next prayer time if parsing fails

            # Compare to current time
            if prayer_time_obj > current_time_obj:
                NEXT_PRAYER_NAME = prayer_name
                NEXT_PRAYER_TIME = cleaned_prayer_time
                break
        else:
            # If it's past Isha, the next prayer is tomorrow's Fajr
            fajr_time_obj = datetime.datetime.strptime(PRAYER_TIMES['Fajr'].split()[0] +
                            ' AM', time_format) - datetime.timedelta(minutes=5)
            NEXT_PRAYER_NAME = "Fajr"
            NEXT_PRAYER_TIME = fajr_time_obj.strftime(time_format)

        # Log or send to serial
        if NEXT_PRAYER_NAME:
            print(f"Next Prayer: {NEXT_PRAYER_NAME} at {NEXT_PRAYER_TIME}")
            say_to_serial(f"{NEXT_PRAYER_NAME}: {NEXT_PRAYER_TIME}")

    except Exception as e:  # pylint: disable=broad-except
        exception_logger("find_next_prayer", e)

def is_after_midnight(current_time):
    """Check if the current time is just after midnight (for refreshing prayer times)."""
    midnight_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight_time <= current_time <= (midnight_time + datetime.timedelta(minutes=5))


def read_serial_data(data):
    """read TTGO-Tcall serial data"""
    global LOGS_RECEIVING, LOG_DATA  # pylint: disable=global-statement
    try:
        if "{hay orange-pi!" in data or LOGS_RECEIVING:
            if "[#SaveIt]:" in data or LOGS_RECEIVING:
                LOGS_RECEIVING = True
                print("receiving logs...")
                LOG_DATA += data
                if "end_of_file" in data:
                    LOGS_RECEIVING = False
                    print("logs received saving them")
                    write_in_file("logs", LOG_DATA)
                    LOG_DATA = ""
            elif "send time" in data or "update time" in data or "send updated time" in data:
                update_time()
            elif "send ip" in data or "update ip" in data or "my ip" in data:
                ip = requests.get('https://api.ipify.org', timeout=10).text
                msg = '{hay ttgo-tcall! here is the ip: ' + ip + '.}'
                print(f"sending : {msg}")
                send_to_serial_port(msg)
            elif "untrained_message:" in data:
                print(f"Trying to understand untrained message[{data}]")
                message_pattern = r'_\[_([^]]+)_\]_'
                phone_number_pattern = r'_\{_(\+\d+)_\}_'
                index_pattern = r'_\(_(\d+)_\)_'

                message_match = re.search(message_pattern, data)
                phone_number_match = re.search(phone_number_pattern, data)
                index_match = re.search(index_pattern, data)

                # Storing the extracted data in variables
                message = message_match.group(1) if message_match else None
                phone_number = phone_number_match.group(1) if phone_number_match else None
                index = index_match.group(1) if index_match else None

                # Printing the extracted data
                print("Message:", message)
                print("Phone Number:", phone_number)
                print("Index:", index)
                process_untrained_message(message, phone_number)
            elif "send bypass key" in data:
                say_to_serial("bypass key: " + os.getenv("BYPASS_KEY"))
            else:
                print(f"unknown keywords in command: {data}")
    except Exception as e:  # pylint: disable=broad-except
        exception_logger("read_serial_data", e)


def process_untrained_message(message, sender_number):
    """Untrained messages will be executed and deleted from stack"""
    try:
        message_executed = False
        send_warning(f"untrained message received from {sender_number} working on it.")
        if "restart op" in message or "restart" in message:
            print(
                f"Asking TTGO to delete the message "
                f"{sender_number} and rebooting the system...")
            send_to_serial_port("delete " + sender_number)
            time.sleep(3)
            if "4888420" in sender_number or os.getenv("BYPASS_KEY") in message:
                reboot_system()
            else:
                send_error("Unauthorize person try to reboot"
                           f" message: {message}, number: {sender_number}")
        elif "send new ngrok link" in message or "resend ngrok link" in message:
            print(f"Asking TTGO to delete the message "
                  f"{sender_number} and sending ngrok link...")
            time.sleep(2)
            send_ngrok_link(DEFAULT_PORT)
            print(f"ngrok link: {CURRENT_NGROK_LINK}")
            message_executed = True
        elif "send ngrok link" in message:
            print(
                f"Asking TTGO to delete the message "
                f"{sender_number} and sending ngrok link...")
            time.sleep(2)
            send_ngrok_link()
            print(f"ngrok link: {CURRENT_NGROK_LINK}")
            message_executed = True
        elif "ngrok on" in message:
            match = re.search(r'ngrok on (\d+)', message)
            custom_port_number = int(match.group(1))
            print(
                f"Asking TTGO to delete the message "
                f"{sender_number} and sending ngrok link"
                f" for port {custom_port_number}...")
            time.sleep(3)
            send_ngrok_link(custom_port_number)
            print(f"ngrok link: {CURRENT_NGROK_LINK}")
            message_executed = True

        if message_executed:
            if "isDemo" not in message:
                send_to_serial_port("delete " + sender_number)
            else:
                print("Skipping demo message")
        else:
            print("Message is also not recognizable by python script")
            send_error("\n\t\t***\nMessage is also not recognizable by python script\n"
                       f" message: [{message}] send by {sender_number}\n\n")

    except Exception as e:  # pylint: disable=broad-except
        exception_logger("process_untrained_message", e)


def fetch_current_time_online():
    # TODO: need to separate this part from py_time # pylint: disable=fixme
    """Return current time after fetching from online source if required
        other wise it will send local time for TTGO-TCall"""
    try:
        global USE_MODULE_TIME  # pylint: disable=global-statement
        if not USE_MODULE_TIME:
            response = requests.get(
                'http://worldtimeapi.org/api/timezone/Asia/Karachi', timeout=10)

            data = response.json()
            current_time = datetime.datetime.fromisoformat(data['datetime'])
            formatted_time = current_time.strftime("%y/%m/%d,%H:%M:%S")
            if formatted_time == system_time():
                USE_MODULE_TIME = True
                print("\n\t\tSystem time is same as fetched time using it.")
            else:
                print("\n\tSystem time is not same with the fetch one,")
                print(f"Online time: {formatted_time}, System time: {system_time()}")
        else:
            formatted_time = system_time()
        return str(formatted_time)
    except requests.exceptions.RequestException as e:
        exception_logger("fetch_current_time_online", e)
        return None


def say_to_serial(serial_data):
    """This will convert the incoming string to the proper message so
    ttgo can understand that orange pi is communicating with it"""
    try:
        # Convert serial_data to string using str() function
        serial_data_str = str(serial_data)
        # Concatenate the strings
        message = str("{hay ttgo-tcall!" + serial_data_str + "}")
        print(f"sending : {message}")
        send_to_serial_port(message)
    except Exception as e: # pylint: disable=broad-except
        exception_logger("say_to_serial, data is received: [" + str(serial_data) + "]", e)


def update_time():
    """Will send updated time to TTGO-TCall"""
    current_time = ""
    try:
        current_time = fetch_current_time_online()
        if current_time:
            # Ensure current_time is a string
            if not isinstance(current_time, str):
                raise TypeError("Expected current_time to be str," +
                                f"but got {type(current_time).__name__}")
            print(f"Current time in Karachi: {current_time}")

            # Ensure concatenation results in a valid string
            message = f"py_time:{current_time}+20"
            if not isinstance(message, str):
                raise TypeError(f"Expected message to be str, but got {type(message).__name__}")

            send_to_serial_port(message)
        else:
            print("Failed to fetch current time.")
    except TypeError as e:
        exception_logger(f"TypeError in update_time, time function got: {current_time}", e)
    except Exception as e: # pylint: disable=broad-except
        exception_logger(f"update_time, time function got: {current_time}", e)


def stop_ngrok():
    """Need to kill NGROK if it is already running"""
    try:
        print("killing ngrok server (if running)...")
        subprocess.run(['pkill', '-f', 'ngrok'], check=False)
    except Exception as e:  # pylint: disable=broad-except
        exception_logger("stop_ngrok", e)


def send_custom_message(message, number):
    """Used to send message to custom number"""
    try:
        print("Sending custom message request from orange-pi!")
        send_to_serial_port("smsTo [" + message + "]{" + number + "}")
        # TODO: make sure that message is sent # pylint: disable=fixme
    except Exception as e:  # pylint: disable=broad-except
        exception_logger("send_message", e)


def send_message(message):
    """Used to send sms to defined number"""
    try:
        print("Sending message request from orange-pi")
        send_to_serial_port("sms " + message)
    except Exception as e:  # pylint: disable=broad-except
        exception_logger("send_message", e)


def write_in_file(file_name, content):
    # return False
    """Will write data in file"""
    file_name = os.path.join(os.environ['LOG_FILE_PATH'], file_name + EXTENSION_TYPE)
    content = "\n\n------------------------------>\n" + content + "\n" + \
              "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t{time:" + \
              fetch_current_time_online() + "}\n<--------------------------------\n"
    try:
        with open(file_name, 'a', encoding='utf-8') as file:
            file.write(content)
            file.flush()  # Ensure the data is written to the file immediately
        return True
    except Exception as ex:  # pylint: disable=broad-except
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
        send_error(f"Error in {function_name}."
                   f"\tError message: {error} at: {fetch_current_time_online()}")
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


def system_time():
    """Return system time in the format: %y/%m/%d,%H:%M:%S"""
    return time.strftime("%y/%m/%d,%H:%M:%S")


def inform_supervisor():
    """Will send message to required number"""
    message = f"Informing supervisor at: {fetch_current_time_online()}"
    number = os.getenv("_SUPERVISOR_NUMBER_")
    state = request.args.get('state', '')
    message = os.getenv("_KID_NAME_")
    message += " leave " if state == "leave" else " enter "
    message += f"flat at: {fetch_current_time_online()}"

    print(f"\n\n\tSending message: {message} to {number}")
    send_api_info(f"Sending custom message: {message} to {number}")

    send_custom_message(message, number)
    return jsonify({'result': 'message send successfully'})

# Function to send random data to ESP32 every 5 seconds
def send_to_serial_port(serial_data):
    """This function Will send string as it is to TTGO-TCall"""
    data_to_send = {"data": serial_data}

    try:
        # Send the data to ESP32 using a POST request
        response = requests.post(ESP32_URL, json=data_to_send, timeout=10)
        if response.status_code == 200:
            print(f"Sent data to ESP32: {data_to_send}")
        else:
            print(f"Failed to send data to ESP32. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to ESP32: {e}")


# if __name__ == '__main__':
#     while True:
#         print ("\n\n\t ------------------ run ------------------ \n\n")
#         update_namaz_time()
#         time.sleep(5)
