import subprocess
import requests
import time


def start_ngrok():
    return subprocess.Popen(["ngrok", "http", "192.168.0.122:80"])


def get_ngrok_url():
    ngrok_status = requests.get("http://localhost:4040/api/tunnels")
    ngrok_data = ngrok_status.json()
    return ngrok_data['tunnels'][0]['public_url']


def main():
    ngrok_process = start_ngrok()
    prev_ngrok_url = None

    while True:
        try:
            time.sleep(10)  # Check every 10 seconds

            # Check if Ngrok process is still running
            if ngrok_process.poll() is not None:
                print("Ngrok process stopped. Restarting...")
                ngrok_process = start_ngrok()

            # Get Ngrok URL
            ngrok_url = get_ngrok_url()

            # Print only if the URL changes or at the start
            if ngrok_url != prev_ngrok_url or prev_ngrok_url is None:
                print("Ngrok URL:", ngrok_url)
                prev_ngrok_url = ngrok_url

        except KeyboardInterrupt:
            print("Script terminated.")
            ngrok_process.terminate()
            break
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
