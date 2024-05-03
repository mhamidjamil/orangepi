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



