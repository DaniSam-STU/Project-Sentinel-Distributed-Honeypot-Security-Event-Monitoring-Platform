from flask import Flask, request, render_template_string
import requests
import uuid
from datetime import datetime, timezone
import logging

# Disable Flask logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# -------- CONFIG --------
API_URL = "https://sentinel-api-6ojq.onrender.com/api/v1/ingest"
SENSOR_ID = "http-eu-1"
SENSOR_LOCATION = "london"
PORT = 8080

# -------- HTML --------
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Sentinel Admin</title>
    <style>
        body {
            font-family: Arial;
            background: #f4f4f4;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .box {
            background: white;
            padding: 30px;
            border-radius: 5px;
            text-align: center;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
        }
        button {
            padding: 10px;
            width: 100%;
            background: #007BFF;
            color: white;
            border: none;
        }
        .error { color: red; }
    </style>
</head>
<body>
<div class="box">
    <h2>🔐 Sentinel Admin</h2>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
</div>
</body>
</html>
"""

# -------- ROUTE --------
@app.route('/', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        source_ip = request.remote_addr

        print(f"\n[!] HTTP Login Attempt from {source_ip}")
        print(f"User: {username} | Pass: {password}")

        # Build payload
        payload = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": source_ip,
            "vector": "http",
            "interaction_level": "low",
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

        # Send to API
        try:
            print("[*] Sending event to API...")

            response = requests.post(API_URL, json=payload, timeout=5)

            print(f"[DEBUG] {response.status_code} → {response.text}")

            if response.status_code == 200:
                print(f"[+] Event sent successfully")
            else:
                print(f"[-] API Error")

        except Exception as e:
            print(f"[-] Connection error: {e}")

        return render_template_string(LOGIN_HTML, error="Invalid credentials")

    return render_template_string(LOGIN_HTML)


# -------- MAIN --------
if __name__ == "__main__":
    print(f"[🌐] HTTP Honeypot running on http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT)