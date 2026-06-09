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
			"service": "spirit-svc",
		})
	})

	// Spirit routes
	api := r.Group("/api/v1")
	{
		spirits := api.Group("/spirits")
		{
			spirits.POST("", createSpirit)
			spirits.GET("/:id", getSpirit)
			spirits.PUT("/:id", updateSpirit)
			spirits.GET("/:id/skills", getSpiritSkills)
			spirits.POST("/:id/skills", addSpiritSkill)
			spirits.GET("/:id/profile", getSpiritProfile)
			spirits.PUT("/:id/profile", updateSpiritProfile)
		}

		skills := api.Group("/skills")
		{
			skills.GET("", listSkills)
			skills.GET("/:id", getSkill)
		}
	}

	log.Println("spirit-svc starting on :8002")
	if err := r.Run(":8002"); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}

func createSpirit(c *gin.Context) {
	// TODO: Create spirit with initial attributes
	c.JSON(http.StatusCreated, gin.H{"message": "spirit created"})
}

func getSpirit(c *gin.Context) {
	id := c.Param("id")
	// TODO: Fetch spirit from database
	c.JSON(http.StatusOK, gin.H{"id": id, "message": "not implemented"})
}

func updateSpirit(c *gin.Context) {
	id := c.Param("id")
	// TODO: Update spirit attributes
	c.JSON(http.StatusOK, gin.H{"id": id, "message": "not implemented"})
}

func getSpiritSkills(c *gin.Context) {
	id := c.Param("id")
	// TODO: Fetch spirit's learned skills
	c.JSON(http.StatusOK, gin.H{"spirit_id": id, "skills": []any{}})
}

func addSpiritSkill(c *gin.Context) {
	id := c.Param("id")
	// TODO: Add skill to spirit's repertoire
	c.JSON(http.StatusCreated, gin.H{"spirit_id": id, "message": "skill added"})
}

func getSpiritProfile(c *gin.Context) {
	id := c.Param("id")
	// TODO: Get spirit personality profile
	c.JSON(http.StatusOK, gin.H{"spirit_id": id, "profile": nil})
}

func updateSpiritProfile(c *gin.Context) {
	id := c.Param("id")
	// TODO: Update spirit personality profile
	c.JSON(http.StatusOK, gin.H{"spirit_id": id, "message": "profile updated"})
}

func listSkills(c *gin.Context) {
	// TODO: List all available skills
	c.JSON(http.StatusOK, gin.H{"skills": []any{}})
}

func getSkill(c *gin.Context) {
	id := c.Param("id")
	// TODO: Get skill details
	c.JSON(http.StatusOK, gin.H{"id": id, "message": "not implemented"})
}
