from flask import Flask, request, render_template_string
import requests
import uuid
from datetime import datetime, timezone
import logging
import time
from collections import defaultdict

# --- Function to detect attacker country ---
def get_attacker_country(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()
        return data.get("country", "Unknown")
    except:
        return "Unknown"

# Disable Flask request logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# --- Configuration ---
API_URL = "https://sentinel-api-6ojq.onrender.com/api/v1/ingest"
SENSOR_ID = "http-eu-1"
SENSOR_LOCATION = "london"
PORT = 8080

# --- Temporary IP blocking config ---
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 120   # increased window
BLOCK_SECONDS = 120   # 2 minutes

ip_attempts = defaultdict(list)
blocked_ips = {}

def is_ip_blocked(ip):
    now = time.time()

    if ip in blocked_ips:
        unblock_at = blocked_ips[ip]
        if now < unblock_at:
            return True, int(unblock_at - now)
        else:
            del blocked_ips[ip]

    return False, 0

def register_attack_attempt(ip):
    now = time.time()

    ip_attempts[ip] = [t for t in ip_attempts[ip] if now - t <= WINDOW_SECONDS]
    ip_attempts[ip].append(now)

    print(f"[DEBUG] {ip} attempts: {len(ip_attempts[ip])}")

    if len(ip_attempts[ip]) >= MAX_ATTEMPTS:
        blocked_ips[ip] = now + BLOCK_SECONDS
        ip_attempts[ip] = []
        return True

    return False

# --- Fake Login Page HTML ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Sentinel Secure Admin</title>
<style>
body {
    background: linear-gradient(120deg,#0f2027,#203a43,#2c5364);
    font-family: Arial;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
}
.box {
    background:white;
    padding:40px;
    border-radius:8px;
    width:350px;
}
.error {
    color:red;
    margin-bottom:10px;
}
input, button {
    width:100%;
    padding:10px;
    margin:10px 0;
}
button {
    background:#007BFF;
    color:white;
    border:none;
}
</style>
</head>
<body>

<div class="box">
<h2>🔐 Sentinel Secure Admin</h2>

{% if error %}
<div class="error">{{ error }}</div>
{% endif %}

<form method="POST">
<input name="username" placeholder="Administrator ID" required>
<input name="password" type="password" placeholder="Password" required>
<button>Sign In</button>
</form>

</div>

</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def admin_login():
    source_ip = request.remote_addr

    # Check if IP is blocked
    blocked, remaining = is_ip_blocked(source_ip)
    if blocked:
        print(f"[BLOCKED] HTTP request denied for {source_ip}, remaining {remaining}s")
        return render_template_string(
            LOGIN_HTML,
            error=f"Too many attempts. IP blocked for {remaining} seconds."
        ), 403

    if request.method == 'POST':

        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # Detect country
        if source_ip == "127.0.0.1":
            attacker_country = "Localhost"
        else:
            attacker_country = get_attacker_country(source_ip)

        print(f"\n[!] HTTP Login Attempt from {source_ip}")
        print(f"User: {username} | Pass: {password}")
        print(f"Country: {attacker_country}")

        # Register attempt
        just_blocked = register_attack_attempt(source_ip)

        # Create payload
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        interaction_level = "high" if just_blocked else "low"

        payload = {
            "event_id": event_id,
            "timestamp": timestamp,
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": source_ip,
            "attacker_country": attacker_country,
            "vector": "http",
            "interaction_level": interaction_level,
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

        # Send to API
        try:
            print("[*] Sending data to API...")

            response = requests.post(API_URL, json=payload, timeout=20)

            if response.status_code == 200:
                print(f"[+] Successfully ingested HTTP event: {event_id}")
            else:
                print(f"[-] API Error: {response.status_code}")

        except Exception as e:
            print(f"[-] Failed to connect to Core API: {e}")

        # If blocked now
        if just_blocked:
            print(f"[BLOCKED] HTTP IP {source_ip} blocked for 2 minutes")
            return render_template_string(
                LOGIN_HTML,
                error="Too many attempts. Your IP has been blocked for 2 minutes."
            ), 403

        return render_template_string(LOGIN_HTML, error="Invalid username or password")

    return render_template_string(LOGIN_HTML)


if __name__ == "__main__":
    print(f"[🌐] Sentinel HTTP Honeypot running on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT)