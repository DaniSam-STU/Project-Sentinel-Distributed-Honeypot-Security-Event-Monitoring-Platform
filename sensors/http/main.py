from flask import Flask, request, render_template_string
import requests
import uuid
from datetime import datetime, timezone
import logging
import time

# -------- CONFIG --------
API_URL = "https://sentinel-api-6ojq.onrender.com/api/v1/ingest"
HEALTH_URL = "https://sentinel-api-6ojq.onrender.com/health"

SENSOR_ID = "http-eu-1"
SENSOR_LOCATION = "london"
PORT = 8080  

# -------- LOGGING --------
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# -------- COUNTRY DETECTION --------
def get_attacker_country(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        return response.json().get("country", "Unknown")
    except:
        return "Unknown"

# -------- HTML --------
LOGIN_HTML = """<!DOCTYPE html>
<html>
<head><title>Sentinel Admin</title></head>
<body style="font-family:sans-serif;text-align:center;margin-top:100px;">
<h2>🔐 Sentinel Secure Admin</h2>
<form method="POST">
<input type="text" name="username" placeholder="Username" required><br><br>
<input type="password" name="password" placeholder="Password" required><br><br>
<button type="submit">Login</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
</body>
</html>"""

# -------- ROUTE --------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        source_ip = request.remote_addr

        # Detect country
        attacker_country = "Localhost" if source_ip == "127.0.0.1" else get_attacker_country(source_ip)

        print("\n[!] HTTP Login Attempt")
        print(f"IP: {source_ip}")
        print(f"User: {username} | Pass: {password}")
        print(f"Country: {attacker_country}")

        # -------- BUILD EVENT --------
        payload = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": source_ip,
            "vector": "http",   # 🔥 IMPORTANT
            "interaction_level": "low",
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

        # -------- SEND TO GO BACKEND --------
        try:
            print("[*] Sending event to API...")

            # Wake up Render (optional but useful)
            requests.get(HEALTH_URL, timeout=10)

            response = requests.post(API_URL, json=payload, timeout=10)

            print(f"[DEBUG] Response: {response.status_code} | {response.text}")

            if response.status_code == 200:
                print(f"[+] Event sent successfully")
            else:
                print(f"[-] API Error: {response.status_code}")

        except Exception as e:
            print(f"[-] Failed to connect: {e}")

        return render_template_string(LOGIN_HTML, error="Invalid credentials")

    return render_template_string(LOGIN_HTML)

# -------- MAIN --------
if __name__ == "__main__":
    print(f"[🌐] HTTP Honeypot running on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT)