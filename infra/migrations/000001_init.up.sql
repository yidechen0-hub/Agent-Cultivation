-- 000001_init.up.sql
-- Initial schema for Agent Cultivation (sanrenxing)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- Users
-- ============================================================
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username    VARCHAR(50) UNIQUE NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url  TEXT,
    level       INTEGER NOT NULL DEFAULT 1,
    experience  BIGINT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- ============================================================
-- Spirits
-- ============================================================
CREATE TABLE spirits (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    archetype   VARCHAR(50) NOT NULL,  -- sage, warrior, trickster, healer, etc.
    element     VARCHAR(30),           -- fire, water, earth, wind, void
    level       INTEGER NOT NULL DEFAULT 1,
    experience  BIGINT NOT NULL DEFAULT 0,
    elo_rating  INTEGER NOT NULL DEFAULT 1200,
    personality_seed TEXT,             -- initial personality configuration
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_spirits_owner ON spirits(owner_id);
CREATE INDEX idx_spirits_elo ON spirits(elo_rating DESC);
CREATE INDEX idx_spirits_archetype ON spirits(archetype);

-- ============================================================
-- Skills
-- ============================================================
CREATE TABLE skills (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(50) NOT NULL,  -- combat, knowledge, social, creative
    description TEXT,
    rarity      VARCHAR(20) NOT NULL DEFAULT 'common',  -- common, rare, epic, legendary
    max_level   INTEGER NOT NULL DEFAULT 10,
    base_power  INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_rarity ON skills(rarity);

-- ============================================================
-- Spirit Skills (junction table)
-- ============================================================
CREATE TABLE spirit_skills (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spirit_id   UUID NOT NULL REFERENCES spirits(id) ON DELETE CASCADE,
    skill_id    UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    level       INTEGER NOT NULL DEFAULT 1,
    proficiency INTEGER NOT NULL DEFAULT 0,  -- progress toward next level
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(spirit_id, skill_id)
);

CREATE INDEX idx_spirit_skills_spirit ON spirit_skills(spirit_id);
CREATE INDEX idx_spirit_skills_skill ON spirit_skills(skill_id);

-- ============================================================
-- Spirit Profiles (personality/agent configuration)
-- ============================================================
CREATE TABLE spirit_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spirit_id       UUID NOT NULL REFERENCES spirits(id) ON DELETE CASCADE UNIQUE,
    speaking_style  TEXT NOT NULL,
    values          TEXT[] NOT NULL DEFAULT '{}',
    quirks          TEXT[] NOT NULL DEFAULT '{}',
    knowledge_domains TEXT[] NOT NULL DEFAULT '{}',
    system_prompt_override TEXT,
    temperature     REAL NOT NULL DEFAULT 0.7,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_spirit_profiles_spirit ON spirit_profiles(spirit_id);

-- ============================================================
-- Episodic Memories (metadata, vectors stored in Qdrant)
-- ============================================================
CREATE TABLE episodic_memories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spirit_id   UUID NOT NULL REFERENCES spirits(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    importance  REAL NOT NULL DEFAULT 0.5,
    context_tags TEXT[] NOT NULL DEFAULT '{}',
    vector_id   VARCHAR(100),  -- reference to Qdrant point ID
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_episodic_memories_spirit ON episodic_memories(spirit_id);
CREATE INDEX idx_episodic_memories_importance ON episodic_memories(spirit_id, importance DESC);
CREATE INDEX idx_episodic_memories_created ON episodic_memories(created_at DESC);

-- ============================================================
-- Conversations
-- ============================================================
CREATE TABLE conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spirit_id   UUID NOT NULL REFERENCES spirits(id) ON DELETE CASCADE,
    title       VARCHAR(200),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    message_count INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_spirit ON conversations(spirit_id);
CREATE INDEX idx_conversations_active ON conversations(user_id, is_active) WHERE is_active = TRUE;

-- ============================================================
-- Messages
-- ============================================================
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,  -- user, assistant, system, tool
    content         TEXT NOT NULL,
    token_count     INTEGER,
    model_used      VARCHAR(50),
    tool_calls      JSONB,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_role ON messages(conversation_id, role);

-- ============================================================
-- Battles
-- ============================================================
CREATE TABLE battles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    challenger_id       UUID NOT NULL REFERENCES spirits(id) ON DELETE CASCADE,
    defender_id         UUID NOT NULL REFERENCES spirits(id) ON DELETE CASCADE,
    season_id           UUID,
    mode                VARCHAR(30) NOT NULL,  -- debate, knowledge, creative, strategy
    topic               TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    winner_id           UUID REFERENCES spirits(id),
    rounds_data         JSONB NOT NULL DEFAULT '[]',
    challenger_elo_before INTEGER,
    defender_elo_before   INTEGER,
    challenger_elo_after  INTEGER,
    defender_elo_after    INTEGER,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_battles_challenger ON battles(challenger_id);
CREATE INDEX idx_battles_defender ON battles(defender_id);
CREATE INDEX idx_battles_status ON battles(status);
CREATE INDEX idx_battles_season ON battles(season_id);
CREATE INDEX idx_battles_completed ON battles(completed_at DESC) WHERE status = 'completed';

-- ============================================================
-- Rankings
-- ============================================================
CREATE TABLE rankings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spirit_id   UUID NOT NULL REFERENCES spirits(id) ON DELETE CASCADE,
    season_id   UUID NOT NULL,
    elo_rating  INTEGER NOT NULL DEFAULT 1200,
    wins        INTEGER NOT NULL DEFAULT 0,
    losses      INTEGER NOT NULL DEFAULT 0,
    draws       INTEGER NOT NULL DEFAULT 0,
    streak      INTEGER NOT NULL DEFAULT 0,  -- positive = win streak, negative = loss streak
    peak_elo    INTEGER NOT NULL DEFAULT 1200,
    rank_tier   VARCHAR(30) NOT NULL DEFAULT 'bronze',  -- bronze, silver, gold, platinum, diamond, master
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(spirit_id, season_id)
);

CREATE INDEX idx_rankings_season_elo ON rankings(season_id, elo_rating DESC);
CREATE INDEX idx_rankings_spirit ON rankings(spirit_id);
CREATE INDEX idx_rankings_tier ON rankings(season_id, rank_tier);

-- ============================================================
-- Seasons
-- ============================================================
CREATE TABLE seasons (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    season_number INTEGER NOT NULL UNIQUE,
    starts_at   TIMESTAMPTZ NOT NULL,
    ends_at     TIMESTAMPTZ NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT FALSE,
    config      JSONB NOT NULL DEFAULT '{}',  -- season-specific rules/modifiers
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seasons_active ON seasons(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_seasons_dates ON seasons(starts_at, ends_at);

-- Add foreign key from battles to seasons (now that seasons table exists)
ALTER TABLE battles ADD CONSTRAINT fk_battles_season
    FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE SET NULL;

-- Add foreign key from rankings to seasons
ALTER TABLE rankings ADD CONSTRAINT fk_rankings_season
    FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE CASCADE;
