#!/bin/bash

# Function to check if a container is already running
is_container_running() {
    local container_name="$1"
    docker ps --format '{{.Names}}' | grep -q "$container_name"
}

# Name of the Docker container
container_name="cloudflared_tunnel"

# Infinite loop to continuously check and start the container if not running
while true; do
    # Check if the container is already running
    if ! is_container_running "$container_name"; then
        echo "Starting Docker container..."
        docker run -d --restart=unless-stopped --name "$container_name" cloudflare/cloudflared:latest tunnel --no-autoupdate run --token "$CLOUDFLARE_TOKEN"
    else
        echo "Container is already running. Skipping container start."
    fi

    # Sleep for 5 minutes before checking container status again
    echo "Sleeping for 5 minutes..."
    sleep 300
done
