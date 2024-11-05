# For additional setup:

## NTFY setup:
```
sudo docker run -p 9999:80 -itd --restart=unless-stopped binwiederhier/ntfy serve
```
## CloudFlare setup:
```
docker run -d --restart=unless-stopped cloudflare/cloudflared:latest tunnel --no-autoupdate run --token "$CLOUDFLARE_TOKEN"
```


## AdGuard Setup:
```
curl -s -S -L https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh | sh -s -- -v
```
### To Kill previous services:

```
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved
```


## Terminal setup:
### To add branch name in the terminal add this to bashrc file:
- sudo nano ~/.bashrc
```
parse_git_branch() {
     git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/(\1)/'
}

export PS1="\u@\h \[\e[32m\]\w \[\e[91m\]\$(parse_git_branch)\[\e[00m\]$ "
```

## netData:

Add this to docker-compose file in /opt

```
  netdata:
    image: netdata/netdata:stable
    container_name: netdata
    pid: host
    network_mode: host
    restart: unless-stopped
    cap_add:
      - SYS_PTRACE
      - SYS_ADMIN
    security_opt:
      - apparmor:unconfined
    volumes:
      - netdataconfig:/etc/netdata
      - netdatalib:/var/lib/netdata
      - netdatacache:/var/cache/netdata
      - /etc/passwd:/host/etc/passwd:ro
      - /etc/group:/host/etc/group:ro
      - /etc/localtime:/etc/localtime:ro
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /etc/os-release:/host/etc/os-release:ro
      - /var/log:/host/var/log:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - NETDATA_CLAIM_TOKEN=h5lSpsyoDQtZ7TqE-N9WtEjl19uVxfNpcigT9ex9dK3u5EuPMB4AH-_Z2wdNGHuJ_dCZV8TX75EUPseupUEq0nMBwZ6t9Had84HqOYhUTpm6B-37j5O6_Y-S2xop_SGIUTvHHI8
      - NETDATA_CLAIM_URL=https://app.netdata.cloud
      - NETDATA_CLAIM_ROOMS=851ec14e-2a88-460b-9e10-4626dce9677e
volumes:
  netdataconfig:
  netdatalib:
  netdatacache:
```

# Jellyfin setup:

## This setup will use the external HDD

- To see attached external devices type this in terminal:  `lsblk`
- Spot your drive like in my case it is sdb1 under sdb
- You need to create a mount point: `sudo mkdir -p /mnt/external`
- In case you get any error like this:
```
Mount is denied because the NTFS volume is already exclusively opened.
The volume may be already mounted, or another software may use it which
could be identified for example by the help of the 'fuser' command.
```
- To solve this error please follow [these](#mounting-issue-solution) commands:

- Mount the drive manually `sudo mount /dev/sda1 /mnt/external`
- Verify it `ls /mnt/external` it should show the data of hdd
- Now get the UUID of HDD `sudo blkid /dev/sda1` it looks like this: `UUID="01DA837C8C0D34B0"`
- Edit fstab: `sudo nano /etc/fstab`
 - After adjusting add this line to the file `UUID=1234-5678-90AB-CDEF /mnt/external ntfs defaults 0 2`
 - Save file and type `sudo mount -a`
 - Please follow [these](#To-share-external-HDD) instruction to share that HDD on local network

#### Create new folders for config and cache (in my case):
- /home/orangepi/Desktop/temp/jellyfin/config
- /home/orangepi/Desktop/temp/jellyfin/cache

#### Add this to docker compose file:

```
version: "3.8"
services:
  jellyfin:
    image: jellyfin/jellyfin
    container_name: jellyfin
    network_mode: host
    restart: unless-stopped
    volumes:
      - /mnt/external:/media
      - /home/orangepi/Desktop/temp/jellyfin/config:/config
      - /home/orangepi/Desktop/temp/jellyfin/cache:/cache
    environment:
      - UID=1000
      - GID=1000
```
- For permission issue: `sudo chown -R 1000:1000 /mnt/external`
- To restart jellyfin docker: `sudo docker-compose restart jellyfin`

# How to setup grafana:

- To setup with docker compose:

```
version: '3.0'
services:
  grafana:
    image: grafana/grafana-enterprise
    container_name: grafana
    restart: unless-stopped
    ports:
      - '3000:3000'
    volumes:
      - grafana-storage:/var/lib/grafana
volumes:
  grafana-storage: {}
```
- To setup with terminal:
```
sudo apt update
sudo apt upgrade -y
sudo apt install -y apt-transport-https gnupg2 curl
curl https://packages.grafana.com/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/grafana-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/grafana-archive-keyring.gpg] https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install -y grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

# How to setup Influxdb:

```
services:
  influxdb:
    image: influxdb:latest
    container_name: influxdb
    ports:
      - "8086:8086"
    volumes:
      - influxdb-data:/var/lib/influxdb
    restart: always

volumes:
  influxdb-data:
```


# Odoo setup

##  Postgres docker:

```
docker run -d \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_PASSWORD=odoo \
  -e POSTGRES_DB=postgres \
  --name db \
  --restart unless-stopped \
  postgres:15
```

##  Odoo docker:

```
docker run -d \
  -p 8069:8069 \
  --name odoo \
  --link db:db \
  -t \
  --restart unless-stopped \
  odoo
```



### Enable arduino nano with these commands:

```
sudo apt remove brltty

sudo mv /usr/lib/udev/rules.d/90-brltty-device.rules /usr/lib/udev/rules.d/90-brltty-device.rules.disabled
sudo mv /usr/lib/udev/rules.d/90-brltty-uinput.rules /usr/lib/udev/rules.d/90-brltty-uinput.rules.disabled
sudo udevadm control --reload-rules
```

# To share external HDD

### Setup Samba to Share `/mnt/external` Directory

Consider looking into [this](#To-share-smb-server-of-router) information as it uses the smb server (HDD mount in router).

Follow these steps to configure Samba for sharing the `/mnt/external` directory on your Linux machine so it can be accessed from other devices on the same network:

### 1. Install Samba

```sh
sudo apt update
sudo apt install samba
```

### 2. Configure Samba

Edit the Samba configuration file:

```sh
sudo nano /etc/samba/smb.conf
```

Add the following lines at the end of the file:

```ini
[External]
path = /mnt/external
browsable = yes
writable = yes
guest ok = yes
create mask = 0777
directory mask = 0777
```

### 3. Set Directory Permissions

Ensure the directory has the appropriate permissions:

```sh
sudo chmod -R 0777 /mnt/external
sudo chown -R nobody:nogroup /mnt/external
```

### 4. Restart Samba

Restart the Samba service to apply the changes:

```sh
sudo systemctl restart smbd
```

### 5. Check Samba Status

Ensure Samba is running without errors:

```sh
sudo systemctl status smbd
```

### 6. Access the Share

From a Windows machine, you can access the share by typing `\\linux_ip\External` in the File Explorer's address bar.

Replace `linux_ip` with the IP address of your Linux machine.

## Mounting Issue Solution
Here are the commands you need to run:
1. `sudo fuser -v /dev/sda1`
2. `sudo fuser -k /dev/sda1`
3. `sudo umount /dev/sda1`
4. `sudo mount /dev/sda1 /mnt/external`


# To setup dashy
- All the installation guid is present on [this](https://dashy.to/) page.
- Navigate to required directory `cd /Desktop/projects/`
- Create folder `mkdir dashy_config`
- Create config file in created folder `cd dashy_config && sudo nano config.yaml`
- In dashy past [this](#dashy-config-data) content for now or try using backup.
- Create folder in dashy `mkdir icons && cd icons`
- In dashy folder clone [this](https://github.com/walkxcode/dashboard-icons.git) repo: `git clone https://github.com/walkxcode/dashboard-icons.git`
- Navigate to docker compose file `cd /opt`
- Edit docker compose file add this service:

```
services:
  dashy:
    image: lissy93/dashy
    container_name: Dashy
    ports:
      - 8080:8080
    volumes:
      - /home/orangepi/Desktop/projects/dashy_config/config.yml:/app/public/config.yml
      - /home/orangepi/Desktop/projects/dashy_config/icons/dashboard-icons/png:/app/public/item-icons/icons
    restart: unless-stopped
```

# Dashy config data:
```
pageInfo:
  title: Home Lab
sections: # An array of sections
- name: Example Section
  icon: far fa-rocket
  items:
  - title: GitHub
    description: Dashy source code and docs
    icon: fab fa-github
    url: https://github.com/Lissy93/dashy
  - title: Issues
    description: View open issues, or raise a new one
    icon: fas fa-bug
    url: https://github.com/Lissy93/dashy/issues
- name: Local Services
  items:
  - title: Firewall
    icon: favicon
    url: http://192.168.1.1/
  - title: Game Server
    icon: https://i.ibb.co/710B3Yc/space-invader-x256.png
    url: http://192.168.130.1/
```
# Steps to configure no-ip

```
wget --content-disposition https://www.noip.com/download/linux/latest
sudo tar xf noip-duc_3.1.1.tar.gz
cd /home/$USER/noip-duc_3.1.1/binaries && sudo apt install ./noip-duc_3.1.1_arm64.deb
```
### To run process:
- `noip-duc -g all.ddnskey.com --username $no_ip_username --password $no_ip_password`

## To share smb server of router:
### Install Required Packages

```
sudo apt-get update
sudo apt-get install cifs-utils
```

### Create a Mount Point

`sudo mkdir -p /mnt/smbshare`


### Mount the SMB Share Manually (don't forgot to change the username and password)

`sudo mount -t cifs -o username=$SMB_USERNAME,password=$SMB_PASSWORD,vers=1.0 //192.168.1.1/g /mnt/smbshare`


### Auto mount the SMB Share on Boot

`sudo nano /etc/fstab`

### Adds this to end of the file:

`//192.168.1.1/g /mnt/smbshare cifs username=$SMB_USERNAME,password=$SMB_PASSWORD,vers=1.0,iocharset=utf8 0 0`

---

### Setting Up Postfix to Send Emails via Gmail

Follow these steps to configure your Ubuntu system to send emails using Gmail.

#### 1. Install Postfix and Mailutils
```bash
sudo apt-get update
sudo apt-get install postfix mailutils
```
- During installation, select "Internet Site" and use your system's hostname.

#### 2. Configure Postfix
Edit `/etc/postfix/main.cf`:
```bash
sudo nano /etc/postfix/main.cf
```
Add or update the following lines:
```plaintext
relayhost = [smtp.gmail.com]:587
smtp_use_tls = yes
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
```

#### 3. Set Mail Name
Set your system's domain name: (if you havn't set during postfix installation)
```bash
echo "yourdomain.com" | sudo tee /etc/mailname
```
(Replace `yourdomain.com` with your actual domain or hostname.)

#### 4. Create Authentication File
Create `/etc/postfix/sasl_passwd`:
```bash
sudo nano /etc/postfix/sasl_passwd
```
Add:
```plaintext
[smtp.gmail.com]:587 your_email@gmail.com:your_app_password
```
(Replace `your_email@gmail.com` and `your_app_password`.)

#### 5. Secure and Apply Authentication
```bash
sudo chmod 600 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
```

#### 6. Restart Postfix
```bash
sudo systemctl restart postfix
```

#### 7. Send a Test Email
```bash
echo "Test email from Ubuntu" | mail -s "Test Email" recipient@example.com
```
(Replace `recipient@example.com` with the recipient's email address.)

---
