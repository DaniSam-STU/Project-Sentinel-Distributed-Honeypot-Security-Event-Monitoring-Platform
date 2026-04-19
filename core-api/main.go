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

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/joho/godotenv"
	"gopkg.in/gomail.v2"
)

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
	AttackerCountry  *string   `json:"attacker_country"`
	Vector           string    `json:"vector" binding:"required"`
	InteractionLevel *string   `json:"interaction_level"`
	Payload          *Payload  `json:"payload"`
}

// ---------------- APP ----------------

type App struct {
	db *pgxpool.Pool
}

// ---------------- EMAIL ----------------

func sendEmail(to, subject, message string) error {
	email := os.Getenv("EMAIL")
	password := os.Getenv("APP_PASSWORD")

	if email == "" || password == "" {
		return fmt.Errorf("EMAIL or APP_PASSWORD env vars not set")
	}

	m := gomail.NewMessage()
	m.SetHeader("From", email)
	m.SetHeader("To", to)
	m.SetHeader("Subject", subject)
	m.SetBody("text/html", message)

	d := gomail.NewDialer("smtp.gmail.com", 587, email, password)

	if err := d.DialAndSend(m); err != nil {
		return fmt.Errorf("failed to send email: %w", err)
	}

	return nil
}

func (a *App) sendEmailToAll(subject, message string) {
	rows, err := a.db.Query(context.Background(), "SELECT email FROM public.users")
	if err != nil {
		log.Println("❌ Query error:", err)
		return
	}
	defer rows.Close()

	for rows.Next() {
		var email string
		if err := rows.Scan(&email); err != nil {
			log.Println("❌ Scan error:", err)
			continue
		}

		log.Println("📧 Sending to:", email)
		if err := sendEmail(email, subject, message); err != nil {
			log.Println("❌ Email error:", err)
		} else {
			log.Println("✅ Email sent to:", email)
		}
	}
}

// ---------------- TELEGRAM ----------------

func sendTelegram(message string) {
	botToken := os.Getenv("TELEGRAM_BOT_TOKEN")
	chatID := os.Getenv("TELEGRAM_CHAT_ID")

	if botToken == "" || chatID == "" {
		log.Println("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
		return
	}

	apiURL := "https://api.telegram.org/bot" + botToken + "/sendMessage"
	body := strings.NewReader("chat_id=" + chatID + "&text=" + message)

	req, err := http.NewRequest("POST", apiURL, body)
	if err != nil {
		log.Println("❌ Telegram request build error:", err)
		return
	}
	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		log.Println("❌ Telegram error:", err)
		return
	}
	defer resp.Body.Close()

	log.Println("📱 Telegram alert sent")
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

	country := "N/A"
	if event.AttackerCountry != nil {
		country = *event.AttackerCountry
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
	<li><b>Country:</b> %s</li>
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
		country,
		event.Timestamp.Format(time.RFC1123),
		username,
		password,
		commands,
		files,
	)
}

// ---------------- DB ----------------

func getDatabaseURL() string {
	url := os.Getenv("DATABASE_URL")
	if url == "" {
		log.Fatal("DATABASE_URL environment variable not set")
	}
	return url
}

// ---------------- HANDLERS ----------------

func (a *App) health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func (a *App) ingestEvent(c *gin.Context) {
	var event SecurityEvent

	if err := c.ShouldBindJSON(&event); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	log.Println("🔥 Received event - vector:", event.Vector, "| ip:", event.SourceIP)

	// -------- PREPARE DATA --------

	var usernameAttempted, passwordAttempted *string
	commandsExecuted := []string{}
	filesDropped := []string{}

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

	commandsJSON, _ := json.Marshal(commandsExecuted)
	filesJSON, _ := json.Marshal(filesDropped)

	// -------- INSERT INTO DB --------

	query := `
		INSERT INTO security_events (
			event_id, timestamp, sensor_id, sensor_location,
			source_ip, attacker_country, vector, interaction_level,
			username_attempted, password_attempted,
			commands_executed, files_dropped
		) VALUES (
			$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12::jsonb
		) ON CONFLICT (event_id) DO NOTHING
	`

	_, err := a.db.Exec(c.Request.Context(), query,
		event.EventID,
		event.Timestamp,
		event.SensorID,
		event.SensorLocation,
		event.SourceIP,
		event.AttackerCountry,
		event.Vector,
		event.InteractionLevel,
		usernameAttempted,
		passwordAttempted,
		string(commandsJSON),
		string(filesJSON),
	)

	if err != nil {
		log.Println("❌ DB insert error:", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// -------- NOTIFICATIONS --------

	vector := strings.ToLower(event.Vector)

	if vector == "ssh" || vector == "http" {
		message := buildEmailMessage(event)
		go a.sendEmailToAll("🚨 Project Sentinel Alert - "+strings.ToUpper(vector), message)
	}

	go sendTelegram("🚨 ALERT: " + event.Vector + " attack from " + event.SourceIP)

	c.JSON(http.StatusOK, gin.H{"status": "success"})
}

// ---------------- MAIN ----------------

func main() {
	godotenv.Load()

	ctx := context.Background()

	pool, err := pgxpool.New(ctx, getDatabaseURL())
	if err != nil {
		log.Fatalf("Failed to connect to DB: %v", err)
	}
	defer pool.Close()

	if err := pool.Ping(ctx); err != nil {
		log.Fatalf("DB ping failed: %v", err)
	}
	log.Println("✅ Connected to database.")

	app := &App{db: pool}

	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	r.GET("/health", app.health)
	r.POST("/api/v1/ingest", app.ingestEvent)

	log.Println("🚀 Server running on :8000")
	if err := r.Run(":8000"); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}