# iPerson — 通用全自动个人IP运营平台 系统架构设计

> **版本**: v1.0 | **日期**: 2026-05-11 | **状态**: 设计阶段
>
> 基于 IPulse (单用户CLI工具) 架构升级为多租户SaaS平台

---

## 目录

1. [项目背景与产品定位](#1-项目背景与产品定位)
2. [系统架构总览](#2-系统架构总览)
3. [技术选型](#3-技术选型)
4. [核心领域模块](#4-核心领域模块)
5. [AI/ML 架构](#5-aiml-架构)
6. [数据模型设计](#6-数据模型设计)
7. [API 设计](#7-api-设计)
8. [多租户设计](#8-多租户设计)
9. [集成与部署](#9-集成与部署)
10. [开发路线图](#10-开发路线图)

---

## 1. 项目背景与产品定位

### 1.1 核心理念

iPerson 是一个"AI辅助+人主导"的个人IP内容生产平台。核心理念是：**用AI放大创作者的人格，而非替代它**。

### 1.2 四大产品线

| 产品线 | 目标用户 | 核心价值 | 定价模型 |
|--------|---------|---------|---------|
| **内容IP孵化器** | 想通过自媒体变现但缺乏内容生产力的个人 | 3个月建立有辨识度的个人IP，AI加速80%标准化工作 | 月费 500-2000元 |
| **AI内容工坊** | 有行业经验但不懂技术的个人（HR、健身教练、育儿博主） | 专属AI工作流：语气模型+视觉风格+叙事模板 | 月费 500-2000元 |
| **数字分身IP孵化器** | 有独特经历的个人（导游、退休教师、非遗传承人） | 知识资产数字化，可交互的AI数字分身 | 5000-20000元前期 + 分成 |
| **内容加速器** | 知识博主、自媒体创作者、行业KOL | AI处理80%标准化内容，人工聚焦20%个性化打磨 | SaaS订阅 + 1对1咨询 |

### 1.3 与IPulse的关系

IPulse是本平台的参考原型和核心引擎来源：

- **继承**: Pipeline架构(Discovery→Ranking→Generation→Adaptation→Quality→Publish)、插件化平台/Source体系、Persona概念
- **升级**: 单用户→多租户SaaS、CLI→Web UI、SQLite→PostgreSQL、简单prompt persona→完整风格建模、无RAG→知识库+RAG
- **新增**: 用户系统、订阅支付、数据看板、多平台分发（小红书/微博/微信/Twitter）、内容日历、素材库

---

## 2. 系统架构总览

### 2.1 架构模式: 模块化单体 (Modular Monolith)

**选择理由:**
- 项目初期团队规模小，微服务带来不必要的部署和运维复杂度
- 模块化单体在代码层面强制模块边界，未来可机械式拆分为微服务
- IPulse已有的插件化模式（PlatformRegistry, BaseSource）天然适合模块化单体

### 2.2 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                     WEB UI (Next.js 14 App Router)                │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ │
│  │Dashboard│ │Content   │ │Persona   │ │Analytics│ │Settings  │ │
│  │         │ │Studio    │ │Studio    │ │        │ │          │ │
│  └─────────┘ └──────────┘ └──────────┘ └────────┘ └──────────┘ │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────┴─────────────────────────────────────┐
│                    API LAYER (FastAPI)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │Auth      │ │Tenant    │ │Content   │ │Analytics         │   │
│  │(JWT+RBAC)│ │Manager   │ │Pipeline  │ │+Reporting        │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────┴─────────────────────────────────────┐
│                    DOMAIN SERVICES (Python)                       │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │Content Pipeline │  │Persona Engine   │  │Knowledge Base   │  │
│  │(继承IPulse)     │  │(风格建模+克隆)  │  │(RAG + 向量搜索) │  │
│  │- Discovery      │  │- Tone analysis  │  │- Doc ingestion  │  │
│  │- Ranking        │  │- Style transfer │  │- Embedding      │  │
│  │- Generation     │  │- Voice cloning  │  │- Semantic search│  │
│  │- Adaptation     │  │- Few-shot tuning│  │- Context window │  │
│  │- Quality Gate   │  │                 │  │                 │  │
│  │- Publishing     │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │Publish Hub      │  │Analytics Engine │  │Subscription     │  │
│  │(多平台分发)     │  │(反馈闭环)       │  │& Billing        │  │
│  │- Xiaohongshu    │  │- Metrics collect│  │- Plan management│  │
│  │- Weibo          │  │- Insight gen    │  │- Payment(Stripe)│  │
│  │- WeChat MP      │  │- Prompt optimize│  │- Revenue share  │  │
│  │- Twitter/X      │  │- A/B testing    │  │                 │  │
│  │- Douyin         │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────┴─────────────────────────────────────┐
│                    DATA LAYER                                     │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐   │
│  │PostgreSQL│ │Redis         │ │Milvus/   │ │S3/MinIO      │   │
│  │(主数据库)│ │(缓存+队列)   │ │Qdrant    │ │(媒体存储)    │   │
│  │          │ │              │ │(向量库)  │ │              │   │
│  └──────────┘ └──────────────┘ └──────────┘ └──────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 模块边界与依赖

```
                    ┌──────────┐
                    │  Web UI  │
                    └────┬─────┘
                         │ (仅依赖API)
                    ┌────┴─────┐
                    │ API Layer│
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    ┌─────┴─────┐ ┌──────┴──────┐ ┌─────┴─────┐
    │  Tenant   │ │  Content    │ │ Analytics │
    │  + Auth   │ │  Pipeline   │ │           │
    └─────┬─────┘ └──────┬──────┘ └─────┬─────┘
          │              │              │
          └──────────────┼──────────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
        ┌─────┴─────┐ ┌──┴────┐ ┌──┴──────────┐
        │ Persona   │ │Publish│ │Knowledge Base│
        │ Engine    │ │Hub    │ │+ RAG         │
        └───────────┘ └───────┘ └─────────────┘
```

模块间通过明确的接口（Python Protocol/ABC）通信，不允许跨模块直接导入内部实现。

---

## 3. 技术选型

### 3.1 后端

| 层面 | 技术 | 理由 |
|------|------|------|
| **语言** | Python 3.12+ | 与IPulse一致，AI/ML生态最成熟 |
| **Web框架** | FastAPI | 异步原生支持，自动OpenAPI文档，类型安全 |
| **ORM** | SQLAlchemy 2.0 (async) + Alembic | 成熟稳定，异步支持好，迁移工具完善 |
| **任务队列** | Celery + Redis broker | 异步内容生成、定时发布、批量处理 |
| **定时任务** | Celery Beat | 替代IPulse的cron，支持动态调度 |

### 3.2 前端

| 层面 | 技术 | 理由 |
|------|------|------|
| **框架** | Next.js 14 (App Router) | React生态，SSR/SSG，API Routes |
| **UI组件** | Tailwind CSS + shadcn/ui | 快速开发，组件可定制 |
| **状态管理** | React Query (TanStack) + Zustand | 服务端状态+客户端状态分离 |
| **富文本** | TipTap | 内容编辑，可扩展 |

### 3.3 数据层

| 层面 | 技术 | 理由 |
|------|------|------|
| **主数据库** | PostgreSQL 16 | 多租户、JSONB支持、全文搜索、成熟生态 |
| **缓存** | Redis | 会话、API限流、任务队列、热点数据 |
| **向量数据库** | Milvus (自建) 或 Qdrant (轻量) | 知识库语义搜索、内容去重、相似推荐 |
| **对象存储** | MinIO (自建) / S3 (云) | 图片、视频素材、内容附件 |
| **搜索引擎** | Elasticsearch (可选) | 内容全文搜索、日志分析 |

### 3.4 AI/ML

| 层面 | 技术 | 理由 |
|------|------|------|
| **LLM抽象** | LangChain + 直接SDK | 继承IPulse经验，复杂场景用LangChain，简单场景直接用SDK |
| **模型供应商** | OpenAI GPT-4o + Anthropic Claude 4.x | 双供应商策略，互为fallback |
| **国内模型** | 百度文心/阿里通义 (可选) | 国内用户访问稳定，中文优化更好 |
| **Embedding** | text-embedding-3-large / BGE-M3 | 中英文双语向量化 |
| **Prompt管理** | 自建Prompt Registry (DB + Git版本化) | IPulse的prompt散落在代码和YAML中，需要集中管理 |
| **评估** | LLM-as-Judge + 规则引擎 | 内容质量打分、风格一致性检验 |

### 3.5 DevOps

| 层面 | 技术 |
|------|------|
| **容器化** | Docker + Docker Compose (开发) / Kubernetes (生产) |
| **CI/CD** | GitHub Actions |
| **监控** | Prometheus + Grafana (指标) / Sentry (错误) |
| **日志** | 结构化JSON日志 → ELK/Loki |

---

## 4. 核心领域模块

### 4.1 用户与租户管理 (Tenant & Auth)

```
┌──────────────────────────────────────────┐
│              Tenant Management            │
│                                           │
│  Workspace (租户)                         │
│  ├── Tenant ID (隔离边界)                 │
│  ├── Plan/Subscription                    │
│  ├── Members (多用户协作)                 │
│  │   ├── Owner (创建者，完全控制)         │
│  │   ├── Admin (管理内容、查看分析)       │
│  │   ├── Editor (创建编辑内容)            │
│  │   └── Viewer (只读查看)               │
│  ├── Personas (多个人设)                  │
│  └── Settings (平台连接、偏好)            │
└──────────────────────────────────────────┘
```

**多租户隔离策略**: 共享数据库 + Tenant ID列隔离（每个表带tenant_id）+ Row-Level Security

**认证方案**: JWT (access + refresh token) + OAuth2 social login

### 4.2 内容管线 (Content Pipeline) — 继承并扩展IPulse

```
原IPulse Pipeline (6阶段) → 扩展为8阶段:

┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Discovery │ → │ Ranking  │ → │ Research │ → │Generation│
│ 热点发现 │   │ 选题排序 │   │ 素材搜集 │   │ 内容生成 │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                    │
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────┴─────┐
│Publishing│ ← │ Quality  │ ← │ Human    │ ← │Adaptation │
│ 多平台发布│   │ Gate     │   │ Review   │   │ 平台适配  │
└──────────┘   │ 质量把关 │   │ 人工审核 │   └───────────┘
               └──────────┘   └──────────┘
```

**新增阶段说明:**

- **Research (素材搜集)**: 在生成前自动从知识库检索相关素材、历史爆款内容、行业数据，注入生成prompt — 这是IPulse最缺的能力
- **Human Review (人工审核)**: 生成内容先进入审核队列，创作者审核/微调后方可发布。支持Web UI内嵌编辑器直接修改

**Pipeline状态机:**

```
DRAFT → RESEARCHING → GENERATING → REVIEW → APPROVED/REJECTED
  ↓                                               ↓
SCHEDULED → PUBLISHING → PUBLISHED → ARCHIVED
```

**内容类型支持:**
- 图文笔记 (小红书/微博)
- 长文章 (微信公众号)
- 短视频脚本 (抖音/视频号)
- Twitter Thread
- 问答内容 (知乎)

### 4.3 人设引擎 (Persona Engine) — 核心差异化

```
┌─────────────────────────────────────────────────────┐
│                 Persona Engine                       │
│                                                     │
│  输入: 创作者历史内容(文章/视频/语音) + 偏好设置    │
│                                                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────────┐   │
│  │Tone       │  │Style      │  │Narrative      │   │
│  │Analyzer   │  │Extractor  │  │Template Builder│  │
│  │           │  │           │  │               │   │
│  │- 语言风格 │  │- 排版偏好 │  │- 开头模式     │   │
│  │- 常用词汇 │  │- 配图风格 │  │- 论证结构     │   │
│  │- 情绪倾向 │  │- 色彩体系 │  │- 互动方式     │   │
│  │- 专业术语 │  │- 字体选择 │  │- 结尾钩子     │   │
│  └───────────┘  └───────────┘  └───────────────┘   │
│                                                     │
│  输出: Persona Profile (JSON + 向量嵌入)            │
│  ├── system_prompt (动态生成，含风格示例)           │
│  ├── few_shot_examples (精选代表性内容)             │
│  ├── style_vector (风格向量，用于一致性检测)        │
│  ├── banned_patterns (避免的表达方式)               │
│  └── visual_theme (配色、排版、字体)                │
└─────────────────────────────────────────────────────┘
```

**风格建模方法 (三层递进):**

1. **L1 - 基础Prompt建模** (继承IPulse): YAML配置 → system_prompt注入，适合新用户快速上手
2. **L2 - Few-Shot建模**: 从用户历史内容中自动选取代表性样本作为few-shot示例，显著提升风格一致性
3. **L3 - 风格微调**: 对高频用户使用LoRA微调开源模型（如Qwen），实现真正的"风格克隆"

**风格一致性检测:**
- 生成内容 vs Persona Profile的embedding余弦相似度
- 低于阈值则自动重新生成或标记为需人工审核

### 4.4 知识库与RAG (Knowledge Base + RAG)

```
┌─────────────────────────────────────────────────────┐
│              Knowledge Base System                   │
│                                                     │
│  数据摄入管道:                                       │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐         │
│  │Upload   │ → │Chunking  │ → │Embedding │         │
│  │(多格式) │   │(语义分块)│   │(向量化)  │         │
│  └─────────┘   └──────────┘   └─────┬────┘         │
│                                     │               │
│  检索增强生成:                      ↓               │
│  ┌──────────┐   ┌─────────┐   ┌──────────┐         │
│  │Query     │ → │Hybrid   │ → │Context   │         │
│  │Rewrite   │   │Search   │   │Assembly  │         │
│  │(查询改写)│   │(混合检索)│   │(上下文组装)│        │
│  └──────────┘   └─────────┘   └──────────┘         │
│                     │                               │
│              ┌──────┴──────┐                        │
│              │             │                        │
│         Vector Search  BM25/Keyword                 │
│         (语义相似)     (关键词匹配)                 │
│                                                     │
│  知识类型:                                          │
│  ├── 创作者历史内容 (文章/视频逐字稿/语音转录)     │
│  ├── 行业知识库 (专业术语、常见问题、数据)          │
│  ├── 爆款素材库 (历史高互动内容、标题模板)          │
│  └── 竞品分析 (同类创作者的内容策略)               │
└─────────────────────────────────────────────────────┘
```

**Hybrid Search策略:**
- 向量检索 (Milvus/Qdrant): 语义相似度，适合"类似主题的内容"
- 关键词检索 (BM25/PostgreSQL FTS): 精确匹配，适合"提到某概念的所有内容"
- 融合排序: Reciprocal Rank Fusion (RRF)

**RAG使用场景:**
- 内容生成前: 检索相关素材和历史内容注入prompt
- 数字分身: 检索知识库回答用户问题
- 内容去重: 检测新内容与已发布内容的相似度
- 选题推荐: 从知识库中发现可复用的主题角度

### 4.5 发布中心 (Publish Hub) — 扩展IPulse的多平台能力

```
┌──────────────────────────────────────────────┐
│              Publish Hub                      │
│                                               │
│  统一发布接口 (BasePlatform ABC，继承IPulse)  │
│                                               │
│  ┌──────────┐ ┌──────┐ ┌──────┐ ┌─────────┐ │
│  │Xiaohongshu│ │Weibo │ │WeChat│ │Twitter  │ │
│  │小红书     │ │微博  │ │公众号│ │/X       │ │
│  │           │ │      │ │      │ │         │ │
│  │- 图文笔记 │ │- 微博│ │- 图文│ │- Tweet  │ │
│  │- 视频笔记 │ │- 头条│ │- 视频│ │- Thread │ │
│  │- 商品标签 │ │- 投票│ │- 付费│ │- Poll   │ │
│  └──────────┘ └──────┘ └──────┘ └─────────┘ │
│                                               │
│  ┌──────────┐ ┌──────────┐                    │
│  │Douyin    │ │Zhihu     │                    │
│  │抖音      │ │知乎      │                    │
│  │          │ │          │                    │
│  │- 短视频  │ │- 回答    │                    │
│  │- 图文    │ │- 文章    │                    │
│  │- 直播    │ │- 想法    │                    │
│  └──────────┘ └──────────┘                    │
│                                               │
│  通用能力:                                    │
│  ├── Content Adaptation (格式+长度适配)       │
│  ├── Media Processing (图片裁剪/水印/压缩)    │
│  ├── Schedule & Queue (定时发布+队列管理)     │
│  ├── Rate Limiting (平台频率限制)             │
│  └── Cross-post Analytics (跨平台效果对比)    │
└──────────────────────────────────────────────┘
```

**平台接入优先级:**
1. 小红书 (核心，最高优先级)
2. 微信公众号
3. 微博
4. Twitter/X (已由IPulse实现基础，直接迁移)
5. 抖音
6. 知乎

### 4.6 分析与反馈闭环 (Analytics & Feedback Loop)

```
┌─────────────────────────────────────────────────┐
│            Analytics Engine                      │
│                                                  │
│  数据采集层:                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │Platform  │ │Content   │ │User Behavior │    │
│  │Metrics   │ │Pipeline  │ │(Web UI)      │    │
│  │(API采集)│ │Metrics   │ │              │    │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘    │
│       └─────────────┼─────────────┘             │
│                     ↓                            │
│  分析层:                                         │
│  ┌──────────────────────────────────────────┐   │
│  │  - 内容表现分析 (互动率/转化/增长)       │   │
│  │  - 受众画像 (兴趣/活跃时间/地域)         │   │
│  │  - 选题效果对比 (什么主题最受欢迎)       │   │
│  │  - 风格一致性监控                         │   │
│  │  - A/B测试引擎 (标题/封面/发布时间)      │   │
│  └──────────────────────────────────────────┘   │
│                     ↓                            │
│  反馈闭环:                                       │
│  ┌──────────────────────────────────────────┐   │
│  │  Metrics Data → Prompt Optimization       │   │
│  │                                           │   │
│  │  - 高互动内容特征 → 调整Generation Prompt │   │
│  │  - 低互动主题 → 调整Ranking权重            │   │
│  │  - 最佳发布时间 → 更新Schedule配置         │   │
│  │  - 受众偏好词汇 → 更新Persona Tone Guide   │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 4.7 订阅与支付 (Subscription & Billing)

```
Plan Tier:
┌──────────────────────────────────────────────────────┐
│ Free          │ Pro            │ Enterprise           │
│ (免费试用)    │ (月费500-2000) │ (定制报价)           │
├───────────────┼────────────────┼──────────────────────┤
│ 1 persona     │ 5 personas     │ 无限personas         │
│ 3篇/周        │ 10篇/天        │ 无限                 │
│ 1个平台       │ 3个平台        │ 所有平台             │
│ 基础模板      │ 高级模板+L2    │ 定制+L3风格微调      │
│ 基础分析      │ 深度分析+A/B   │ 专属数据看板         │
│ 社区支持      │ 优先支持       │ 1对1顾问             │
│               │ 7天试用        │ 按月/年flexible       │
└──────────────────────────────────────────────────────┘
```

**支付集成**: Stripe (国际) + 支付宝/微信支付 (国内)
**数字分身额外**: 初始化费5000-20000元 (数据采集+模型训练) + 月收入分成10-20%

---

## 5. AI/ML 架构

### 5.1 模型路由策略

```
                    ┌─────────────┐
                    │ Model Router│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────┴────┐ ┌────┴────┐ ┌─────┴─────┐
         │Primary  │ │Fallback │ │Cost-Opt   │
         │(最高质量)│ │(容错)   │ │(低成本)   │
         └────┬────┘ └────┬────┘ └─────┬─────┘
              │            │            │
    ┌─────────┼────────────┼────────────┼─────────┐
    │         │            │            │         │
  GPT-4o  Claude 4.x  文心一言    GPT-4o-mini
  (OpenAI)(Anthropic)  (百度)     (OpenAI)
```

**Per-Task模型配置 (扩展IPulse的models.yaml):**

| 任务 | 主模型 | 备选模型 | 温度 | 说明 |
|------|--------|---------|------|------|
| topic_ranking | gpt-4o-mini | claude-haiku-4-5 | 0.1 | 便宜快速即可 |
| content_generation | claude-sonnet-4-6 | gpt-4o | 0.7 | 核心创作能力 |
| style_analysis | claude-sonnet-4-6 | gpt-4o | 0.3 | 需要深度理解 |
| quality_check | gpt-4o-mini | - | 0.0 | 规则+LLM双检 |
| research_query | gpt-4o-mini | - | 0.1 | RAG查询改写 |
| digital_twin_chat | claude-sonnet-4-6 | gpt-4o | 0.6 | 数字分身对话 |
| analytics_insight | claude-sonnet-4-6 | gpt-4o | 0.5 | 分析报告 |
| translation | gpt-4o | - | 0.3 | 翻译任务 |

### 5.2 Prompt管理体系

```
Prompt Registry (DB Table):
┌──────────────────────────────────────────────────────┐
│ prompts                                               │
├──────────────────────────────────────────────────────┤
│ id, name, version, persona_id, task_type,            │
│ system_template, user_template, variables (JSONB),   │
│ model_config (JSONB), is_active, created_at          │
│                                                      │
│ + Git-backed version history for audit trail         │
│ + Each content generation records which prompt ver   │
│   was used (for performance traceability)            │
└──────────────────────────────────────────────────────┘
```

**Prompt优化闭环:**
```
Content Performance Data
        │
        ▼
┌─────────────────┐
│ Analyze what     │
│ worked/didn't    │
│ (LLM-as-Judge)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate prompt  │
│ variants         │
│ (自动建议改进)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ A/B test         │
│ (新prompt vs旧)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Auto-promote     │
│ winner           │
│ (或人工审核)     │
└─────────────────┘
```

### 5.3 Agent工作流

针对数字分身等复杂场景，引入Agent架构:

```
Digital Twin Agent:
┌────────────────────────────────────────┐
│         Orchestrator Agent             │
│  (理解用户意图，分配子任务)            │
└────────┬──────────┬──────────┬─────────┘
         │          │          │
    ┌────┴────┐ ┌───┴────┐ ┌──┴─────────┐
    │Knowledge│ │Content │ │Consultation │
    │Retrieval│ │Generator│ │Planner     │
    │Tool     │ │Tool    │ │Tool        │
    └─────────┘ └────────┘ └────────────┘
```

---

## 6. 数据模型设计

### 6.1 核心实体关系图

```
┌──────────┐    1:N    ┌──────────┐    1:N    ┌──────────┐
│  Tenant  │──────────→│  User    │──────────→│  Session │
│(Workspace)│          │          │           │          │
└────┬─────┘           └──────────┘           └──────────┘
     │
     │ 1:N
     ├──────────────→ ┌──────────────┐
     │                 │   Persona    │
     │                 │ (人设配置)   │
     │                 └──────┬───────┘
     │                        │ 1:N
     │                 ┌──────┴───────┐
     │                 │ PersonaSample│
     │                 │ (风格样本)   │
     │                 └──────────────┘
     │
     │ 1:N              ┌──────────────┐    1:N    ┌──────────────┐
     ├──────────────→   │   Content    │←──────────│ContentVersion│
     │                  │  (内容记录)  │           │(版本历史)    │
     │                  └──────┬───────┘           └──────────────┘
     │                         │
     │                         │ 1:N
     │                  ┌──────┴───────┐
     │                  │ Publication  │
     │                  │ (发布记录)   │
     │                  └──────┬───────┘
     │                         │ 1:N
     │                  ┌──────┴───────┐
     │                  │   Metrics    │
     │                  │ (互动数据)   │
     │                  └──────────────┘
     │
     │ 1:N              ┌──────────────┐
     ├──────────────→   │  Knowledge   │
     │                  │  Document    │
     │                  │ (知识库文档) │
     │                  └──────┬───────┘
     │                         │ 1:N
     │                  ┌──────┴───────┐
     │                  │  Chunk       │
     │                  │ (文档分块)   │
     │                  └──────────────┘
     │
     │ 1:N              ┌──────────────┐
     ├──────────────→   │ Subscription │
     │                  │ (订阅记录)   │
     │                  └──────────────┘
     │
     │ 1:N              ┌──────────────┐
     └──────────────→   │PlatformAccount│
                        │ (平台账号绑定)│
                        └──────────────┘
```

### 6.2 核心表设计 (PostgreSQL)

```sql
-- 租户/工作空间
tenants (
    id UUID PK,
    name VARCHAR(255),
    slug VARCHAR(100) UNIQUE,     -- URL标识
    plan_tier VARCHAR(50),        -- free/pro/enterprise
    settings JSONB,               -- 全局设置
    created_at, updated_at
)

-- 用户 (属于某个租户)
users (
    id UUID PK,
    tenant_id UUID FK → tenants,
    email VARCHAR(255),
    display_name VARCHAR(100),
    role VARCHAR(20),             -- owner/admin/editor/viewer
    avatar_url TEXT,
    password_hash TEXT,
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    created_at, updated_at
)

-- 人设配置 (核心!)
personas (
    id UUID PK,
    tenant_id UUID FK → tenants,
    name VARCHAR(100),
    language VARCHAR(10),         -- zh/en/ja
    system_prompt TEXT,           -- 动态生成的完整system prompt
    tone_instruction TEXT,        -- 风格指令
    style_profile JSONB,          -- 风格分析结果 (词汇特征/情绪倾向/句式等)
    style_vector VECTOR(1536),    -- pgvector 风格向量
    few_shot_examples JSONB,      -- [{input, output, score}]
    visual_theme JSONB,           -- {colors, fonts, layout, image_style}
    banned_patterns TEXT[],       -- 避免的词汇/表达
    focus_areas TEXT[],           -- 关注领域
    keywords TEXT[],              -- 核心关键词
    content_types TEXT[],         -- 内容类型
    is_active BOOLEAN,
    created_at, updated_at
)

-- 内容 (管线产物)
contents (
    id UUID PK,
    tenant_id UUID FK → tenants,
    persona_id UUID FK → personas,
    topic_id UUID FK → topics,   -- 选题
    title VARCHAR(500),
    draft_content TEXT,           -- AI生成的初稿
    final_content TEXT,           -- 人工修改后的终稿
    prompt_version VARCHAR(50),   -- 生成使用的prompt版本
    model_used VARCHAR(100),      -- 使用的模型
    generation_tokens INT,        -- token消耗
    status VARCHAR(30),           -- draft/researching/generating/review/approved/scheduled/publishing/published/archived
    quality_score FLOAT,          -- 质量分
    style_consistency FLOAT,      -- 风格一致性分
    scheduled_at TIMESTAMP,       -- 计划发布时间
    published_at TIMESTAMP,
    created_at, updated_at
)

-- 发布记录 (一条content可发多平台)
publications (
    id UUID PK,
    content_id UUID FK → contents,
    platform VARCHAR(50),         -- xiaohongshu/weibo/wechat/twitter/douyin/zhihu
    platform_post_id VARCHAR(255),-- 平台返回的帖子ID
    platform_url TEXT,            -- 公开访问URL
    status VARCHAR(30),           -- pending/published/failed/deleted
    error_message TEXT,
    publish_metadata JSONB,       -- 平台特定字段
    published_at TIMESTAMP
)

-- 互动指标 (时间序列)
metrics (
    id UUID PK,
    publication_id UUID FK → publications,
    collected_at TIMESTAMP,
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    saves INT DEFAULT 0,
    views INT DEFAULT 0,
    clicks INT DEFAULT 0,
    followers_gained INT DEFAULT 0,
    raw_data JSONB               -- 平台原始数据
)

-- 知识库文档
knowledge_docs (
    id UUID PK,
    tenant_id UUID FK → tenants,
    persona_id UUID FK → personas,
    title VARCHAR(500),
    source_type VARCHAR(50),      -- article/video_transcript/voice/upload
    source_url TEXT,
    content_text TEXT,            -- 原始文本
    file_path TEXT,               -- 原始文件路径(S3)
    metadata JSONB,
    created_at
)

-- 知识库分块 (向量搜索用)
knowledge_chunks (
    id UUID PK,
    doc_id UUID FK → knowledge_docs,
    chunk_index INT,
    chunk_text TEXT,
    embedding VECTOR(1536),       -- pgvector
    metadata JSONB,
    created_at
)
-- 索引: IVFFlat或HNSW on embedding

-- 选题库
topics (
    id UUID PK,
    tenant_id UUID FK → tenants,
    source VARCHAR(100),          -- 来源平台
    source_id VARCHAR(255),       -- 原始ID
    title VARCHAR(500),
    summary TEXT,
    url TEXT,
    heat_score FLOAT,             -- 热度分 (0-1)
    ai_rank_score FLOAT,          -- AI排序分
    metadata JSONB,
    title_hash VARCHAR(64),       -- SHA256去重
    discovered_at TIMESTAMP,
    UNIQUE(source, source_id)
)

-- 提示词模板 (版本化管理)
prompts (
    id UUID PK,
    persona_id UUID FK → personas,
    task_type VARCHAR(50),
    version VARCHAR(20),
    system_template TEXT,
    user_template TEXT,
    variables JSONB,
    model_config JSONB,
    is_active BOOLEAN DEFAULT true,
    performance_score FLOAT,      -- 基于历史内容表现的评分
    created_at
)
-- UNIQUE(persona_id, task_type, version)

-- 管线运行记录
pipeline_runs (
    id UUID PK,
    tenant_id UUID FK → tenants,
    persona_id UUID FK → personas,
    content_id UUID FK → contents,
    stages_completed JSONB,       -- [{stage, status, timestamp}]
    errors JSONB,
    context_snapshot JSONB,       -- 断点恢复
    started_at, completed_at
)

-- 订阅
subscriptions (
    id UUID PK,
    tenant_id UUID FK → tenants UNIQUE,
    plan_tier VARCHAR(50),
    status VARCHAR(20),           -- active/trialing/past_due/canceled
    current_period_start,
    current_period_end,
    payment_provider VARCHAR(50), -- stripe/alipay/wechat
    provider_subscription_id VARCHAR(255),
    created_at, updated_at
)
```

### 6.3 数据隔离策略

- 所有业务表都带 `tenant_id`
- 查询层通过中间件自动注入 `WHERE tenant_id = current_tenant_id`
- 使用 PostgreSQL Row-Level Security 作为双重保障
- 向量数据通过 `tenant_id` 过滤

---

## 7. API 设计

### 7.1 API 路由结构

```
/api/v1/
├── /auth
│   ├── POST   /register           # 注册
│   ├── POST   /login              # 登录
│   ├── POST   /refresh            # 刷新token
│   └── POST   /logout             # 登出
│
├── /tenants
│   ├── GET    /{id}               # 获取租户信息
│   ├── PATCH  /{id}               # 更新租户设置
│   └── GET    /{id}/members       # 成员列表
│
├── /personas
│   ├── GET    /                   # 人设列表
│   ├── POST   /                   # 创建人设
│   ├── GET    /{id}               # 人设详情
│   ├── PATCH  /{id}               # 更新人设
│   ├── DELETE /{id}               # 删除人设
│   ├── POST   /{id}/analyze       # 分析上传内容，提取风格
│   └── GET    /{id}/samples       # 风格样本列表
│
├── /contents
│   ├── GET    /                   # 内容列表 (支持筛选/分页)
│   ├── POST   /                   # 创建内容 (触发pipeline)
│   ├── GET    /{id}               # 内容详情
│   ├── PATCH  /{id}               # 编辑内容 (人工审核)
│   ├── DELETE /{id}               # 删除内容
│   ├── POST   /{id}/approve       # 审核通过
│   ├── POST   /{id}/reject        # 驳回
│   ├── POST   /{id}/regenerate    # 重新生成
│   ├── POST   /{id}/schedule      # 定时发布
│   └── POST   /{id}/publish       # 立即发布
│
├── /topics
│   ├── GET    /                   # 选题列表
│   ├── POST   /discover           # 触发热点发现
│   └── GET    /{id}               # 选题详情
│
├── /publish
│   ├── GET    /accounts           # 平台账号列表
│   ├── POST   /accounts           # 绑定平台账号
│   ├── DELETE /accounts/{id}      # 解绑
│   └── GET    /queue              # 发布队列
│
├── /knowledge
│   ├── GET    /docs               # 知识库文档列表
│   ├── POST   /docs/upload        # 上传文档
│   ├── DELETE /docs/{id}          # 删除文档
│   ├── POST   /docs/{id}/reindex  # 重新索引
│   └── POST   /search             # 语义搜索
│
├── /analytics
│   ├── GET    /dashboard          # 总览数据
│   ├── GET    /contents/{id}      # 单篇分析
│   ├── GET    /personas/{id}      # 人设维度分析
│   └── GET    /report             # 周/月报告
│
├── /subscription
│   ├── GET    /                   # 当前订阅状态
│   ├── POST   /checkout           # 创建订阅
│   ├── POST   /cancel             # 取消订阅
│   └── POST   /webhook            # 支付回调
│
└── /digital-twin
    ├── POST   /{persona_id}/init  # 初始化数字分身
    ├── POST   /{persona_id}/chat  # 与数字分身对话
    └── GET    /{persona_id}/stats # 数字分身使用统计
```

### 7.2 WebSocket 端点

```
/ws/pipeline/{content_id}     # 管线进度实时推送
/ws/notifications             # 系统通知
```

### 7.3 API 统一响应格式

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 150
  }
}
```

---

## 8. 多租户设计

### 8.1 租户识别

- JWT token中包含 `tenant_id`
- API中间件提取并注入请求上下文
- 所有DB查询自动添加tenant过滤

### 8.2 资源配额

```json
// tenant.quota (JSONB)
{
  "personas_max": 1,
  "contents_per_day": 3,
  "platforms_max": 1,
  "knowledge_docs_max": 10,
  "team_members_max": 1,
  "ai_tokens_per_month": 50000,
  "digital_twin_enabled": false,
  "style_finetune_enabled": false
}
```

### 8.3 自定义域名

企业版支持: `{custom-domain}` → iPerson平台，白标方案

---

## 9. 集成与部署

### 9.1 部署架构 (Docker Compose - 开发/小规模)

```yaml
# docker-compose.yml
services:
  api:
    build: ./backend
    depends_on: [postgres, redis, minio]
    
  worker:
    build: ./backend
    command: celery -A app.worker worker
    
  beat:
    build: ./backend
    command: celery -A app.worker beat
    
  web:
    build: ./frontend
    depends_on: [api]
    
  postgres:
    image: pgvector/pgvector:pg16  # 含向量扩展
    
  redis:
    image: redis:7-alpine
    
  minio:
    image: minio/minio
    
  nginx:
    image: nginx:alpine
    # 反向代理 + SSL终止
```

### 9.2 社交媒体平台集成

| 平台 | API | 认证 | 能力 |
|------|-----|------|------|
| 小红书 | 开放平台API | OAuth2 | 发布图文/视频笔记、获取数据 |
| 微信公众号 | 公众号API | 开发者凭证 | 发布图文、获取阅读数据 |
| 微博 | 微博开放平台 | OAuth2 | 发微博、获取互动数据 |
| Twitter/X | API v2 (tweepy) | OAuth 1.0a | 发推/线程、获取指标 |
| 抖音 | 开放平台API | OAuth2 | 发布视频、获取数据 |
| 知乎 | 知乎API | OAuth2 | 回答问题、发布文章 |

### 9.3 定时任务 (Celery Beat)

```python
# schedule配置 (数据库存储，支持Web UI动态调整)
SCHEDULE = {
    "discover_topics": {
        "task": "pipeline.discover_topics",
        "schedule": crontab(hour="*/2"),     # 每2小时
    },
    "generate_content": {
        "task": "pipeline.generate_content",
        "schedule": crontab(hour="8,14,20"),  # 每日3次
    },
    "collect_metrics": {
        "task": "analytics.collect_metrics",
        "schedule": crontab(hour="*/6"),      # 每6小时
    },
    "weekly_report": {
        "task": "analytics.weekly_report",
        "schedule": crontab(hour="9", minute="0", day_of_week="1"),  # 每周一早9点
    },
}
```

---

## 10. 开发路线图

### Phase 1: MVP 核心管线 (8-12周)

**目标**: 单租户可用的内容生成管线 + 基础Web UI

- [ ] FastAPI项目搭建，基础中间件（日志/错误处理/CORS）
- [ ] PostgreSQL + Alembic 数据模型
- [ ] 用户注册/登录 (JWT)
- [ ] Persona管理 CRUD + L1基础Prompt建模
- [ ] Content Pipeline (继承IPulse代码): Discovery → Generation → Quality → Review
- [ ] 小红书平台接入 (发布)
- [ ] 基础Dashboard (内容列表 + 简单指标)
- [ ] Next.js前端 (内容管理 + 人设配置)

### Phase 2: 多租户 + 知识库 (6-8周)

- [ ] 多租户隔离 (tenant_id + RLS)
- [ ] 订阅/支付集成 (Stripe基础版)
- [ ] 知识库: 文档上传 → Chunking → Embedding → 向量搜索
- [ ] RAG集成到Content Pipeline (Research阶段)
- [ ] L2 Few-Shot风格建模
- [ ] 人工审核工作流完善

### Phase 3: 多平台 + 分析 (6-8周)

- [ ] 微信公众号接入
- [ ] 微博接入
- [ ] 完整Analytics Engine (指标采集 + 数据看板 + 周报)
- [ ] A/B测试引擎基础版
- [ ] 反馈闭环: 指标 → Prompt优化建议

### Phase 4: 数字分身 + 高级功能 (8-12周)

- [ ] 数字分身Agent (Orchestrator + Knowledge Retrieval + Content Generation)
- [ ] 付费问答系统
- [ ] L3 风格微调 (LoRA)
- [ ] 企业版: 白标方案/自定义域名/团队协作
- [ ] 抖音平台接入

---

## 附录A: 与IPulse的代码复用映射

| IPulse模块 | iPerson复用方式 |
|-----------|---------------|
| `pipeline/orchestrator.py` | 核心逻辑迁移到Celery task，PipelineContext改为DB持久化 |
| `pipeline/stages.py` | Stage基类复用，StageSkip/StageAbort语义保持 |
| `discovery/` (BaseSource, HN, Zhihu) | 插件化接口复用，新增小红书/微博Source |
| `content/generator.py` | LCEL链式调用改为PromptRegistry + ModelRouter模式 |
| `content/adapters/` | 扩展为多平台Adapter体系 |
| `content/quality.py` | 规则引擎保留，新增LLM Quality Check |
| `publishing/` (BasePlatform, Twitter) | Twitter直接迁移，新增各平台实现 |
| `models/factory.py` | ModelFactory升级为ModelRouter (含fallback + cost优化) |
| `state/repository.py` | SQLite → SQLAlchemy async + PostgreSQL，接口语义保持 |
| `utils/config.py` | YAML配置 → DB存储 + 环境变量，env interpolation保留 |
| `utils/retry.py` | 直接复用 |
| `content/templates/` | 废弃，改为PromptRegistry管理 |

---

## 附录B: 关键技术风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|---------|
| 小红书API限制/封号 | 核心功能不可用 | RPA方案兜底，多账号轮换，频率控制 |
| LLM输出风格不一致 | 内容质量波动 | 风格一致性检测 + 自动重生成 + 人工兜底 |
| 向量检索精度不足 | RAG效果差 | Hybrid Search (向量+关键词) + 迭代优化分块策略 |
| 平台API变更 | 发布失败 | 适配器模式隔离，版本化API调用，降级方案 |
| 用户数据隐私 | 合规风险 | 数据加密，租户隔离，可选择私有化部署(企业版) |

---

> **下一步**: 评审本设计文档 → 确定Phase 1开发排期 → 开始后端项目搭建