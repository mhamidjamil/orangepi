import re
import requests

# Pi-hole URL
url = "http://192.168.1.238/admin/index.php"
# The user and password for Pi-hole authentication
auth = ('admin', 'qwaszx')

# Send an authenticated GET request to the Pi-hole admin page
response = requests.get(url, auth=auth)

# Check if the request was successful
if response.status_code == 200:
    # Use regex to find the temperature value
    temperature_match = re.search(r'<span id="tempdisplay">([\d.]+)', response.text)
    if temperature_match:
        temperature = temperature_match.group(1)
        print(f"CPU Temperature: {temperature}°C")
    else:
        print("CPU temperature element not found on the page.")
else:
    print(f"Request failed with status code {response.status_code}")
