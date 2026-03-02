-- ============================================================
-- Project Sentinel - Database Schema
-- Member A: The Systems Architect
-- Store in: /database-schema/schema.sql
-- ============================================================

-- Attack Logs Table (TimescaleDB compatible)
CREATE TABLE IF NOT EXISTS attack_logs (
    id            SERIAL PRIMARY KEY,
    sensor_id     TEXT NOT NULL,
    sensor_ip     TEXT NOT NULL,
    protocol      TEXT NOT NULL CHECK (protocol IN ('SSH', 'HTTP', 'SMB', 'Telnet')),
    attacker_ip   TEXT NOT NULL,
    attacker_port INT,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload       TEXT,
    username      TEXT,
    password      TEXT,
    command       TEXT,
    user_agent    TEXT,
    raw_data      JSONB
);

-- Convert to TimescaleDB hypertable for time-series performance (if using TimescaleDB)
-- SELECT create_hypertable('attack_logs', 'timestamp');

-- Sensors Registry Table
CREATE TABLE IF NOT EXISTS sensors (
    id          TEXT PRIMARY KEY,
    ip_address  TEXT NOT NULL,
    location    TEXT,
    last_seen   TIMESTAMPTZ,
    status      TEXT DEFAULT 'offline' CHECK (status IN ('online', 'offline'))
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_attack_logs_timestamp    ON attack_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_attack_logs_attacker_ip  ON attack_logs (attacker_ip);
CREATE INDEX IF NOT EXISTS idx_attack_logs_protocol     ON attack_logs (protocol);
CREATE INDEX IF NOT EXISTS idx_attack_logs_sensor_id    ON attack_logs (sensor_id);

-- ============================================================
-- Sample JSON Schema (for README - share with Member B & C)
-- ============================================================
-- {
--   "sensor_id":     "sensor-us-east-01",
--   "sensor_ip":     "192.168.1.10",
--   "protocol":      "SSH",
--   "attacker_ip":   "45.33.32.156",
--   "attacker_port": 54321,
--   "timestamp":     "2024-01-15T10:30:00Z",
--   "payload":       "root\x00admin\x00",
--   "username":      "root",
--   "password":      "admin123",
--   "command":       "whoami",
--   "user_agent":    null
-- }
