import os


def fetch_temperatures():
    temperatures = []

    # Loop through all thermal zones and fetch temperature values
    for zone in range(0, 10):  # Assuming thermal zones are numbered from 0 to 9
        zone_path = f"/sys/class/thermal/thermal_zone{zone}"

        # Check if the thermal zone exists
        if os.path.exists(zone_path):
            with open(os.path.join(zone_path, 'temp'), 'r') as file:
                # Convert temperature to an integer
                temp = int(file.read().strip())
                temperatures.append(temp)

    return temperatures


def display_temperature_stats(temperatures):
    if temperatures:
        # Calculate average and maximum temperature values
        average_temp = sum(temperatures) / len(temperatures)
        max_temp = max(temperatures)

        # Print individual temperature values
        print(f"Temperature values: {temperatures}")

        # Print average and maximum values
        print(f"Average Temperature: {average_temp}")
        print(f"Maximum Temperature: {max_temp}")
    else:
        print("No valid temperature values found.")


# Call the function to fetch temperatures
temperatures = fetch_temperatures()

# Call the function to display temperature statistics
display_temperature_stats(temperatures)
