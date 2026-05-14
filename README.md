# iPerson — 通用全自动个人IP运营平台

> **AI辅助 · 人主导** — 用AI放大创作者的人格，而非替代它

iPerson 是一个 **CLI 优先** 的个人 IP 内容引擎，通过插件化管线编排内容生产流程，支持知识库驱动的内容生成、多维度质量审核、人设风格控制，以及多平台发布。

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

也支持按阶段配置不同的 LLM 提供商和模型：

```yaml
providers:
  - stage: default          provider: openai    model: gpt-4o          temperature: 0.7
  - stage: generation       provider: openai    model: gpt-4o          temperature: 0.8
  - stage: audit            provider: openai    model: gpt-4o          temperature: 0.3
  - stage: humanizer        provider: openai    model: gpt-4o          temperature: 0.5
```

所有配置项均可通过 `IPERSON_<KEY>` 环境变量覆盖（如 `IPERSON_LLM_API_KEY`）。

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

## CLI 命令参考

| 命令 | 说明 |
|------|------|
| `iperson publish run` | 运行内容生产管线（核心命令） |
| `iperson kb import` | 导入文档到知识库 |
| `iperson kb search` | 混合检索知识库 |
| `iperson persona create` | 创建/编辑创作者人设 |
| `iperson audit report` | 查看质量审核报告 |
| `iperson analytics collect` | 记录内容表现数据 |
| `iperson analytics report` | 查看内容表现分析 |
| `iperson topics suggest` | 基于 KB 和分析数据推荐选题 |
| `iperson agent run` | 运行单次自主内容生成 |
| `iperson agent auto` | 自动选题并生成内容 |
| `iperson tuning analyze` | 分析人设风格并给出调优建议 |
| `iperson --version` | 查看版本号 |

### `iperson publish run` 完整选项

```bash
iperson publish run <TOPIC>                # 内容主题（必填）
  --recipe, -r  <name>                     # Recipe 名称，默认 "quick"
  --persona, -p <name>                     # 人设名称
  --platform     <name>                    # 目标平台，默认 "xiaohongshu"
  --verbose                                # 显示详细输出（含插件注册、阶段耗时、内容预览等）
```

## 管线架构

内容生产采用 **插件化管线** 架构，每个阶段由 YAML Recipe 灵活编排：

```
┌─────────────────────────────────────────────────────────┐
│                     Pipeline                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │  Research   │→ │ Generation │→ │  Quality   │         │
│  │  素材检索    │  │  内容生成   │  │  质量把关   │         │
│  └────────────┘  └────────────┘  └────────────┘         │
│                        │                                 │
│                        ↓                                 │
│  ┌────────────┐  ┌────────────┐                          │
│  │  Publish   │← │   Human    │                          │
│  │  多平台发布  │  │   Review   │                          │
│  └────────────┘  │  人工审核   │                          │
│                   └────────────┘                          │
└─────────────────────────────────────────────────────────┘
```

### 内置阶段插件

| 阶段 | 插件 ID | 说明 |
|------|---------|------|
| Research | `research.kb_retrieve` | 从知识库检索 Top-K 相关素材 |
| Generation | `generation.article` | 结合人设与素材生成文章正文 |
| Quality | `quality.humanizer` | AI 痕迹淡化（检测 → 加权评分 → 局部改写），支持迭代 |
| Quality | `quality.audit` | 多维度质量审核（子指标评分 + 加权综合 + 改进建议） |
| Publish | `publish.multiplatform` | 多平台格式适配与内容导出 |

管线支持 CircuitBreaker 熔断保护、Recipe 预校验、on_error 策略（abort/skip）。

### Recipes（内容配方）

通过 YAML 编排各阶段插件及其配置。内置三种 Recipes：

- **完整模式** (`full.yaml`) — 深度内容：KB搜索(10条) → 生成 → 人味化 → 审核 → 三平台发布
- **极速模式** (`quick.yaml`) — 个人日更，5分钟出稿：KB搜索(5条) → 生成 → 人味化 → 审核 → 小红书发布
- **热点追稿** (`trending.yaml`) — 快速追热点，精简审核维度，失败仅标记不阻塞

Recipe 示例（`quick.yaml`）：

```yaml
name: "极速模式"
description: "个人创作者日更，5分钟出稿"
stages:
  - plugin: research.kb_retrieve
    config:
      top_k: 5
  - plugin: generation.article
  - plugin: quality.humanizer
    config:
      min_score: 0.35
      max_iterations: 2
  - plugin: quality.audit
    config:
      on_fail: regenerate
  - plugin: publish.multiplatform
    config:
      platforms: [xiaohongshu]
```

## 功能模块

### 知识库 (`iperson kb`)

基于 SQLite 的轻量级知识库，支持混合检索（BM25 + Embedding 向量搜索）：

- `kb import <path>` — 导入文档（支持 `.txt`, `.md`, `.py` 等），自动分块与向量化
- `kb search <query>` — 混合检索知识库（BM25 全文搜索 + Embedding 语义搜索融合）
- 底层组件：`chunker`（文本分块）、`loader`（文件加载）、`embedder`（向量化）、`bm25`（全文索引）、`vector_store`（向量存储）

### 人设引擎 (`iperson persona`)

定义和管理创作者人设，控制生成内容的风格与语气：

- 系统提示词（`system_prompt`）+ 语气指令（`tone_instruction`）+ 风格画像（`style_profile`）
- 少样本示例（`few_shot_examples`）+ 禁用词模式（`banned_patterns`）
- 人设文件以 YAML 格式存储于 `~/.iperson/personas/`
- 内置默认人设，含常用禁用词：*值得注意的是、总的来说、综上所述*

### 内容生成 (`generation.article`)

基于 LangChain 调用 LLM，结合人设引擎构建的 System Prompt 和知识库上下文生成文章：

- 支持 OpenAI / Anthropic 双提供商，自动路由
- 每阶段可独立配置 provider + model + temperature
- LLM 实例自动 LRU 缓存，避免重复创建

### AI 痕迹淡化 (`quality.humanizer`)

三段式管线：检测 AI 模式 → 评分 → 改写重试：

- **Detector**：识别 AI 生成文本的模式特征（排比句、过渡词、模板化表达等）
- **Scorer**：对检测结果打分（0~1），低于阈值触发改写
- **Transformer**：结合人设引擎的 tone instruction 进行改写，保留原文信息量

### 质量审核 (`quality.audit`)

从 6 个维度对生成内容进行评分（0~1）：

| 维度 | 说明 |
|------|------|
| keyword_fit | 关键词合规 — 敏感词/禁用词检测 |
| structure | 结构质量 — 段落、标题、逻辑结构 |
| platform_rules | 平台规则 — 各平台合规要求 |
| ai_score | AI 浓度 — AI 痕迹评分（越低越好） |
| style_consistency | 风格一致 — 是否匹配人设风格 |
| grounding | 事实依据 — 内容是否偏离知识库素材 |

审核结果以 JSON 报告输出到 `output/{timestamp}-{topic}/audit_report.json`。

### 多平台发布 (`publish.multiplatform`)

基于 Recipe 编排的最终阶段，将生成内容适配为目标平台格式：

- 支持小红书（`xiaohongshu`）、微信公众号（`wechat`）、知乎（`zhihu`）
- 平台内容输出到 `output/{timestamp}-{topic}/platforms/{platform}.md`
- 管线上下文传递、执行耗时追踪、错误处理（含重试机制）

## 输出目录结构

```
~/.iperson/
├── config.yaml              # 全局配置
├── data/
│   └── iperson.db           # SQLite 数据库
├── personas/                 # 人设 YAML 文件
└── output/                   # 管线输出
    └── {timestamp}-{topic}/
        ├── article.md                 # 原始生成内容
        ├── humanized_article.md        # 人味化后内容
        ├── audit_report.json          # 审核结果
        └── platforms/
            ├── xiaohongshu.md
            ├── wechat.md
            └── zhihu.md
```

## 数据持久化

SQLite 数据库（`~/.iperson/data/iperson.db`）包含以下表：

| 表名 | 说明 |
|------|------|
| `contents` | 内容记录（含草稿、终稿、审核分数） |
| `personas` | 人设持久化 |
| `publications` | 发布记录（平台、状态、时间） |
| `kb_docs` | 知识库文档 |
| `kb_chunks` | 文档分块（含向量 Embedding） |
| `audit_reports` | 审核报告 |
| `pipeline_runs` | 管线运行记录 |

## 技术栈

| 层 | 技术 |
|---|------|
| 语言 | Python 3.12+ |
| CLI 框架 | Typer + Rich |
| 存储 | SQLite (Pydantic 模型) |
| AI | LangChain (OpenAI / Anthropic / Gemini) |
| 向量搜索 | NumPy + scikit-learn (BM25 + Embedding) |
| 配置 | YAML + 环境变量覆盖 |
| 测试 | pytest, pytest-asyncio |
| 构建 | Hatchling |

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率报告
pytest --cov=iperson

# 运行特定测试
pytest tests/test_pipeline.py -v
pytest tests/test_audit_gate.py -v
```

当前测试覆盖范围：管线编排（含 CircuitBreaker 熔断）、插件注册、Recipe 校验、知识库检索/分块/混合搜索、内容生成、人味化（检测/评分/改写）、人设引擎、质量审核门控（含加权评分）、LLM 路由、集成测试。

## 路线图

- **Phase 1** (已完成): CLI MVP + 插件化管线 + 知识库 RAG + 质量审核 + 人味化
- **Phase 2** (已完成): Pipeline 弹性（CircuitBreaker + 错误恢复）+ Humanizer 质量提升 + 审核精准度优化 + Gemini 支持 + 管线加固
- **Phase 3** (已完成): 分析引擎（内容表现追踪）+ 平台 API 适配器（知乎/微博/抖音）+ 数据驱动优化
- **Phase 4** (已完成): 自动选题（KB + 分析数据）+ 数字分身 Agent（自主内容生成）+ 风格微调（AI模式分析 + 性能反馈调优）

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
iperson publish run --recipe quick --topic "示例选题" --verbose
```

## 项目结构

```
iperson/
├── pyproject.toml              # 项目元数据与依赖
├── recipes/                    # 内置 Recipe YAML
│   ├── full.yaml
│   ├── quick.yaml
│   └── trending.yaml
├── tests/                      # 测试套件（12 个测试文件）
├── iperson/
│   ├── cli/                    # CLI 入口
│   │   ├── app.py             # Typer 应用主入口
│   │   ├── publish_cmd.py     # publish 命令组
│   │   ├── kb_cmd.py          # kb 命令组
│   │   ├── persona_cmd.py     # persona 命令组
│   │   └── audit_cmd.py       # audit 命令组
│   ├── pipeline/               # 管线引擎
│   │   ├── orchestrator.py    # PipelineOrchestrator
│   │   ├── context.py         # PipelineContext（状态传递）
│   │   ├── recipe.py          # Recipe 加载
│   │   ├── registry.py        # 插件注册表
│   │   ├── plugin.py          # StagePlugin 基类
│   │   └── plugins/           # 内置插件实现
│   │       ├── research/kb_retrieve.py
│   │       ├── generation/article.py
│   │       ├── quality/audit.py
│   │       ├── quality/humanizer.py
│   │       └── publish/multiplatform.py
│   ├── core/                   # 核心业务逻辑
│   │   ├── persona/           # 人设引擎
│   │   ├── kb/                # 知识库
│   │   ├── generation/        # 内容生成
│   │   ├── humanizer/         # AI 痕迹淡化
│   │   ├── audit/             # 质量审核
│   │   └── output/            # 输出格式化
│   ├── storage/                # 数据持久化
│   │   ├── db.py             # SQLite 连接管理
│   │   └── models.py         # Pydantic 数据模型
│   └── utils/                  # 工具库
│       ├── llm.py            # LLM 客户端（含 DummyLLM 测试替身）
│       └── output.py         # 输出文件写入
```