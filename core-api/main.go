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

	email := os.Getenv("EMAIL")
	password := os.Getenv("APP_PASSWORD")

	if email == "" || password == "" {
		log.Println("❌ EMAIL credentials not set")
		return
	}

	m := gomail.NewMessage()
	m.SetHeader("From", email)
	m.SetHeader("To", to)
	m.SetHeader("Subject", subject)
	m.SetBody("text/html", message)

	d := gomail.NewDialer("smtp.gmail.com", 587, email, password)

	if err := d.DialAndSend(m); err != nil {
		fmt.Println("❌ EMAIL ERROR:", err)
	} else {
		fmt.Println("✅ Email sent successfully")
	}
}

// ---------------- TELEGRAM ----------------

func sendTelegram(message string) {

	botToken := os.Getenv("TELEGRAM_BOT_TOKEN")
	chatID := os.Getenv("TELEGRAM_CHAT_ID")

	if botToken == "" || chatID == "" {
		fmt.Println("❌ Telegram ENV not set")
		return
	}

	url := "https://api.telegram.org/bot" + botToken + "/sendMessage"

	payload := strings.NewReader(
		"chat_id=" + chatID + "&text=" + message,
	)

	req, err := http.NewRequest("POST", url, payload)
	if err != nil {
		fmt.Println("❌ Telegram request error:", err)
		return
	}

	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")

	client := &http.Client{}
	resp, err := client.Do(req)

	if err != nil {
		fmt.Println("❌ Telegram error:", err)
		return
	}
	defer resp.Body.Close()

	fmt.Println("📱 Telegram alert sent")
}

// ---------------- DB ----------------

func getDatabaseURL() string {
	url := os.Getenv("DATABASE_URL")
	if url == "" {
		log.Fatal("DATABASE_URL not set")
	}
	return url
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

// ---------------- EMAIL TEMPLATE ----------------

func buildEmailMessage(event SecurityEvent) string {

	username := "N/A"
	password := "[REDACTED]" // 🔐 safer
	commands := "N/A"
	files := "N/A"

	if event.Payload != nil {
		if event.Payload.UsernameAttempted != nil {
			username = *event.Payload.UsernameAttempted
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
	<li><b>Username:</b> %s</li>
	<li><b>Password:</b> %s</li>
	<li><b>Commands:</b> %s</li>
	<li><b>Files:</b> %s</li>
</ul>

<hr>

<p style="color:red;"><b>⚠️ Investigate immediately</b></p>
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
		log.Fatalf("DB connect failed: %v", err)
	}
	defer pool.Close()

	if err := pool.Ping(ctx); err != nil {
		log.Fatalf("DB ping failed: %v", err)
	}

	log.Println("Connected to database")

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

	fmt.Println("🔥 Received:", event.Vector)

	// -------- DB PREP --------

	var usernameAttempted *string
	var passwordAttempted *string
	commands := []string{}
	files := []string{}

	if event.Payload != nil {
		usernameAttempted = event.Payload.UsernameAttempted
		passwordAttempted = event.Payload.PasswordAttempted
		commands = event.Payload.CommandsExecuted
		files = event.Payload.FilesDropped
	}

	cmdJSON, _ := json.Marshal(commands)
	fileJSON, _ := json.Marshal(files)

	// -------- INSERT --------

	sql := `
	INSERT INTO security_events (
		event_id, timestamp, sensor_id, sensor_location,
		source_ip, vector, interaction_level,
		username_attempted, password_attempted,
		commands_executed, files_dropped
	)
	VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11::jsonb)
	ON CONFLICT (event_id) DO NOTHING
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
		string(cmdJSON),
		string(fileJSON),
	)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// -------- ALERTS --------

	vector := strings.ToLower(event.Vector)

	if vector == "ssh" || vector == "http" {

		message := buildEmailMessage(event)

		a.sendEmailToAll("🚨 Sentinel Alert - "+vector, message)

		sendTelegram("🚨 " + vector + " attack from " + event.SourceIP)
	}

	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

// ---------------- EMAIL BROADCAST ----------------

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
			continue
		}
		sendEmail(email, subject, message)
	}
}

// ---------------- HEALTH ----------------

func (a *App) health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}