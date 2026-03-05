import socket
import threading
import paramiko
import requests
import uuid
from datetime import datetime, timezone

# --- Configuration ---
API_URL = "https://sentinel-api-6ojq.onrender.com/api/v1/ingest"
SENSOR_ID = "ssh-eu-1"
SENSOR_LOCATION = "london"
PORT = 2222

# Generate a temporary RSA key for the fake SSH server to use
HOST_KEY = paramiko.RSAKey.generate(2048)

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
        print(f"\n[!] ALERT: Login attempt from {self.client_ip}")
        print(f"    User: {username} | Pass: {password}")

        # 1. Build the payload adhering to the Master JSON Contract
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "event_id": event_id,
            "timestamp": timestamp,
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": self.client_ip,
            "vector": "ssh",
            "interaction_level": "low",
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

        # 2. Fire the data to the Core API
        try:
            response = requests.post(API_URL, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[+] Successfully ingested event: {event_id}")
            else:
                print(f"[-] API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[-] Failed to connect to Core API: {e}")

        # 3. Always deny the attacker access (it's a trap, not a real shell!)
        return paramiko.AUTH_FAILED

def handle_connection(client_socket, client_addr):
    client_ip = client_addr[0]
    print(f"[*] Incoming connection from {client_ip}")

    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        server = SentinelSSHServer(client_ip)

        transport.start_server(server=server)

        # Wait for authentication attempt
        while transport.is_active():
            if transport.is_authenticated():
                break
            threading.Event().wait(0.5)

    except Exception as e:
        print(f"[-] Connection error: {e}")
    finally:
        transport.close()

def start_honeypot():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to all interfaces on port 2222
    server_socket.bind(('0.0.0.0', PORT))
    server_socket.listen(100)

    print(f"[🛡️] Sentinel SSH Honeypot listening on port {PORT}...")

    try:
        while True:
            client_socket, client_addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_connection, args=(client_socket, client_addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down honeypot.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # Ensure paramiko logs don't clutter our clean terminal output
    import logging
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)
    
    start_honeypot()
