"""This script will be used to send notification to andriod"""
import subprocess
import sys
NTFY_URL = "192.168.1.238:9999"

def send_notification(message):
    """Function to send notification to andriod"""
    message = message.replace(' ', '_')
    command = f"curl -d {message} {NTFY_URL}/mi"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("Command output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error executing command:", e)
        print("Command output (stderr):", e.stderr)

def send_alert(message):
    """Function to send alerts to andriod"""
    message = message.replace(' ', '_')
    command = f"curl -d {message} {NTFY_URL}/alerts"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("Command output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error executing command:", e)
        print("Command output (stderr):", e.stderr)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        send_notification("no args send test message")
    else:
        send_notification(' '.join(sys.argv[1:]))
        # send_alert("test message")
