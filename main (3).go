package main

import (
	"log"
	"github.com/gin-gonic/gin"
	"core-api/handlers"
	"core-api/database"
)

func main() {
	// Initialize DB
	database.InitDB()

	r := gin.Default()

	// Routes
	r.POST("/ingest", handlers.IngestLog)       // Receive attack logs from sensors
	r.GET("/health", handlers.HealthCheck)       // Check which sensors are online
	r.GET("/logs", handlers.GetLogs)             // View stored logs

	log.Println("Core API running on :8080")
	r.Run(":8080")
}
