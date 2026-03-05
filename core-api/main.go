package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
)

// --- Config ---

func getDatabaseURL() string {
	if url := os.Getenv("DATABASE_URL"); url != "" {
		return url
	}
	log.Fatal("DATABASE_URL environment variable not set")
	return ""
}

// --- Models (Master JSON Contract) ---

type Payload struct {
	UsernameAttempted *string  `json:"username_attempted"`
	PasswordAttempted *string  `json:"password_attempted"`
	CommandsExecuted  []string `json:"commands_executed"` // Fixed: Enforcing array of strings
	FilesDropped      []string `json:"files_dropped"`     // Fixed: Enforcing array of strings
}

type SecurityEvent struct {
	EventID          uuid.UUID `json:"event_id"          binding:"required"`
	Timestamp        time.Time `json:"timestamp"         binding:"required"`
	SensorID         string    `json:"sensor_id"         binding:"required,max=50"`
	SensorLocation   *string   `json:"sensor_location"`
	SourceIP         string    `json:"source_ip"         binding:"required,max=45"`
	Vector           string    `json:"vector"            binding:"required,max=20"`
	InteractionLevel *string   `json:"interaction_level"`
	Payload          *Payload  `json:"payload"`
}

// --- App State ---

type App struct {
	db *pgxpool.Pool
}

func main() {
	ctx := context.Background()

	pool, err := pgxpool.New(ctx, getDatabaseURL())
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer pool.Close()

	if err := pool.Ping(ctx); err != nil {
		log.Fatalf("Database ping failed: %v", err)
	}
	log.Println("Connected to database.")

	app := &App{db: pool}

	// Initialize Gin Router
	r := gin.Default()
	r.POST("/api/v1/ingest", app.ingestEvent)
	r.GET("/health", app.health)

	log.Println("Starting server on :8000")
	if err := r.Run(":8000"); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

// --- Route Handlers ---

func (a *App) ingestEvent(c *gin.Context) {
	var event SecurityEvent

	// Bind and validate the JSON against our struct
	if err := c.ShouldBindJSON(&event); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Unpack payload fields safely to avoid nil pointer panics
	var (
		usernameAttempted *string
		passwordAttempted *string
		commandsExecuted  = []string{}
		filesDropped      = []string{}
	)

	if event.Payload != nil {
		usernameAttempted = event.Payload.UsernameAttempted
		passwordAttempted = event.Payload.PasswordAttempted
		if event.Payload.CommandsExecuted != nil {
			commandsExecuted = event.Payload.CommandsExecuted
		}
		if event.Payload.FilesDropped != nil {
			filesDropped = event.Payload.FilesDropped
		}
	}

	// Convert Go arrays back to JSON bytes for PostgreSQL JSONB columns
	commandsJSON, err := json.Marshal(commandsExecuted)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to encode commands_executed"})
		return
	}
	filesJSON, err := json.Marshal(filesDropped)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to encode files_dropped"})
		return
	}

	// SQL Insertion Statement
	sql := `
		INSERT INTO security_events (
			event_id, timestamp, sensor_id, sensor_location,
			source_ip, vector, interaction_level,
			username_attempted, password_attempted,
			commands_executed, files_dropped
		) VALUES (
			$1, $2, $3, $4,
			$5, $6, $7,
			$8, $9,
			$10::jsonb, $11::jsonb
		)
		ON CONFLICT (event_id) DO NOTHING
	`

	// Execute the query
	_, err = a.db.Exec(c.Request.Context(), sql,
		event.EventID,
		event.Timestamp,
		event.SensorID,
		event.SensorLocation,
		event.SourceIP,
		event.Vector,
		event.InteractionLevel,
		usernameAttempted,
		passwordAttempted,
		string(commandsJSON),
		string(filesJSON),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "database error: " + err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "event_id": event.EventID.String()})
}

// Fixed the Health endpoint (Removed the Python code)
func (a *App) health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}
