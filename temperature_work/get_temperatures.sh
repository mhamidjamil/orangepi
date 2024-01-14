#!/bin/bash

# Define an array to store temperature values
declare -a temperatures

# Loop through all thermal zones and fetch temperature values
for zone in /sys/class/thermal/thermal_zone*; do
    temp=$(cat "$zone/temp")
    temperatures+=("$temp")
done

# Print the array of temperature values
echo "Temperature values: ${temperatures[@]}"

