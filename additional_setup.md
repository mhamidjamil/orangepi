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



