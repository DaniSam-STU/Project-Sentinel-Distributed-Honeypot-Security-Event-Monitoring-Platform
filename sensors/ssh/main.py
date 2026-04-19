import socket
import threading
import paramiko
import requests
import uuid
from datetime import datetime, timezone
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

# --- Configuration ---
API_URL = "https://sentinel-api-6ojq.onrender.com/api/v1/ingest"
SENSOR_ID = "ssh-eu-1"
SENSOR_LOCATION = "london"
PORT = 2222

# Generate RSA key for fake SSH server
HOST_KEY = paramiko.RSAKey.generate(2048)

# --- Temporary IP blocking config ---
MAX_ATTEMPTS = 3
WINDOW_SECONDS = 300
BLOCK_SECONDS = 120  # 2 minutes

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

    print(f"[DEBUG SSH] {ip} attempts: {len(ip_attempts[ip])}")

    if len(ip_attempts[ip]) >= MAX_ATTEMPTS:
        blocked_ips[ip] = now + BLOCK_SECONDS
        ip_attempts[ip] = []
        return True

    return False


class SentinelSSHServer(paramiko.ServerInterface):

    def __init__(self, client_ip):
        self.client_ip = client_ip
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return 'password'

    def check_auth_password(self, username, password):

        # Check if already blocked
        blocked, remaining = is_ip_blocked(self.client_ip)
        if blocked:
            print(f"[BLOCKED] SSH auth denied for {self.client_ip}, remaining {remaining}s")
            return paramiko.AUTH_FAILED

        # Detect attacker country
        if self.client_ip == "127.0.0.1":
            attacker_country = "Localhost"
        else:
            attacker_country = get_attacker_country(self.client_ip)

        print(f"\n[!] ALERT: Login attempt from {self.client_ip}")
        print(f"Country: {attacker_country}")
        print(f"User: {username} | Pass: {password}")

        # Register attack attempt
        just_blocked = register_attack_attempt(self.client_ip)

        # Create event payload
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        interaction_level = "high" if just_blocked else "low"

        payload = {
            "event_id": event_id,
            "timestamp": timestamp,
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": self.client_ip,
            "attacker_country": attacker_country,
            "vector": "ssh",
            "interaction_level": interaction_level,
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=20)

            if response.status_code == 200:
                print(f"[+] Successfully ingested event: {event_id}")
            else:
                print(f"[-] API Error: {response.status_code}")

        except Exception as e:
            print(f"[-] Failed to connect to Core API: {e}")

        if just_blocked:
            print(f"[BLOCKED] SSH IP {self.client_ip} blocked for 2 minutes")

        return paramiko.AUTH_FAILED


def handle_connection(client_socket, client_addr):
    client_ip = client_addr[0]
    print(f"[*] Incoming connection from {client_ip}")

    blocked, remaining = is_ip_blocked(client_ip)
    if blocked:
        print(f"[BLOCKED] SSH connection dropped for {client_ip}, remaining {remaining}s")
        client_socket.close()
        return

    transport = None
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)

        server = SentinelSSHServer(client_ip)
        transport.start_server(server=server)

        while transport.is_active():
            if transport.is_authenticated():
                break
            threading.Event().wait(0.5)

    except Exception as e:
        print(f"[-] Connection error: {e}")

    finally:
        if transport is not None:
            transport.close()


def start_honeypot():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind(('0.0.0.0', PORT))
    server_socket.listen(100)

    print(f"[🛡️] Sentinel SSH Honeypot listening on port {PORT}...")

    try:
        while True:
            client_socket, client_addr = server_socket.accept()

            client_thread = threading.Thread(
                target=handle_connection,
                args=(client_socket, client_addr)
            )
            client_thread.daemon = True
            client_thread.start()

    except KeyboardInterrupt:
        print("\n[!] Shutting down honeypot.")

    finally:
        server_socket.close()


if __name__ == "__main__":
    import logging
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)
    start_honeypot()