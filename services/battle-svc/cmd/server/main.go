package main

import (
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "battle-svc",
		})
	})

	// Battle routes
	api := r.Group("/api/v1")
	{
		battles := api.Group("/battles")
		{
			battles.POST("", createBattle)
			battles.GET("/:id", getBattle)
			battles.GET("/:id/result", getBattleResult)
			battles.POST("/:id/cancel", cancelBattle)
		}

		rankings := api.Group("/rankings")
		{
			rankings.GET("", getLeaderboard)
			rankings.GET("/season/:season_id", getSeasonRankings)
			rankings.GET("/spirit/:spirit_id", getSpiritRanking)
		}

		seasons := api.Group("/seasons")
		{
			seasons.GET("/current", getCurrentSeason)
			seasons.GET("/:id", getSeason)
		}
	}

	log.Println("battle-svc starting on :8003")
	if err := r.Run(":8003"); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}

func createBattle(c *gin.Context) {
	// TODO: Create battle, validate spirits, publish to NATS
	c.JSON(http.StatusCreated, gin.H{"message": "battle created"})
}

func getBattle(c *gin.Context) {
	id := c.Param("id")
	// TODO: Fetch battle from database
	c.JSON(http.StatusOK, gin.H{"id": id, "message": "not implemented"})
}

func getBattleResult(c *gin.Context) {
	id := c.Param("id")
	// TODO: Fetch battle result
	c.JSON(http.StatusOK, gin.H{"battle_id": id, "result": nil})
}

func cancelBattle(c *gin.Context) {
	id := c.Param("id")
	// TODO: Cancel pending battle
	c.JSON(http.StatusOK, gin.H{"battle_id": id, "message": "cancelled"})
}

func getLeaderboard(c *gin.Context) {
	// TODO: Get global leaderboard
	c.JSON(http.StatusOK, gin.H{"rankings": []any{}})
}

func getSeasonRankings(c *gin.Context) {
	seasonID := c.Param("season_id")
	// TODO: Get season-specific rankings
	c.JSON(http.StatusOK, gin.H{"season_id": seasonID, "rankings": []any{}})
}

func getSpiritRanking(c *gin.Context) {
	spiritID := c.Param("spirit_id")
	// TODO: Get specific spirit's ranking
	c.JSON(http.StatusOK, gin.H{"spirit_id": spiritID, "rank": nil})
}

func getCurrentSeason(c *gin.Context) {
	// TODO: Get current active season
	c.JSON(http.StatusOK, gin.H{"season": nil})
}

func getSeason(c *gin.Context) {
	id := c.Param("id")
	// TODO: Get season details
	c.JSON(http.StatusOK, gin.H{"id": id, "message": "not implemented"})
}
