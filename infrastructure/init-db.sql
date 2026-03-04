-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create events table with composite primary key
CREATE TABLE IF NOT EXISTS events (
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
