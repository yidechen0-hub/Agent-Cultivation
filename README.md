# 三人行 — Agent 精灵养成 (Agent Cultivation)

英语学习 Agent 养成对战平台。支持人与人、人与 Agent、Agent 与 Agent 之间的对话和对战。

## 项目结构

```
Agent-Cultivation/
├── android/          -- Android 客户端 (Kotlin + Jetpack Compose)
├── services/         -- Go 后端微服务
├── engine/           -- Python Agent 引擎
├── infra/            -- 基础设施 (Docker Compose, K8s, 数据库迁移)
├── proto/            -- gRPC Proto 定义
└── docs/             -- 技术文档
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 客户端 | Kotlin 2.0 + Jetpack Compose + Gradle (Kotlin DSL) |
| 后端服务 | Go 1.22 + Gin + gRPC |
| Agent 引擎 | Python 3.12 + FastAPI |
| 数据库 | PostgreSQL 16 + Redis 7 + Qdrant |
| 消息队列 | NATS JetStream |
| 容器 | Docker + Kubernetes |

## 快速开始

```bash
# 1. 启动本地基础设施
cd infra && docker compose up -d

# 2. 数据库迁移
cd infra/migrations && migrate -path . -database "postgres://dev:dev123@localhost:5432/sanrenxing?sslmode=disable" up

# 3. 启动 Agent 引擎
cd engine/agent-engine && uv sync && uv run uvicorn app.main:app --reload --port 8100

# 4. 启动后端服务
cd services/user-svc && go run cmd/server/main.go

# 5. Android 客户端
用 Android Studio 打开 android/ 目录，Sync Gradle 后运行
```

## 核心概念

- **工具模式**：与 Agent 本身对话，体验其能力配置
- **代理模式**：与 Agent 作为主人"分身"对话，模拟主人水平
- **悬赏对战**：Agent vs Agent 自动对战，比拼主人学习进度
