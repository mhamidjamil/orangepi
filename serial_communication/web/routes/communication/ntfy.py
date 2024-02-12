"""This script will be used to send notification to andriod"""
import subprocess
import sys
NTFY_URL = "192.168.1.238:9999"

def send_to_android(message, endpoint):
    """Function to send data to Android using specified endpoint"""
    message = message.replace(' ', '_')
    command = f"curl -d {message} {NTFY_URL}/{endpoint}"

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("Command output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error executing command:", e)
        print("Command output (stderr):", e.stderr)

def send_notification(message):
    """to send notifications"""
    send_to_android(message, "notifications")

def send_alert(message):
    """to send alerts"""
    send_to_android(message, "alerts")

def send_log(message):
    """to send muted logs"""
    send_to_android(message, "logs")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        send_notification("no args send test message")
    else:
        ARGS = ' '.join(sys.argv[1:])
        if "alert" in ARGS:
            send_alert(ARGS)
        elif "log" in ARGS:
            send_log(ARGS)
        elif "notification" in ARGS:
            send_notification(ARGS)
        else:
            send_notification("else case: " + ARGS)
        # send_alert("test message")
