package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"gopkg.in/gomail.v2"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/joho/godotenv"
)

// ---------------- EMAIL ----------------

func sendEmail(to string, subject string, message string) {
	m := gomail.NewMessage()
	m.SetHeader("From", "projectsentinel001@gmail.com")
	m.SetHeader("To", to)
	m.SetHeader("Subject", subject)
	m.SetBody("text/html", message)

	email := os.Getenv("EMAIL")
password := os.Getenv("APP_PASSWORD")

d := gomail.NewDialer(
    "smtp.gmail.com",
    587,
    email,
    password,
)

if email == "" || password == "" {
    log.Println("❌ EMAIL credentials not set")
    return
}

	if err := d.DialAndSend(m); err != nil {
		fmt.Println("❌ EMAIL ERROR:", err)
	} else {
		fmt.Println("✅ Email sent successfully")
	}
}

// ---------------- DB ----------------

func getDatabaseURL() string {
	if url := os.Getenv("DATABASE_URL"); url != "" {
		return url
	}
	log.Fatal("DATABASE_URL environment variable not set")
	return ""
}

// ---------------- MODELS ----------------

type Payload struct {
	UsernameAttempted *string  `json:"username_attempted"`
	PasswordAttempted *string  `json:"password_attempted"`
	CommandsExecuted  []string `json:"commands_executed"`
	FilesDropped      []string `json:"files_dropped"`
}

type SecurityEvent struct {
	EventID          uuid.UUID `json:"event_id" binding:"required"`
	Timestamp        time.Time `json:"timestamp" binding:"required"`
	SensorID         string    `json:"sensor_id" binding:"required"`
	SensorLocation   *string   `json:"sensor_location"`
	SourceIP         string    `json:"source_ip" binding:"required"`
	Vector           string    `json:"vector" binding:"required"`
	InteractionLevel *string   `json:"interaction_level"`
	Payload          *Payload  `json:"payload"`
}

// ---------------- APP ----------------

type App struct {
	db *pgxpool.Pool
}

func (a *App) sendEmailToAll(subject string, message string) {
	rows, err := a.db.Query(context.Background(), "SELECT email FROM public.users")
	if err != nil {
		fmt.Println("❌ Query error:", err)
		return
	}
	defer rows.Close()

	for rows.Next() {
		var email string
		if err := rows.Scan(&email); err != nil {
			fmt.Println("❌ Scan error:", err)
			continue
		}

		fmt.Println("📧 Sending to:", email)
		sendEmail(email, subject, message)
	}
}

// ---------------- EMAIL TEMPLATE ----------------

func buildEmailMessage(event SecurityEvent) string {
	username := "N/A"
	password := "N/A"
	commands := "N/A"
	files := "N/A"

	if event.Payload != nil {
		if event.Payload.UsernameAttempted != nil {
			username = *event.Payload.UsernameAttempted
		}
		if event.Payload.PasswordAttempted != nil {
			password = *event.Payload.PasswordAttempted
		}
		if len(event.Payload.CommandsExecuted) > 0 {
			commands = fmt.Sprintf("%v", event.Payload.CommandsExecuted)
		}
		if len(event.Payload.FilesDropped) > 0 {
			files = fmt.Sprintf("%v", event.Payload.FilesDropped)
		}
	}

	return fmt.Sprintf(`
<h2>🚨 Project Sentinel Alert</h2>

<p><b>Threat Detected!</b></p>

<hr>

<h3>📌 Event Details</h3>
<ul>
	<li><b>Sensor ID:</b> %s</li>
	<li><b>Vector:</b> %s</li>
	<li><b>Source IP:</b> %s</li>
	<li><b>Timestamp:</b> %s</li>
</ul>

<hr>

<h3>🧪 Payload Info</h3>
<ul>
	<li><b>Username Attempted:</b> %s</li>
	<li><b>Password Attempted:</b> %s</li>
	<li><b>Commands Executed:</b> %s</li>
	<li><b>Files Dropped:</b> %s</li>
</ul>

<hr>

<p style="color:red;"><b>⚠️ Action Recommended:</b> Investigate immediately.</p>

<p>— Project Sentinel 🚀</p>
`,
		event.SensorID,
		event.Vector,
		event.SourceIP,
		event.Timestamp.Format(time.RFC1123),
		username,
		password,
		commands,
		files,
	)
}

// ---------------- MAIN ----------------

func main() {
	godotenv.Load()
	ctx := context.Background()

	pool, err := pgxpool.New(ctx, getDatabaseURL())
	if err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer pool.Close()

	if err := pool.Ping(ctx); err != nil {
		log.Fatalf("DB ping failed: %v", err)
	}
	log.Println("Connected to database.")

	app := &App{db: pool}

	r := gin.Default()
	r.POST("/api/v1/ingest", app.ingestEvent)
	r.GET("/health", app.health)

	log.Println("Server running on :8000")
	r.Run(":8000")
}

// ---------------- HANDLER ----------------

func (a *App) ingestEvent(c *gin.Context) {
	var event SecurityEvent

	if err := c.ShouldBindJSON(&event); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	fmt.Println("🔥 Received vector:", event.Vector)

	// -------- PREPARE DATA --------

	var usernameAttempted *string
	var passwordAttempted *string
	commandsExecuted := []string{}
	filesDropped := []string{}

	if event.Payload != nil {
		usernameAttempted = event.Payload.UsernameAttempted
		passwordAttempted = event.Payload.PasswordAttempted
		commandsExecuted = event.Payload.CommandsExecuted
		filesDropped = event.Payload.FilesDropped
	}

	commandsJSON, _ := json.Marshal(commandsExecuted)
	filesJSON, _ := json.Marshal(filesDropped)

	// -------- INSERT INTO DB --------

	sql := `
	INSERT INTO security_events (
		event_id, timestamp, sensor_id, sensor_location,
		source_ip, vector, interaction_level,
		username_attempted, password_attempted,
		commands_executed, files_dropped
	) VALUES (
		$1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11::jsonb
	) ON CONFLICT (event_id) DO NOTHING
	`

	_, err := a.db.Exec(c.Request.Context(), sql,
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
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// -------- EMAIL TRIGGER --------

	vector := strings.ToLower(event.Vector)

fmt.Println("🔥 VECTOR RECEIVED:", event.Vector)
fmt.Println("🔥 NORMALIZED:", vector)

if vector == "ssh" || vector == "http" {
	fmt.Println("🔥 ENTERING EMAIL BLOCK")

	message := buildEmailMessage(event)

	a.sendEmailToAll(
		"🚨 Project Sentinel Alert - "+vector,
		message,
	)
}

	c.JSON(http.StatusOK, gin.H{"status": "success"})
}

// ---------------- HEALTH ----------------

func (a *App) health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}