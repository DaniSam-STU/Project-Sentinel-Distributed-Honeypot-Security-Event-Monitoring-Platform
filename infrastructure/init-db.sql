-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Drop table if exists to start fresh
DROP TABLE IF EXISTS events;
-- Create events table with composite primary key including timestamp
CREATE TABLE events (
    event_id UUID,
    timestamp TIMESTAMPTZ NOT NULL,
    sensor_id TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    source_ip INET NOT NULL,
    source_port INTEGER,
    destination_ip INET,
    destination_port INTEGER,
    protocol TEXT,
    event_type TEXT NOT NULL,
    data JSONB,
    severity TEXT,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (event_id, timestamp)
);

-- Convert to hypertable
SELECT create_hypertable('events', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_events_sensor_id ON events (sensor_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_source_ip ON events (source_ip, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events (severity, timestamp DESC);

-- Create API user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'sentinel_api') THEN
        CREATE USER sentinel_api WITH PASSWORD 'api_password';
    END IF;
END
$$;
GRANT CONNECT ON DATABASE sentinel TO sentinel_api;
GRANT USAGE ON SCHEMA public TO sentinel_api;
GRANT SELECT, INSERT, UPDATE ON events TO sentinel_api;
