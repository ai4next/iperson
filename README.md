# iPerson — 通用全自动个人IP运营平台

> **AI辅助 · 人主导** — 用AI放大创作者的人格，而非替代它

iPerson 是一个 **CLI 优先** 的个人 IP 内容引擎，通过插件化管线编排内容生产流程，支持知识库驱动的内容生成、多维度质量审核、人设风格化，以及多平台发布。

## 快速开始

### 安装

```bash
# 通过 pip 安装
pip install iperson

# 或从源码安装
git clone https://github.com/ai4next/iperson.git
cd iperson
pip install -e ".[all]"
```

### 配置

```bash
# 初始化配置文件
mkdir -p ~/.iperson
cp recipes/*.yaml ~/.iperson/data/recipes/

# 配置 API Key（也支持环境变量 IPERSON_LLM_API_KEY）
vim ~/.iperson/config.yaml
```

```yaml
# ~/.iperson/config.yaml
llm:
  provider: openai         # 或 anthropic
  api_key: sk-xxx
  model: gpt-4o
  embedding_model: text-embedding-3-small
```

### 基础使用

```bash
# 查看帮助
iperson

# 导入知识库文档
iperson kb import ./docs

# 搜索知识库
iperson kb search "你的主题"

# 创建人设
iperson persona create

# 运行管线（按 recipe 顺序执行多阶段）
iperson publish run --recipe quick --topic "你的选题"

# 查看质量审核报告
iperson audit report ./output/xxx/
```

## 管线架构

内容生产采用 **插件化管线** 架构，每个阶段可由配置文件（Recipe）灵活编排：

```
┌─────────────────────────────────────────────────────┐
│                   Pipeline                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Research  │→ │Generation│→ │ Quality  │           │
│  │ 素材检索  │  │ 内容生成  │  │ 质量把关  │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                       │                              │
│                       ↓                              │
│  ┌──────────┐  ┌──────────┐                          │
│  │ Publish  │← │ Human    │                          │
│  │ 多平台发布│  │ Review   │                          │
│  └──────────┘  │ 人工审核  │                          │
│                 └──────────┘                          │
└─────────────────────────────────────────────────────┘
```

### 内置阶段插件

| 阶段 | 插件 ID | 说明 |
|------|---------|------|
| Research | `research.kb_retrieve` | 从知识库检索相关素材 |
| Generation | `generation.article` | 结合人设与素材生成文章 |
| Quality | `quality.humanizer` | AI 痕迹淡化，提升自然度 |
| Quality | `quality.audit` | 多维度质量审核 |
| Publish | `publish.multiplatform` | 多平台格式适配与发布 |

### Recipes（内容配方）

通过 YAML 定义不同场景的内容生产流程。内置三种 Recipes：

- **完整模式** (`full.yaml`): 深度内容 — KB检索 → 生成 → 润色 → 审核 → 多平台发布
- **极速模式** (`quick.yaml`): 个人日更，5分钟出稿 — KB检索 → 生成 → 润色 → 审核 → 单平台发布
- **热点追稿** (`trending.yaml`): 快速追热点，精简审核维度

## 功能模块

### 知识库 (`iperson kb`)

基于 SQLite 的轻量级知识库，支持混合检索（BM25 + Embedding 向量搜索）：

- `kb import <path>` — 导入文档（支持 `.txt`, `.md`, `.py` 等）
- `kb search <query>` — 混合检索知识库
- 自动分块与向量化，支持语义搜索和关键词搜索

### 人设引擎 (`iperson persona`)

定义和管理创作者人设，控制生成内容的风格与语气：

- 系统提示词、语气指令、风格画像
- 少样本示例与禁用词模式
- 内容类型与关注领域配置

### 质量审核 (`iperson audit`)

从 5 个维度对生成内容进行评分（0~1）：

| 维度 | 说明 |
|------|------|
| 关键词合规 | 敏感词/禁用词检测 |
| 结构质量 | 段落、标题、逻辑结构 |
| 平台规则 | 各平台合规要求 |
| AI 浓度 | AI 痕迹评分 |
| 事实依据 | 内容是否偏离知识库素材 |

### 多平台发布 (`iperson publish`)

基于 Recipe 编排完整管线（知识库 → 生成 → 质量 → 发布），支持：

- 小红书、微信公众号、知乎等平台适配
- 管线上下文传递与错误追踪
- 输出结果持久化存储

## 技术栈

| 层 | 技术 |
|---|------|
| 语言 | Python 3.12+ |
| CLI 框架 | Typer + Rich |
| 存储 | SQLite (Pydantic 模型) |
| AI | OpenAI / Anthropic API |
| 向量搜索 | NumPy + scikit-learn (BM25 + Embedding) |
| 测试 | pytest, pytest-asyncio |
| 构建 | Hatchling |

## 路线图

- **Phase 1** (当前): CLI MVP + 插件化管线 + 知识库 RAG + 质量审核
- **Phase 2**: 多租户隔离 + 订阅支付 + Web Dashboard
- **Phase 3**: 分析引擎 + 反馈闭环 + 更多平台适配
- **Phase 4**: 数字分身 Agent + 风格微调 + 企业版

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
mypy iperson/

# 运行管线（dry-run 模式）
iperson publish run --recipe quick --topic "示例选题"
```
