from flask import Flask, request, render_template_string
import requests
import uuid
from datetime import datetime, timezone
import logging

# Disable default Flask startup logs to keep our terminal clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# --- Configuration ---
API_URL = "http://localhost:8000/api/v1/ingest"
SENSOR_ID = "http-eu-1"
SENSOR_LOCATION = "london"
PORT = 8080

# --- Fake Login Page HTML ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Portal - Sentinel</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #fff; padding: 20px 40px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); text-align: center; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 3px; }
        input[type="submit"] { background: #007BFF; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 3px; width: 100%; }
        input[type="submit"]:hover { background: #0056b3; }
        .error { color: red; font-size: 0.9em; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>System Administration</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="submit" value="Secure Login">
        </form>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # 1. Capture Attacker Data
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        source_ip = request.remote_addr

        print(f"\n[!] ALERT: HTTP POST Login Attempt from {source_ip}")
        print(f"    User: {username} | Pass: {password}")

        # 2. Construct Master JSON Contract
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "event_id": event_id,
            "timestamp": timestamp,
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": source_ip,
            "vector": "http",  # Explicitly defined as requested
            "interaction_level": "low",
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

        # 3. Fire to Core API
        try:
            response = requests.post(API_URL, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[+] Successfully ingested HTTP event: {event_id}")
            else:
                print(f"[-] API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[-] Failed to connect to Core API: {e}")

        # 4. Always deny access with a generic error
        return render_template_string(LOGIN_HTML, error="Invalid username or password. Login Failed.")

    # Render normal login page for GET requests
    return render_template_string(LOGIN_HTML)

if __name__ == "__main__":
    print(f"[🌐] Sentinel HTTP Honeypot running on http://0.0.0.0:{PORT}...")
    app.run(host="0.0.0.0", port=PORT)