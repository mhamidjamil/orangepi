# filename: whatsapp_starter.py
import time
import threading
import requests
import json
from flask import Flask, jsonify, request
from ntfy import waha_msgs

app = Flask(__name__)

# ----------------------------
# WhatsApp API Call Function
# ----------------------------
def start_whatsapp_session():
    url = "https://whatsapp.dolphinpk.com/api/sessions/start"  # WAHA API inside Docker

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": "change_me_now"  # <-- update with your real WAHA key
    }

    payload = {
        "name": "default",
        "config": {
            "webhooks": [
                {
                    "url": "https://webhook.dolphinpk.com/waha",  # <-- this Flask endpoint
                    # "url": "http://192.168.1.100:8000/waha",  # <-- this Flask endpoint
                    "events": ["message"]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return {"status": response.status_code, "response": response.text}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}

# ----------------------------
# Flask Routes
# ----------------------------
@app.route("/trigger", methods=["GET"])
def trigger():
    """Manually trigger the WhatsApp session start."""
    result = start_whatsapp_session()
    return jsonify(result)

@app.route("/waha", methods=["POST"])
def waha():
    """Receive WAHA webhook events (e.g., new messages)."""
    payload = request.json

    # Extract "body" and "from"
    msg_body = payload.get("payload", {}).get("body")
    raw_from = payload.get("payload", {}).get("from")

    # Clean up the "from" (remove @c.us if present)
    sender_number = raw_from.split("@")[0] if raw_from else None

    # Format the result
    result = {"body": msg_body, "from": sender_number}
    waha_msgs(result)

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Incoming WAHA simplified event:")
    print(json.dumps(result, indent=2))

    return {"ok": True}, 200


# ----------------------------
# Startup delayed call
# ----------------------------
def delayed_start():
    print("Waiting 2 minutes before starting WhatsApp session...")
    # time.sleep(120)  # 2 minutes
    time.sleep(2)
    print("Running initial WhatsApp session call...")
    start_whatsapp_session()

if __name__ == "__main__":
    threading.Thread(target=delayed_start, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
