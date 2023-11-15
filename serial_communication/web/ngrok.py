import subprocess

def start_ngrok():
    try:
        # Run Ngrok command and capture the output
        ngrok_process = subprocess.Popen(['ngrok', 'http', '192.168.1.238:6677'], stdout=subprocess.PIPE)

        # Read the output of the command
        output, error = ngrok_process.communicate()

        # Decode the byte output to a string
        ngrok_output = output.decode('utf-8')

        # Print the Ngrok URL
        print("Ngrok URL:", ngrok_output)

    except Exception as e:
        print(f"An error occurred: {e}")

# Call the function to start Ngrok
start_ngrok()
