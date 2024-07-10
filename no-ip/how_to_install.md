## How I setup NO-IP:

```
wget --content-disposition https://www.noip.com/download/linux/latest
sudo tar xf noip-duc_3.1.1.tar.gz
cd /home/$USER/noip-duc_3.1.1/binaries && sudo apt install ./noip-duc_3.1.1_arm64.deb
```
- Allow service to be run without any issue:

```
sudo chmod +x /home/orangepi/Desktop/projects/orangepi/no-ip/noip-startup.sh
```

- After that need to add the service:

```
sudo nano /etc/systemd/system/noip-startup.service
```

```
[Unit]
Description=NoIP Startup Script
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/home/orangepi/Desktop/projects/orangepi/no-ip/noip-startup.sh
Type=oneshot

[Install]
WantedBy=multi-user.target
```

## Enable and start service:

```
sudo systemctl daemon-reload
sudo systemctl enable noip-startup.service
sudo systemctl start noip-startup.service
```