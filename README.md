# Orange Pi 5 Plus automation hub 🍊

The always-on machine in the middle of my home setup. It talks to an [ESP32 TTGO T-Call](https://github.com/mhamidjamil/TTGO_TCall) over a serial line, exposes a small web console for that link, records telemetry to InfluxDB, pushes alerts to ntfy, sends mail, and runs everything else on a schedule.

[![Pylint](https://github.com/mhamidjamil/orangepi/actions/workflows/pylint.yml/badge.svg)](https://github.com/mhamidjamil/orangepi/actions/workflows/pylint.yml)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-web%20console-000000?logo=flask&logoColor=white)
![Orange Pi 5 Plus](https://img.shields.io/badge/Orange%20Pi-5%20Plus-FF6600)
![License](https://img.shields.io/badge/license-MIT-green)

![Serial console](Screenshot%202024-02-27%20234903.png)

---

## What runs here

| Piece | What it does |
|---|---|
| **Serial web console** | Live view of the serial traffic to and from the TTGO board, with an input box to send commands back |
| **Watcher and uptime checker** | Watches services and reports when something stops answering |
| **Script runner** | Runs shell commands and scripts on the Pi, triggered from the web console |
| **InfluxDB writer** | Stores sensor and telemetry readings for later charting |
| **ntfy bridge** | Turns events on the Pi into push notifications on my phone |
| **Mailer** | Sends outbound mail for alerts that deserve more than a push |
| **Prayer time fetcher** | Fetches upcoming Namaz times and the current local time for Lahore, Punjab, Pakistan, and feeds them to the TTGO display |
| **Two factor helper** | Pairs with the TTGO T-Call project so an SMS to the GSM board can act as a second factor |
| **Tunnels and dynamic DNS** | ngrok, Cloudflare and No-IP setup so the Pi is reachable from outside the house |
| **Home Assistant configuration** | The automation and configuration YAML the Pi runs |

## Talking to the TTGO board

Messages over the serial line are addressed, so both sides can ignore traffic that is not theirs:

```
Orange Pi  ->  TTGO T-Call    {hay ttgo-tcall! here goes the query?}
TTGO T-Call ->  Orange Pi     {hay orange-pi! here goes the query?}
```

## Serial web console

```bash
pip install Flask pyserial schedule requests beautifulsoup4 pyngrok python-dotenv influxdb_client
cd serial_communication/web
python app.py
```

Open `http://<orange-pi-ip>:6677`. On the Pi itself, `http://127.0.0.1:6677` works too.

- The page streams live serial data from the connected device.
- The input field sends data back down the same line.
- The serial port lives in `app.py`; the page markup is in `templates/index.html`.

## Repository layout

| Path | Contents |
|---|---|
| `serial_communication/` | The serial link: web console, routes for ntfy, the watcher, the uptime checker and the script inspector |
| `serial_communication/namaz/`, `serial_communication/time/` | Prayer time and clock feeds pushed to the TTGO board |
| `influx_db/` | InfluxDB manager, ntfy helper and a notebook for poking at the data |
| `api_communication/` | Outbound API calls to the other projects in the setup |
| `mailer/` | Outbound mail |
| `script_runner/` | Command execution on the Pi |
| `home_automation/` | Home Assistant automation and configuration YAML |
| `docker/` | ntfy, Cloudflare and No-IP container setup |
| `ngrok_work/`, `no-ip/` | Tunnel and dynamic DNS startup scripts |
| `additional_setup.md` | Host setup notes for a fresh Orange Pi |

Files ending in `.temp` are templates. Copy one, drop the suffix, and fill in your own values.

## Related projects

- [TTGO_TCall](https://github.com/mhamidjamil/TTGO_TCall) is the GSM board on the other end of the serial line, an SMS and call gateway.
- [ESP32-S3_work](https://github.com/mhamidjamil/ESP32-S3_work) turns an ESP32-S3 into a remotely driven USB keyboard.
- [waha](https://github.com/mhamidjamil/waha) handles the WhatsApp side of notifications.

More background lives in the [discussions](https://github.com/mhamidjamil/orangepi/discussions/15).

## Contributing

Issues and pull requests are welcome. The Pylint workflow gates on a 10.00/10 score, so run `pylint` locally before opening a pull request.

## License

[MIT](LICENSE)

> **Heads up:** new pieces land here a few times a week, so this page trails the code. The closed issues are the accurate changelog.
