import requests
from bs4 import BeautifulSoup
import datetime


def fetch_prayer_times():
    # Replace this URL with the actual URL of the prayer times for Lahore
    url = "https://hamariweb.com/islam/lahore_prayer-timing5.aspx"

    # Fetch the HTML content of the webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Fetch the current time online
    current_time = fetch_current_time_online()

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

    # Print and send the next prayer time to the serial terminal
    if next_prayer:
        message = f"{next_prayer}: {prayer_time}"
        print(message)
        return f"{next_prayer}: {prayer_time}"
        # Replace the following line with code to send the message to /dev/ttyUSB1
    else:
        fajr_element = soup.find('td', {'data-label': 'Fajr'})
        if fajr_element:
            fajr_time = fajr_element.text.strip()
            fajr_time_obj = datetime.datetime.strptime(
                fajr_time, '%I:%M %p') - datetime.timedelta(minutes=2)
            print(f"Fajr: {fajr_time_obj.strftime('%I:%M %p')} (?)")
            return fajr_time_obj.strftime('%I:%M %p')
        else:
            print("Failed to find Fajr time.")
            return None


def fetch_current_time_online():
    try:
        response = requests.get(
            'http://worldtimeapi.org/api/timezone/Asia/Karachi')
        data = response.json()
        current_time = datetime.datetime.fromisoformat(data['datetime'])
        formatted_time = current_time.strftime("%I:%M %p")
        # return "10:00 AM"
        return formatted_time
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    fetch_prayer_times()
