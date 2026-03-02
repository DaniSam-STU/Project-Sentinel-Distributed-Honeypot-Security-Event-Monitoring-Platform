package database

import (
	"fmt"
	"log"
	"os"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

var DB *sqlx.DB

func InitDB() {
	dsn := fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		getEnv("DB_HOST", "localhost"),
		getEnv("DB_PORT", "5432"),
		getEnv("DB_USER", "sentinel"),
		getEnv("DB_PASS", "sentinel_pass"),
		getEnv("DB_NAME", "sentinel_db"),
	)

	var err error
	DB, err = sqlx.Connect("postgres", dsn)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	log.Println("Database connected successfully!")
	runMigrations()
}

func runMigrations() {
	schema := `
	CREATE TABLE IF NOT EXISTS attack_logs (
		id          SERIAL PRIMARY KEY,
		sensor_id   TEXT NOT NULL,
		sensor_ip   TEXT NOT NULL,
		protocol    TEXT NOT NULL,          -- SSH, HTTP, SMB, Telnet
		attacker_ip TEXT NOT NULL,
		attacker_port INT,
		timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
		payload     TEXT,
		username    TEXT,
		password    TEXT,
		command     TEXT,
		user_agent  TEXT,
		raw_data    JSONB
	);

	CREATE TABLE IF NOT EXISTS sensors (
		id          TEXT PRIMARY KEY,
		ip_address  TEXT NOT NULL,
		location    TEXT,
		last_seen   TIMESTAMPTZ,
		status      TEXT DEFAULT 'offline'
	);
	`
	DB.MustExec(schema)
	log.Println("Database migrations applied.")
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}
