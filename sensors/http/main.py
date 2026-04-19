from flask import Flask, request, render_template_string
import requests
import uuid
from datetime import datetime, timezone
import logging
import time
from collections import defaultdict

<<<<<<< HEAD
# --- Function to detect attacker country ---
def get_attacker_country(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()
        return data.get("country", "Unknown")
    except:
        return "Unknown"

# Disable Flask request logs
=======
# -------- CONFIG --------
API_URL = "https://sentinel-api-6ojq.onrender.com/api/v1/ingest"
HEALTH_URL = "https://sentinel-api-6ojq.onrender.com/health"

SENSOR_ID = "http-eu-1"
SENSOR_LOCATION = "london"
PORT = 8080

# -------- LOGGING --------
>>>>>>> 6fc6380b3426a3e66699b182cd85d2de1febac6c
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

<<<<<<< HEAD
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
=======
# -------- HTML --------
>>>>>>> 6fc6380b3426a3e66699b182cd85d2de1febac6c
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<<<<<<< HEAD
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
=======
    <title>Sentinel Admin</title>
</head>
<body style="font-family:sans-serif;text-align:center;margin-top:100px;">
<h2> Sentinel Secure Admin</h2>

<form method="POST">
<input type="text" name="username" placeholder="Username" required><br><br>
<input type="password" name="password" placeholder="Password" required><br><br>
<button type="submit">Login</button>
</form>

{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}
>>>>>>> 6fc6380b3426a3e66699b182cd85d2de1febac6c

</body>
</html>
"""

<<<<<<< HEAD
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

=======
# -------- ROUTE --------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        source_ip = request.remote_addr

        attacker_country = "Localhost" if source_ip == "127.0.0.1" else get_attacker_country(source_ip)

        print("\n[!] HTTP Login Attempt")
        print(f"IP: {source_ip}")
        print(f"User: {username} | Pass: {password}")
        print(f"Country: {attacker_country}")

        # -------- BUILD EVENT --------
>>>>>>> 6fc6380b3426a3e66699b182cd85d2de1febac6c
        payload = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": source_ip,
<<<<<<< HEAD
            "attacker_country": attacker_country,
            "vector": "http",
            "interaction_level": interaction_level,
=======
            "vector": "http",
            "interaction_level": "low",
>>>>>>> 6fc6380b3426a3e66699b182cd85d2de1febac6c
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

<<<<<<< HEAD
        # Send to API
        try:
            print("[*] Sending data to API...")

            response = requests.post(API_URL, json=payload, timeout=20)
=======
        # -------- SEND TO API --------
        try:
            print("[*] Sending event to API...")

            # Wake up Render (optional)
            requests.get(HEALTH_URL, timeout=10)

            response = requests.post(API_URL, json=payload, timeout=10)

            print(f"[DEBUG] {response.status_code} → {response.text}")
>>>>>>> 6fc6380b3426a3e66699b182cd85d2de1febac6c

            if response.status_code == 200:
                print("[+] Event sent successfully")
            else:
                print(f"[-] API Error: {response.status_code}")

        except Exception as e:
            print(f"[-] Connection error: {e}")

<<<<<<< HEAD
        # If blocked now
        if just_blocked:
            print(f"[BLOCKED] HTTP IP {source_ip} blocked for 2 minutes")
            return render_template_string(
                LOGIN_HTML,
                error="Too many attempts. Your IP has been blocked for 2 minutes."
            ), 403

        return render_template_string(LOGIN_HTML, error="Invalid username or password")
=======
        return render_template_string(LOGIN_HTML, error="Invalid credentials")
>>>>>>> 6fc6380b3426a3e66699b182cd85d2de1febac6c

    return render_template_string(LOGIN_HTML)


# -------- MAIN --------
if __name__ == "__main__":
<<<<<<< HEAD
    print(f"[🌐] Sentinel HTTP Honeypot running on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT)
=======
    print(f"[🌐] HTTP Honeypot running on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT)
>>>>>>> 6fc6380b3426a3e66699b182cd85d2de1febac6c
