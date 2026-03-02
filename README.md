# Project Sentinel - Core API

**Member A's Deliverable** | Deadline: Day 14

## JSON Schema (Post this on Day 1!)

Member B and C must send logs in this exact format:

```json
{
  "sensor_id":     "sensor-us-east-01",
  "sensor_ip":     "192.168.1.10",
  "protocol":      "SSH",
  "attacker_ip":   "45.33.32.156",
  "attacker_port": 54321,
  "timestamp":     "2024-01-15T10:30:00Z",
  "payload":       "raw bytes or string captured",
  "username":      "root",
  "password":      "admin123",
  "command":       "whoami",
  "user_agent":    null
}
```

> `protocol` must be one of: `SSH`, `HTTP`, `SMB`, `Telnet`

---

## API Endpoints

| Method | Endpoint   | Description                        |
|--------|------------|------------------------------------|
| POST   | `/ingest`  | Sensors send attack logs here      |
| GET    | `/health`  | Check which sensors are online     |
| GET    | `/logs`    | View recent logs (optional filter) |

### GET /logs (optional filter)
```
GET /logs?protocol=SSH
```

---

## Folder Structure

```
/core-api/
  main.go
  go.mod
  handlers/
    handlers.go
  database/
    db.go

/database-schema/
  schema.sql
```

---

## How to Run

```bash
# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=sentinel
export DB_PASS=sentinel_pass
export DB_NAME=sentinel_db

# Run
cd core-api
go run main.go
```

## Dependencies
- Go 1.21+
- PostgreSQL / TimescaleDB
- gin-gonic, sqlx, lib/pq
