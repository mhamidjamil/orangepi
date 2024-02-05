"""Return bool value base on system uptime"""
def is_uptime_greater_than_threshold(threshold_minutes):
    """It will return if hte system is running from more then 10 minutes or not"""
    try:
        with open('/proc/uptime', 'r', encoding='utf-8') as f:
            uptime_seconds = float(f.readline().split()[0])
            total_uptime = int(uptime_seconds/60)
            print (f"\n\tUptime: {total_uptime}")
            return total_uptime > threshold_minutes
    except FileNotFoundError as file_not_found_error:
        print(f"Error: {file_not_found_error}")
        return None
    except Exception as e: # pylint: disable=broad-except
        print(f"Error: {e}")
        return None

# if __name__ == '__main__':
#     # Example: Check if uptime is greater than 10 minutes
#     threshold_hours = 30  # Change this to the desired threshold in hours
#     result = is_uptime_greater_than_threshold(threshold_hours)

#     if result:
#         print("Uptime is greater than the threshold.")
#     else:
#         print("Uptime is not greater than the threshold.")
