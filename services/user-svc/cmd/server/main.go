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
			"service": "user-svc",
		})
	})

	// User routes
	api := r.Group("/api/v1")
	{
		users := api.Group("/users")
		{
			users.POST("", createUser)
			users.GET("/:id", getUser)
			users.PUT("/:id", updateUser)
			users.GET("/:id/spirits", getUserSpirits)
		}

		auth := api.Group("/auth")
		{
			auth.POST("/login", login)
			auth.POST("/refresh", refreshToken)
		}
	}

	log.Println("user-svc starting on :8001")
	if err := r.Run(":8001"); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}

func createUser(c *gin.Context) {
	// TODO: Implement user creation with validation
	c.JSON(http.StatusCreated, gin.H{"message": "user created"})
}

func getUser(c *gin.Context) {
	id := c.Param("id")
	// TODO: Fetch user from database
	c.JSON(http.StatusOK, gin.H{"id": id, "message": "not implemented"})
}

func updateUser(c *gin.Context) {
	id := c.Param("id")
	// TODO: Update user in database
	c.JSON(http.StatusOK, gin.H{"id": id, "message": "not implemented"})
}

func getUserSpirits(c *gin.Context) {
	id := c.Param("id")
	// TODO: Fetch user's spirits from database
	c.JSON(http.StatusOK, gin.H{"user_id": id, "spirits": []any{}})
}

func login(c *gin.Context) {
	// TODO: Implement JWT-based authentication
	c.JSON(http.StatusOK, gin.H{"token": "not_implemented"})
}

func refreshToken(c *gin.Context) {
	// TODO: Implement token refresh
	c.JSON(http.StatusOK, gin.H{"token": "not_implemented"})
}
