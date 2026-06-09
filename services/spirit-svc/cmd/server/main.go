package main

import (
	"log"
	"net/http"
	"os"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// --- Models ---

type Spirit struct {
	ID           string            `json:"id"`
	UserID       string            `json:"userId"`
	Name         string            `json:"name"`
	Level        int               `json:"level"`
	Exp          int64             `json:"exp"`
	Skills       []SpiritSkill     `json:"skills"`
	PrivacyLevel string            `json:"privacyLevel"`
	OwnerProfile *OwnerProfile     `json:"ownerProfile,omitempty"`
}

type SpiritSkill struct {
	SkillID     string  `json:"skillId"`
	Name        string  `json:"name"`
	Category    string  `json:"category"`
	Description string  `json:"description"`
	Proficiency float64 `json:"proficiency"`
}

type OwnerProfile struct {
	VocabularyLevel int                `json:"vocabularyLevel"`
	CEFRLevel       string             `json:"cefrLevel"`
	WeakPoints      []string           `json:"weakPoints"`
	StrongPoints    []string           `json:"strongPoints"`
	StudyPrefs      string             `json:"studyPreferences"`
	ExprStyle       string             `json:"expressionStyle"`
	KnowledgeGraph  map[string]float64 `json:"knowledgeGraph"`
}

type Skill struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Category    string `json:"category"`
	Description string `json:"description"`
	IsOfficial  bool   `json:"isOfficial"`
}

type CreateSpiritReq struct {
	Name   string `json:"name" binding:"required"`
	UserID string `json:"userId"`
}

type InstallSkillReq struct {
	SkillID string `json:"skillId" binding:"required"`
}

type UpdateProfileReq struct {
	VocabularyLevel *int                `json:"vocabularyLevel,omitempty"`
	CEFRLevel       *string             `json:"cefrLevel,omitempty"`
	WeakPoints      []string            `json:"weakPoints,omitempty"`
	StrongPoints    []string            `json:"strongPoints,omitempty"`
	StudyPrefs      *string             `json:"studyPreferences,omitempty"`
	ExprStyle       *string             `json:"expressionStyle,omitempty"`
	KnowledgeGraph  map[string]float64  `json:"knowledgeGraph,omitempty"`
}

// --- In-memory store (replace with PostgreSQL in production) ---

var spirits = map[string]*Spirit{}

var officialSkills = []Skill{
	{ID: "skill-001", Name: "语境造句引擎", Category: "vocabulary", Description: "根据目标单词生成贴近生活的语境例句，帮助理解和记忆", IsOfficial: true},
	{ID: "skill-002", Name: "语法纠错", Category: "grammar", Description: "检查并纠正英语语法错误，解释错误原因并给出正确示范", IsOfficial: true},
	{ID: "skill-003", Name: "词根词缀分析", Category: "vocabulary", Description: "拆解单词构成，通过词根词缀帮助记忆和推测生词词义", IsOfficial: true},
	{ID: "skill-004", Name: "口语对话模拟", Category: "speaking", Description: "模拟真实英语对话场景，帮助练习口语表达", IsOfficial: true},
	{ID: "skill-005", Name: "翻译练习", Category: "translation", Description: "提供中英互译练习，锻炼双语转换能力", IsOfficial: true},
	{ID: "skill-006", Name: "阅读理解分析", Category: "reading", Description: "分析英语文章结构和逻辑，训练阅读理解能力", IsOfficial: true},
	{ID: "skill-007", Name: "作文批改", Category: "writing", Description: "批改英语作文，提供修改建议和范文参考", IsOfficial: true},
	{ID: "skill-008", Name: "艾宾浩斯复习", Category: "memory", Description: "基于遗忘曲线安排复习计划，科学记忆单词", IsOfficial: true},
	{ID: "skill-009", Name: "听力场景模拟", Category: "listening", Description: "模拟听力考试场景，练习听力理解和速记", IsOfficial: true},
	{ID: "skill-010", Name: "考试冲刺", Category: "exam", Description: "针对四六级/雅思/托福等考试做专项训练", IsOfficial: true},
}

func findSkill(id string) *Skill {
	for _, s := range officialSkills {
		if s.ID == id {
			return &s
		}
	}
	return nil
}

// --- Handlers ---

func main() {
	r := gin.Default()
	r.Use(cors.Default())

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy", "service": "spirit-svc"})
	})

	api := r.Group("/api/v1")
	{
		// Spirit CRUD
		api.POST("/spirits", handleCreateSpirit)
		api.GET("/spirits", handleListSpirits)
		api.GET("/spirits/:id", handleGetSpirit)
		api.DELETE("/spirits/:id", handleDeleteSpirit)

		// Skill management
		api.GET("/spirits/:id/skills", handleGetSpiritSkills)
		api.POST("/spirits/:id/skills", handleInstallSkill)
		api.DELETE("/spirits/:id/skills/:skillId", handleUninstallSkill)

		// Owner profile (for proxy mode)
		api.GET("/spirits/:id/profile", handleGetProfile)
		api.PUT("/spirits/:id/profile", handleUpdateProfile)

		// Skill catalog
		api.GET("/skills", handleListSkills)
		api.GET("/skills/:id", handleGetSkill)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8002"
	}
	log.Printf("spirit-svc starting on :%s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}

func handleCreateSpirit(c *gin.Context) {
	var req CreateSpiritReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	spirit := &Spirit{
		ID:           uuid.New().String(),
		UserID:       req.UserID,
		Name:         req.Name,
		Level:        1,
		Exp:          0,
		Skills:       []SpiritSkill{},
		PrivacyLevel: "standard",
		OwnerProfile: &OwnerProfile{
			VocabularyLevel: 0,
			CEFRLevel:       "A1",
			WeakPoints:      []string{},
			StrongPoints:    []string{},
			KnowledgeGraph:  map[string]float64{},
		},
	}

	spirits[spirit.ID] = spirit
	c.JSON(http.StatusCreated, spirit)
}

func handleListSpirits(c *gin.Context) {
	userID := c.Query("userId")
	result := []*Spirit{}
	for _, s := range spirits {
		if userID == "" || s.UserID == userID {
			result = append(result, s)
		}
	}
	c.JSON(http.StatusOK, gin.H{"spirits": result})
}

func handleGetSpirit(c *gin.Context) {
	id := c.Param("id")
	spirit, ok := spirits[id]
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "spirit not found"})
		return
	}
	c.JSON(http.StatusOK, spirit)
}

func handleDeleteSpirit(c *gin.Context) {
	id := c.Param("id")
	if _, ok := spirits[id]; !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "spirit not found"})
		return
	}
	delete(spirits, id)
	c.JSON(http.StatusOK, gin.H{"deleted": true})
}

func handleGetSpiritSkills(c *gin.Context) {
	id := c.Param("id")
	spirit, ok := spirits[id]
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "spirit not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"skills": spirit.Skills})
}

func handleInstallSkill(c *gin.Context) {
	id := c.Param("id")
	spirit, ok := spirits[id]
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "spirit not found"})
		return
	}

	var req InstallSkillReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	skill := findSkill(req.SkillID)
	if skill == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "skill not found"})
		return
	}

	// Check if already installed
	for _, ss := range spirit.Skills {
		if ss.SkillID == req.SkillID {
			c.JSON(http.StatusConflict, gin.H{"error": "skill already installed"})
			return
		}
	}

	spirit.Skills = append(spirit.Skills, SpiritSkill{
		SkillID:     skill.ID,
		Name:        skill.Name,
		Category:    skill.Category,
		Description: skill.Description,
		Proficiency: 0,
	})

	c.JSON(http.StatusOK, spirit)
}

func handleUninstallSkill(c *gin.Context) {
	id := c.Param("id")
	skillID := c.Param("skillId")

	spirit, ok := spirits[id]
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "spirit not found"})
		return
	}

	newSkills := []SpiritSkill{}
	found := false
	for _, ss := range spirit.Skills {
		if ss.SkillID == skillID {
			found = true
		} else {
			newSkills = append(newSkills, ss)
		}
	}
	if !found {
		c.JSON(http.StatusNotFound, gin.H{"error": "skill not installed"})
		return
	}

	spirit.Skills = newSkills
	c.JSON(http.StatusOK, spirit)
}

func handleGetProfile(c *gin.Context) {
	id := c.Param("id")
	spirit, ok := spirits[id]
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "spirit not found"})
		return
	}
	c.JSON(http.StatusOK, spirit.OwnerProfile)
}

func handleUpdateProfile(c *gin.Context) {
	id := c.Param("id")
	spirit, ok := spirits[id]
	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "spirit not found"})
		return
	}

	var req UpdateProfileReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	p := spirit.OwnerProfile
	if p == nil {
		p = &OwnerProfile{KnowledgeGraph: map[string]float64{}}
		spirit.OwnerProfile = p
	}

	if req.VocabularyLevel != nil {
		p.VocabularyLevel = *req.VocabularyLevel
	}
	if req.CEFRLevel != nil {
		p.CEFRLevel = *req.CEFRLevel
	}
	if req.WeakPoints != nil {
		p.WeakPoints = req.WeakPoints
	}
	if req.StrongPoints != nil {
		p.StrongPoints = req.StrongPoints
	}
	if req.StudyPrefs != nil {
		p.StudyPrefs = *req.StudyPrefs
	}
	if req.ExprStyle != nil {
		p.ExprStyle = *req.ExprStyle
	}
	if req.KnowledgeGraph != nil {
		for k, v := range req.KnowledgeGraph {
			p.KnowledgeGraph[k] = v
		}
	}

	c.JSON(http.StatusOK, p)
}

func handleListSkills(c *gin.Context) {
	category := c.Query("category")
	result := []Skill{}
	for _, s := range officialSkills {
		if category == "" || s.Category == category {
			result = append(result, s)
		}
	}
	c.JSON(http.StatusOK, gin.H{"skills": result})
}

func handleGetSkill(c *gin.Context) {
	id := c.Param("id")
	skill := findSkill(id)
	if skill == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "skill not found"})
		return
	}
	c.JSON(http.StatusOK, skill)
}
