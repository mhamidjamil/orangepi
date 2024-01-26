import requests
from bs4 import BeautifulSoup


def fetch_public_ip():
    url = 'https://www.iplocation.net/find-ip-address'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    ip_div = soup.find('div', {'id': 'ip-placeholder'})
    ip_address = ip_div.find(
        'span', style='font-weight: bold; color:green;').text
    return ip_address


if __name__ == "__main__":
    public_ip = fetch_public_ip()
    print(f"Public IP Address: {public_ip}")
