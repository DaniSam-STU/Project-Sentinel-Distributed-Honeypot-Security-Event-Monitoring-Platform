import socket
import threading
import paramiko
import requests
import uuid
from datetime import datetime, timezone

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

        # Detect attacker country
        if self.client_ip == "127.0.0.1":
            attacker_country = "Localhost"
        else:
            attacker_country = get_attacker_country(self.client_ip)

        print(f"\n[!] ALERT: Login attempt from {self.client_ip}")
        print(f"Country: {attacker_country}")
        print(f"User: {username} | Pass: {password}")

        # Create event payload
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "event_id": event_id,
            "timestamp": timestamp,
            "sensor_id": SENSOR_ID,
            "sensor_location": SENSOR_LOCATION,
            "source_ip": self.client_ip,
            "attacker_country": attacker_country,
            "vector": "ssh",
            "interaction_level": "low",
            "payload": {
                "username_attempted": username,
                "password_attempted": password,
                "commands_executed": [],
                "files_dropped": []
            }
        }

        # Send attack data to Core API
        try:
            response = requests.post(API_URL, json=payload, timeout=60)

            if response.status_code == 200:
                print(f"[+] Successfully ingested event: {event_id}")
            else:
                print(f"[-] API Error: {response.status_code}")

        except Exception as e:
            print(f"[-] Failed to connect to Core API: {e}")

        # Always deny access
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