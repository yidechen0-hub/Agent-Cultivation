package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// --- Models ---

type User struct {
	ID        string `json:"id"`
	Phone     string `json:"phone,omitempty"`
	Nickname  string `json:"nickname"`
	AvatarURL string `json:"avatarUrl,omitempty"`
	Level     int    `json:"level"`
	Exp       int64  `json:"exp"`
	CreatedAt string `json:"createdAt"`
}

type RegisterReq struct {
	Phone    string `json:"phone" binding:"required"`
	Nickname string `json:"nickname" binding:"required"`
}

type LoginReq struct {
	Phone string `json:"phone" binding:"required"`
	Code  string `json:"code" binding:"required"`
}

type AuthResponse struct {
	Token string `json:"token"`
	User  User   `json:"user"`
}

// --- In-memory store ---

var users = map[string]*User{}
var phoneIndex = map[string]string{}

// --- Main ---

func main() {
	r := gin.Default()
	r.Use(cors.Default())

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy", "service": "user-svc"})
	})

	api := r.Group("/api/v1")
	{
		api.POST("/auth/register", handleRegister)
		api.POST("/auth/login", handleLogin)
		api.GET("/users/:id", handleGetUser)
		api.PUT("/users/:id", handleUpdateUser)
		api.GET("/users/me", handleGetCurrentUser)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8001"
	}
	log.Printf("user-svc starting on :%s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}

func handleRegister(c *gin.Context) {
	var req RegisterReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if _, exists := phoneIndex[req.Phone]; exists {
		c.JSON(http.StatusConflict, gin.H{"error": "phone already registered"})
		return
	}

	user := &User{
		ID:        uuid.New().String(),
		Phone:     req.Phone,
		Nickname:  req.Nickname,
		Level:     1,
		Exp:       0,
		CreatedAt: time.Now().Format(time.RFC3339),
	}

	users[user.ID] = user
	phoneIndex[req.Phone] = user.ID

	token := "token_" + user.ID
	c.JSON(http.StatusCreated, AuthResponse{Token: token, User: *user})
}

func handleLogin(c *gin.Context) {
	var req LoginReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// MVP: accept code "123456" for development
	if req.Code != "123456" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid code"})
		return
	}

	userID, exists := phoneIndex[req.Phone]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	}

	user := users[userID]
	token := "token_" + user.ID
	c.JSON(http.StatusOK, AuthResponse{Token: token, User: *user})
}

func handleGetUser(c *gin.Context) {
	id := c.Param("id")
	user, ok := users[id]
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	}
	c.JSON(http.StatusOK, user)
}

func handleUpdateUser(c *gin.Context) {
	id := c.Param("id")
	user, ok := users[id]
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	}

	var updates map[string]interface{}
	if err := c.ShouldBindJSON(&updates); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if nickname, ok := updates["nickname"].(string); ok {
		user.Nickname = nickname
	}
	if avatar, ok := updates["avatarUrl"].(string); ok {
		user.AvatarURL = avatar
	}

	c.JSON(http.StatusOK, user)
}

func handleGetCurrentUser(c *gin.Context) {
	token := c.GetHeader("Authorization")
	if token == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "no token provided"})
		return
	}

	userID := ""
	if len(token) > 6 {
		userID = token[6:]
	}

	user, ok := users[userID]
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
		return
	}

	c.JSON(http.StatusOK, user)
}
