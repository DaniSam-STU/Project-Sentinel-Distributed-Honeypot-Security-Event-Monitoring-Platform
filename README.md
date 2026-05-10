![header](https://capsule-render.vercel.app/api?type=waving&color=0:0A6FC2,100:181717&height=100&section=header)

# 🛡️ Project Sentinel — Honeypot Monitoring System

[![Typing SVG](https://readme-typing-svg.herokuapp.com?size=25&duration=3000&color=0A6FC2&center=true&vCenter=true&width=600&lines=Distributed+Honeypot+Platform;Real-time+Threat+Detection;SSH+%26+HTTP+Attack+Capture;Email+%26+Telegram+Alerts)](https://github.com/DaniSam-STU/project-sentinel)

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Go](https://img.shields.io/badge/Go-1.25+-00ADD8?style=for-the-badge&logo=go)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql)
![Grafana](https://img.shields.io/badge/Monitoring-Grafana-F46800?style=for-the-badge&logo=grafana)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

**A distributed honeypot and security-event monitoring platform that captures real-world attackers, harvests credentials, and fires real-time alerts via Email and Telegram.**

---

## 🚀 Overview

Project Sentinel is a full-stack cybersecurity monitoring system. It deploys low-interaction honeypots (SSH and HTTP) that lure attackers, captures everything they do, and streams the intelligence to a central API — which stores events in PostgreSQL/TimescaleDB and instantly notifies your team.

- 🕵️ **Decoy services** that look real to attackers
- 🌍 **GeoIP resolution** per attacker IP
- 🔒 **Automatic IP blocking** at the sensor level
- 📊 **Grafana dashboards** with provisioned alert rules
- 📧 **Email + Telegram** push notifications

> 🎓 Developed by DAani Sam — Cybersecurity Project (STU)

---

## ✨ Features

✅ SSH honeypot (Paramiko) — captures credentials & blocks repeat attackers  
✅ HTTP honeypot (Flask) — fake admin login panel that logs every attempt  
✅ Central Go/Gin REST API for event ingestion  
✅ PostgreSQL + TimescaleDB for time-series event storage  
✅ Per-IP sliding-window rate limiting and auto-blocking  
✅ Country detection via ip-api.com  
✅ HTML email alerts to all registered users (Gmail SMTP)  
✅ Telegram bot real-time push alerts  
✅ Grafana alerting — brute-force, traffic spikes, multi-service attack detection  
✅ Deployed Core API on Render  

---

## 🖼️ Project Preview

> 📌 Sensors connect to the Core API and stream events in real-time. Grafana visualises attack patterns across all honeypots.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **SSH Sensor** | Python 3, Paramiko |
| **HTTP Sensor** | Python 3, Flask |
| **Core API** | Go 1.25, Gin, pgx/v5, gomail |
| **Database** | PostgreSQL 14 + TimescaleDB |
| **Monitoring** | Grafana (provisioned via YAML) |
| **Notifications** | Gmail SMTP, Telegram Bot API |
| **GeoIP** | ip-api.com |
| **Deployment** | Render (Core API) |

---
## 📁 Project Structure

```
project-sentinel/
├── core-api/                   # Go REST API
│   ├── main.go                 # Routes, handlers, email & Telegram
│   ├── database/db.go          # DB connection + migration
│   ├── handlers/handlers.go    # IngestLog, HealthCheck, GetLogs
│   ├── go.mod / go.sum
│   └── .env                    # Secrets
├── sensors/
│   ├── ssh/main.py             # SSH honeypot (Paramiko)
│   └── http/main.py            # HTTP honeypot (Flask)
├── database-schema/schema.sql  # Canonical PostgreSQL schema
├── grafana/provisioning/
│   ├── alerting/ssh.yaml
│   ├── alerting/traffic-spike.yaml
│   ├── alerting/multiservice-attack.yaml
│   └── datasources/postgres.yaml
├── infrastructure/init-db.sql  # TimescaleDB init
├── sentinel_dump.sql           # Full DB dump
└── README.md
```

---

## ⚙️ Installation

```bash
git clone https://github.com/DaniSam-STU/project-sentinel.git
cd project-sentinel
```

### 1. Database

```bash
psql -U postgres -c "CREATE DATABASE sentinel_db;"
psql -U postgres -d sentinel_db -f infrastructure/init-db.sql
psql -U postgres -d sentinel_db -f database-schema/schema.sql
```

### 2. Core API (Go)

```bash
cd core-api
# Fill in your .env (DATABASE_URL, EMAIL, APP_PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
go mod download
go run main.go
# Starts on :8000
```

### 3. SSH Sensor

```bash
cd sensors/ssh
pip install paramiko requests
python main.py
# Listens on 0.0.0.0:2222
```

### 4. HTTP Sensor

```bash
cd sensors/http
pip install flask requests
python main.py
# Listens on 0.0.0.0:8080
```

### 5. Grafana

Point Grafana's provisioning path to `grafana/provisioning/`. The PostgreSQL datasource and all alert rules load automatically on startup.

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ingest` | Sensors send security events here |
| `GET` | `/health` | Liveness check |
| `GET` | `/api/v1/logs` | View recent attack logs (optional `?protocol=SSH`) |
| `GET` | `/api/v1/health` | Sensor registry + online/offline status |

### Event JSON Schema

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-05-10T12:00:00Z",
  "sensor_id": "ssh-eu-1",
  "sensor_location": "london",
  "source_ip": "45.33.32.156",
  "attacker_country": "United States",
  "vector": "ssh",
  "interaction_level": "low",
  "payload": {
    "username_attempted": "root",
    "password_attempted": "admin123",
    "commands_executed": [],
    "files_dropped": []
  }
}
```

> `vector` must be one of: `ssh`, `http`

---

## ⚠️ Permissions

### Linux / macOS

```bash
sudo python3 sensors/ssh/main.py
sudo python3 sensors/http/main.py
```

### Windows

- Run terminal as Administrator
- Ensure port 2222 and 8080 are not blocked by firewall

---

## 🔔 Notifications

| Channel | Trigger | Content |
|---|---|---|
| **Email (Gmail SMTP)** | Every `ssh` or `http` event | HTML report — sensor, IP, country, credentials |
| **Telegram Bot** | Every event regardless of vector | Plain-text alert with vector and source IP |

Both are dispatched in background goroutines — they never block the API response.

---

## 📊 Grafana Alerts

| Alert | Trigger Condition | Check Interval |
|---|---|---|
| SSH Brute-Force | >3 auth attempts from same IP in 5 min | 1 min |
| Traffic Spike | Current rate >3× hourly baseline | 5 min |
| Multi-Service Attack | Same IP hits >2 sensor types in 10 min | 10 min |

---

## 🐞 Troubleshooting

### Paramiko not installed
```bash
pip install paramiko
```

### Flask not installed
```bash
pip install flask requests
```

### Core API can't reach database
- Verify `DATABASE_URL` in `core-api/.env`
- Ensure PostgreSQL is running and accessible

### No email alerts
- Check `EMAIL` and `APP_PASSWORD` in `.env`
- Use a Gmail **App Password**, not your account password
- Enable "Less secure app access" or use OAuth2

### No Telegram alerts
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Start a conversation with your bot first so it can message you

### Sensor not connecting to API
- The Core API on Render may be sleeping — the sensor sends a `/health` ping first to wake it
- Check `API_URL` in the sensor's `main.py`

---

## 🤝 Contributing

- Pull requests are welcome!
- Fork the repo, create a feature branch, and open a PR.
- For major changes, open an issue first to discuss what you'd like to change.

---

## 👨‍💻 Author & Contact Information

- **DAani Sam**

[![GitHub](https://img.shields.io/badge/GitHub-@DaniSam--STU-181717?style=for-the-badge&logo=github)](https://github.com/DaniSam-STU)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Deepanshu--Semwal-0A6FC2?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/deepanshu-s-437566373)
[![Email](https://img.shields.io/badge/Email-deepanshusemwal99@gmail.com-D14836?style=for-the-badge&logo=gmail)](mailto:deepanshusemwal99@gmail.com)

---

## 📜 License

This project is licensed under the [MIT License](https://github.com/DaniSam-STU/project-sentinel/blob/main/LICENSE).  
Intended for **educational and ethical use only**. Do not deploy honeypots on networks you do not own or have explicit permission to monitor.

---

## ⭐ Support

If you find this project useful, give it a ⭐ on [GitHub](https://github.com/DaniSam-STU/project-sentinel)!

---

![footer](https://capsule-render.vercel.app/api?type=waving&color=0:0A6FC2,100:181717&height=100&section=footer)
