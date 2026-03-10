from flask import Flask, request, render_template_string
import requests
import uuid
from datetime import datetime, timezone
import logging
import time

# Function to detect attacker country
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

# --- Fake Login Page HTML ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Sentinel Secure Admin Portal</title>

<style>

body{
    margin:0;
    padding:0;
    background:linear-gradient(120deg,#0f2027,#203a43,#2c5364);
    font-family:Arial, Helvetica, sans-serif;
    height:100vh;
    display:flex;
    align-items:center;
    justify-content:center;
}

.login-container{
    background:white;
    width:360px;
    padding:40px;
    border-radius:8px;
    box-shadow:0 15px 40px rgba(0,0,0,0.4);
}

.logo{
    text-align:center;
    font-size:22px;
    font-weight:bold;
    margin-bottom:25px;
    color:#333;
}

input{
    width:100%;
    padding:12px;
    margin:10px 0;
    border:1px solid #ccc;
    border-radius:4px;
    font-size:14px;
}

input:focus{
    outline:none;
    border-color:#007BFF;
}

button{
    width:100%;
    padding:12px;
    background:#007BFF;
    border:none;
    color:white;
    font-size:16px;
    border-radius:4px;
    cursor:pointer;
}

button:hover{
    background:#0056b3;
}

.error{
    color:red;
    font-size:13px;
    margin-bottom:10px;
}

.footer{
    text-align:center;
    margin-top:20px;
    font-size:12px;
    color:#888;
}

</style>
</head>

<body>

<div class="login-container">

<div class="logo">
🔐 Sentinel Secure Admin
</div>

{% if error %}
<div class="error">{{ error }}</div>
{% endif %}

<form method="POST">

<input type="text" name="username" placeholder="Administrator ID" required>

<input type="password" name="password" placeholder="Password" required>

<button type="submit">Sign In</button>

</form>

<div class="footer">
Authorized personnel only
</div>

</div>

</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        # Capture attacker input
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        source_ip = request.remote_addr

        # Detect attacker country
        if source_ip == "127.0.0.1":
            attacker_country = "Localhost"
        else:
            attacker_country = get_attacker_country(source_ip)

        print(f"\n[!] HTTP Login Attempt from {source_ip}")
        print(f"User: {username} | Pass: {password}")
        print(f"Country: {attacker_country}")

        # Create event payload
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "event_id": event_id,
            "timestamp": timestamp,
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": source_ip,
            "attacker_country": attacker_country,
            "vector": "http",
            "interaction_level": "low",
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

        # Send event to Core API
        try:

            print("[*] Waking API server...")

            requests.get("https://sentinel-api-6ojq.onrender.com/health", timeout=120)

            time.sleep(5)

            response = requests.post(API_URL, json=payload, timeout=120)

            if response.status_code == 200:
                print(f"[+] Successfully ingested HTTP event: {event_id}")
            else:
                print(f"[-] API Error: {response.status_code}")

        except Exception as e:
            print(f"[-] Failed to connect to Core API: {e}")

        return render_template_string(LOGIN_HTML, error="Invalid username or password")

    return render_template_string(LOGIN_HTML)


if __name__ == "__main__":
    print(f"[🌐] Sentinel HTTP Honeypot running on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT)
