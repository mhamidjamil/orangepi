#!/bin/bash

#steps to auto start ntfy service at startup:


# -> First: you need to install the ntfy docker you can do that with these commands:
# sudo docker run -p 9999:80 -itd binwiederhier/ntfy serve

# sudo docker run -p 9999:80 -itd --restart=unless-stopped binwiederhier/ntfy serve


# -> Second: optional you need to install portainer you can do that by following instruction in this link:
# https://www.homeautomationguy.io/blog/home-assistant-tips/installing-docker-home-assistant-and-portainer-on-ubuntu-linux


# -> Third: You need to inspect the name of ntfy docker copy that name and past at the end of file like name will look like this: unruffled_chebyshev


# Start the ntfy docker at startup
# Don't forget to change the name
docker start unruffled_chebyshev


# We are not done yet
# -> Fourth: Then I grant it required privileges:
# chmod +x ntfy_docker.sh


# Fifth: To make it able to run on startup follow these setps:
# Open up a required file by running this in terminal:
# export VISUAL=nano; crontab -e
# Paste this line at the end of that file:
# @reboot /home/orangepi/Desktop/projects/orangepi/docker/ntfy_docker.sh

