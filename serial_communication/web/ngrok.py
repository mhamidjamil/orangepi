from pyngrok import ngrok

def start_ngrok():
    try:
        # Set the Ngrok auth token (replace 'your_auth_token' with your actual Ngrok auth token)
        ngrok.set_auth_token("2WNPHddOOD72wNwXB7ENq6LWrHP_2ae6k5K68cGKP8Tepa5rt")

        # Open a Ngrok tunnel to your local development server
        public_url = ngrok.connect(6677)

        # Print the Ngrok URL
        print("Ngrok URL:", public_url)

        # Keep the program running to maintain the tunnel
        input("Press Enter to exit...")

    except Exception as e:
        print(f"An error occurred: {e}")

# Call the function to start Ngrok
start_ngrok()
