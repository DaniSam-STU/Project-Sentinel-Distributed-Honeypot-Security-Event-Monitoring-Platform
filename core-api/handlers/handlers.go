package handlers

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"core-api/database"
)

// -------- STRUCTS --------

// AttackLog is the JSON schema sensors must send
type AttackLog struct {
	SensorID     string `json:"sensor_id" binding:"required"`
	SensorIP     string `json:"sensor_ip" binding:"required"`
	Protocol     string `json:"protocol" binding:"required"` // SSH, HTTP, SMB, Telnet
	AttackerIP   string `json:"attacker_ip" binding:"required"`
	AttackerPort int    `json:"attacker_port"`
	Timestamp    string `json:"timestamp"`
	Payload      string `json:"payload"`
	Username     string `json:"username"`
	Password     string `json:"password"`
	Command      string `json:"command"`
	UserAgent    string `json:"user_agent"`
}

// -------- TASK 1: INGEST API --------

// IngestLog receives attack data from sensors and stores it
func IngestLog(c *gin.Context) {
	var log AttackLog

	if err := c.ShouldBindJSON(&log); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON: " + err.Error()})
		return
	}

	// Default timestamp to now if not provided
	if log.Timestamp == "" {
		log.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	query := `
		INSERT INTO attack_logs 
		(sensor_id, sensor_ip, protocol, attacker_ip, attacker_port, timestamp, payload, username, password, command, user_agent)
		VALUES (:sensor_id, :sensor_ip, :protocol, :attacker_ip, :attacker_port, :timestamp, :payload, :username, :password, :command, :user_agent)
	`
	_, err := database.DB.NamedExec(query, map[string]interface{}{
		"sensor_id":     log.SensorID,
		"sensor_ip":     log.SensorIP,
		"protocol":      log.Protocol,
		"attacker_ip":   log.AttackerIP,
		"attacker_port": log.AttackerPort,
		"timestamp":     log.Timestamp,
		"payload":       log.Payload,
		"username":      log.Username,
		"password":      log.Password,
		"command":       log.Command,
		"user_agent":    log.UserAgent,
	})

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "DB insert failed: " + err.Error()})
		return
	}

	// Update sensor last_seen
	database.DB.Exec(`
		INSERT INTO sensors (id, ip_address, last_seen, status)
		VALUES ($1, $2, NOW(), 'online')
		ON CONFLICT (id) DO UPDATE SET last_seen = NOW(), status = 'online'
	`, log.SensorID, log.SensorIP)

	c.JSON(http.StatusOK, gin.H{"message": "Log ingested successfully"})
}

// -------- TASK 3: HEALTH CHECK --------

type SensorStatus struct {
	ID        string `db:"id" json:"sensor_id"`
	IPAddress string `db:"ip_address" json:"ip_address"`
	Location  string `db:"location" json:"location"`
	LastSeen  string `db:"last_seen" json:"last_seen"`
	Status    string `db:"status" json:"status"`
}

// HealthCheck returns status of all registered sensors
func HealthCheck(c *gin.Context) {
	var sensors []SensorStatus

	err := database.DB.Select(&sensors, `
		SELECT id, ip_address, COALESCE(location, 'Unknown') as location,
		       TO_CHAR(last_seen, 'YYYY-MM-DD HH24:MI:SS') as last_seen, status
		FROM sensors
		ORDER BY last_seen DESC
	`)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Mark sensors offline if not seen in last 5 minutes
	database.DB.Exec(`
		UPDATE sensors SET status = 'offline'
		WHERE last_seen < NOW() - INTERVAL '5 minutes'
	`)

	c.JSON(http.StatusOK, gin.H{
		"total_sensors":  len(sensors),
		"sensors":        sensors,
		"checked_at":     time.Now().UTC().Format(time.RFC3339),
	})
}

// -------- BONUS: GET LOGS --------

// GetLogs returns recent attack logs
func GetLogs(c *gin.Context) {
	protocol := c.Query("protocol") // optional filter e.g. ?protocol=SSH

	var rows []map[string]interface{}
	var err error

	if protocol != "" {
		err = database.DB.Select(&rows, `
			SELECT * FROM attack_logs WHERE protocol = $1 ORDER BY timestamp DESC LIMIT 100
		`, protocol)
	} else {
		err = database.DB.Select(&rows, `
			SELECT * FROM attack_logs ORDER BY timestamp DESC LIMIT 100
		`)
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"logs": rows, "count": len(rows)})
}
