#!/bin/bash

# Run the noip-duc command using environment variables
noip-duc -g "$NOIP_HOSTNAME" --username "$NOIP_USERNAME" --password "$NOIP_PASSWORD"