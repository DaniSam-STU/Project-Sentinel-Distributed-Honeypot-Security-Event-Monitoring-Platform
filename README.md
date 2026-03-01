# 🛡️ Project Sentinel
**A Distributed Multi-Vector Honeypot Network**

Welcome to Project Sentinel. This is a decentralized security research tool designed to deceive, detect, and analyze cyber-attacks in real-time. By deploying lightweight, multi-vector sensors globally, Sentinel captures high-fidelity threat intelligence and automates attacker attribution.

---

## 🏗️ System Architecture & Roles

Sentinel is built on a strict, decoupled 3-tier architecture. Each tier is owned by a specific role:

1. **The Brain (Core Systems Architect):** The central ingestion API and database (`/core-api`). Responsible for securely receiving, validating, and storing attack data.
2. **The Skin (Security & Deception Engineer):** The honeypot modules (`/sensors`). Emulated services (SSH, HTTP, etc.) that trick attackers and capture payloads.
3. **The Nerves (Distributed Ops - DevOps/SRE):** The deployment and routing logic (`/infrastructure`). Responsible for containerization, secure WireGuard tunnels, and global fleet management.

---

## 📜 The Master Data Contract (JSON Schema)

**CRITICAL:** This is the most important part of the project. 
* All **Sensors** MUST output data in this exact format.
* The **API and Database** MUST be built to ingest this exact format. 

If this contract is followed, all independent components will sync flawlessly.

```json
{
  "event_id": "uuid-v4-string",
  "timestamp": "ISO-8601-UTC",
  "sensor_id": "string (assigned by DevOps)",
  "sensor_location": "string (e.g., 'fra1', 'nyc3')",
  "source_ip": "string (IPv4/IPv6)",
  "vector": "string (e.g., 'ssh', 'http', 'smb')",
  "interaction_level": "string ('low', 'medium', 'high')",
  "payload": {
    "username_attempted": "string (optional)",
    "password_attempted": "string (optional)",
    "commands_executed": ["array of strings (optional)"],
    "files_dropped": ["array of file hashes (optional)"]
  }
}
