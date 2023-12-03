import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def custom_function():
    password = os.getenv("MY_PASSWORD")
    url = os.getenv("LAHORE_NAMAZ_TIME")
    print(f"password : {password}")
    print(f"url : {url}")
if __name__ == '__main__':
    custom_function()
