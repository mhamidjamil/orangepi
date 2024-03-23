import schedule
import time
import os


def job1():
    os.system("python3 fetch_and_send_time.py")
    print("job executed")


# Schedule the job every 10 minutes
schedule.every(2).minutes.do(job1)

while True:
    schedule.run_pending()
    time.sleep(1)
