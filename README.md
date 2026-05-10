# iPerson — 通用全自动个人IP运营平台

> **AI辅助 · 人主导** — 用AI放大创作者的人格，而非替代它

## 架构

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│Discovery │→│ Ranking  │→│ Research │→│Generation│→│Adaptation│
│ 热点发现 │  │ 选题排序 │  │ 素材搜集 │  │ 内容生成 │  │ 平台适配 │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
                                                              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│Publishing│←│ Quality  │←│ Human    │←──────────────────────┘
│ 多平台发布│  │ Gate     │  │ Review   │
└──────────┘  │ 质量把关 │  │ 人工审核 │
               └──────────┘  └──────────┘
```

## 快速开始

### 前置要求

- Python 3.12+
- Docker & Docker Compose (PostgreSQL, Redis, MinIO)
- Node.js 20+ (前端开发)

### 安装

```bash
# 1. 初始化项目
make setup

# 2. 配置环境变量
vim backend/.env    # 填入 API Keys

# 3. 启动基础设施 (PostgreSQL + Redis + MinIO)
docker compose up -d postgres redis minio

# 4. 运行数据库迁移
make migrate

# 5. 启动 API 服务
cd backend && uvicorn app.main:app --reload --port 8000

# 6. (可选) 启动前端
cd frontend && npm install && npm run dev
```

### 一键启动 (全部服务)

```bash
make dev
```

访问:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- MinIO Console: http://localhost:9001

## 项目结构

```
iperson/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # Pydantic 配置
│   │   ├── database.py         # 异步 DB session
│   │   ├── dependencies.py     # JWT 认证 + RBAC
│   │   ├── worker.py           # Celery 异步任务
│   │   ├── core/               # 横切关注点
│   │   │   ├── security.py     # JWT / bcrypt / 角色
│   │   │   ├── tenant.py       # 多租户上下文
│   │   │   └── errors.py       # 领域异常
│   │   ├── models/             # SQLAlchemy 12 表
│   │   ├── schemas/            # Pydantic 验证
│   │   ├── api/v1/             # RESTful 路由 (7 模块)
│   │   └── domain/             # 领域服务
│   │       ├── pipeline/       # 内容管线编排
│   │       ├── persona/        # 风格引擎
│   │       ├── publish/        # 发布平台插件
│   │       ├── knowledge/      # 知识库 + RAG
│   │       └── analytics/      # 分析引擎
│   └── tests/                  # 26+ 测试用例
├── frontend/                   # Next.js 14 前端
│   ├── app/                    # App Router 页面
│   └── lib/api.ts              # API 客户端
├── docker-compose.yml          # 7 服务编排
└── Makefile                    # 开发工作流
```

## API 概览

| 分组 | 端点 | 说明 |
|-----|------|------|
| Auth | `POST /api/v1/auth/register` | 注册 |
| Auth | `POST /api/v1/auth/login` | 登录 |
| Auth | `POST /api/v1/auth/refresh` | 刷新 Token |
| Personas | `GET/POST /api/v1/personas` | 人设管理 |
| Contents | `GET/POST/PATCH /api/v1/contents` | 内容管线 |
| Contents | `POST /api/v1/contents/{id}/approve` | 审核通过 |
| Contents | `POST /api/v1/contents/{id}/schedule` | 定时发布 |
| Topics | `GET /api/v1/topics` | 选题库 |
| Topics | `POST /api/v1/topics/discover` | 触发热点发现 |
| Publish | `GET/POST/DELETE /api/v1/publish/accounts` | 平台账号 |
| Knowledge | `GET/POST/DELETE /api/v1/knowledge/docs` | 知识库 |
| Analytics | `GET /api/v1/analytics/dashboard` | 数据看板 |

## 路线图

- **Phase 1** (当前): MVP 核心管线 + 基础 Web UI
- **Phase 2**: 多租户隔离 + 知识库 RAG + 订阅支付
- **Phase 3**: 多平台发布 + 分析引擎 + 反馈闭环
- **Phase 4**: 数字分身 Agent + 风格微调 + 企业版

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.12, FastAPI, SQLAlchemy 2.0, Celery |
| 前端 | Next.js 14, React 18, Tailwind CSS |
| 数据库 | PostgreSQL 16 (pgvector), Redis 7 |
| AI | LangChain, OpenAI GPT-4o, Anthropic Claude 4 |
| 基础设施 | Docker Compose, MinIO (S3)