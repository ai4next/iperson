# iPerson — 通用全自动个人IP运营平台

> 用AI放大创作者的人格，而非替代它

iPerson 是一个 **CLI 优先** 的个人 IP 内容引擎，通过插件化管线编排内容生产流程，支持知识库驱动的内容生成、多维度质量审核、人设风格控制，以及多平台发布。

## 快速开始

### 安装

```bash
# 通过 uv 安装
uv pip install iperson

# 或从源码安装
git clone https://github.com/ai4next/iperson.git
cd iperson
uv sync --all-extras
```

### 初始化配置

```bash
# 创建配置目录
mkdir -p ~/.iperson

# 编辑配置文件
vim ~/.iperson/config.yaml
```

```yaml
# ~/.iperson/config.yaml
llm:
  provider: openai              # 或 anthropic / gemini
  api_key: sk-xxx               # 你的 API Key
  model: gpt-4o                 # 生成模型
```

### 首次运行

```bash
# 1. 导入知识库文档（将你的素材喂给系统）
iperson kb import ./my-articles/

# 2. 创建人设（定义你的写作风格）
iperson persona create

# 3. 运行内容管线（自动选题 + 生成 + 发布）
iperson publish run

# 4. 查看输出
ls ~/.iperson/output/
```

> **说明**：`--topic` 为可选参数。不传时会根据知识库素材和人设自动选题。

---

## 配置参考

### 完整配置项

```yaml
# ~/.iperson/config.yaml

# LLM 全局配置
llm:
  provider: openai              # openai / anthropic / gemini
  api_key: sk-xxx
  model: gpt-4o

# 按阶段独立配置 LLM（覆盖全局配置）
providers:
  - stage: default              provider: openai    model: gpt-4o          temperature: 0.7
  - stage: generation           provider: openai    model: gpt-4o          temperature: 0.8
  - stage: audit                provider: openai    model: gpt-4o          temperature: 0.3
  - stage: humanizer            provider: openai    model: gpt-4o          temperature: 0.5

# 数据目录（默认 ~/.iperson/data）
data_dir: ~/.iperson/data
output_dir: ~/.iperson/output

# 数据库路径
db:
  path: ~/.iperson/data/iperson.db

# Webhook 通知（可选）
webhooks:
  - url: https://your-server.com/webhook
    secret: your-hmac-secret
```

### 环境变量覆盖

所有配置项均可通过 `IPERSON_<KEY>` 环境变量覆盖：

```bash
export IPERSON_LLM_API_KEY=sk-xxx
export IPERSON_LLM_MODEL=gpt-4o
export IPERSON_DB_PATH=/custom/path/iperson.db
```

嵌套字段使用下划线连接：`IPERSON_LLM_API_KEY` 对应 `llm.api_key`。

### 按阶段 LLM 配置

每个管道阶段可指定不同的 provider / model / temperature：

| 阶段 | 用途 | 推荐 temperature |
|------|------|-----------------|
| `default` | 未匹配阶段的回退配置 | 0.7 |
| `generation` | 内容生成（创意性要求高） | 0.8 |
| `audit` | 质量审核（需确定性判断） | 0.3 |
| `humanizer` | AI 痕迹淡化改写 | 0.5 |

未配置的阶段会自动回退到 `default`。

---

## 管线与 Pipeline

### 什么是 Pipeline？

Pipeline（管线）定义内容生产的节点顺序和每个节点的配置。每个**人设**都有自己的 Pipeline 配置，放在人设目录的 `config.yaml` 中。

### 默认 Pipeline

未配置时使用内置默认管线：素材检索 → 自动选题 → 内容生成 → 多平台发布。

### Pipeline 配置

在人设的 `config.yaml` 中添加 `pipeline` 字段即可自定义：

```yaml
# ~/.iperson/personas/{name}/config.yaml
is_active: true
pipeline:
  nodes:
    - id: research
      node: research.kb_retrieve
      config:
        top_k: 10

    - id: generate
      node: generation.article
      hooks:
        after:
          - hook: quality.humanizer
            config:
              min_score: 0.35
              max_iterations: 2

    - id: publish
      node: publish.multiplatform
      hooks:
        before:
          - hook: quality.platformize
            config:
              platforms: [xiaohongshu, wechat, zhihu]
      config:
        platforms: [xiaohongshu, wechat, zhihu]
```

每个节点支持的字段：

| 字段 | 说明 |
|------|------|
| `id` | 节点唯一标识 |
| `node` | 节点插件 ID（如 `research.kb_retrieve`） |
| `config` | 节点配置参数 |
| `hooks.before` | 执行前钩子列表 |
| `hooks.after` | 执行后钩子列表 |

---

## 钩子系统 (Hooks)

钩子是在管线阶段执行前后插入的扩展点，用于在不修改阶段插件的情况下增强管线能力。

### 内置钩子

| 钩子 ID | 挂载点 | 功能 | 配置参数 |
|---------|--------|------|----------|
| `intelligence.trending_inject` | `before.generation` | 从知乎/微博获取热点话题，注入生成上下文 | `source`: `zhihu` / `weibo` |
| `safety.prompt_guard` | `before.generation` | 检查生成环境是否完备（如人设引擎是否存在） | 无 |
| `intelligence.seo_analyze` | `after.generation` | 分析内容字数、可读性、关键词密度等 SEO 指标 | 无 |
| `safety.content_scan` | `after.generation` | 扫描生成内容中的屏蔽词 | 无 |
| `media.image_gen` | `before.publish` | 调用 DALL-E 生成封面和内文配图 | `provider`, `style`, `count`, `cover` |
| `webhook.notify` | `after.publish` | 管线完成后发送 HTTP 通知（HMAC-SHA256 签名） | 从 `config.yaml` 读取 `webhooks` 配置 |

### 在 Pipeline 中配置钩子

钩子在 Pipeline 的 `hooks` 字段中配置，分为 `before` 和 `after`：

```yaml
stages:
  - plugin: generation.article
    hooks:
      before:
        - hook: intelligence.trending_inject
          config: { source: zhihu }       # 传给钩子的配置
        - hook: safety.prompt_guard
      after:
        - hook: intelligence.seo_analyze
        - hook: safety.content_scan
```

### Webhook 配置

Webhook 通知钩子从全局配置读取目标地址：

```yaml
# ~/.iperson/config.yaml
webhooks:
  - url: https://your-server.com/pipeline/notify
    secret: your-hmac-secret
```

通知 payload 格式：

```json
{
  "event": "pipeline.complete",
  "topic": "你的选题",
  "status": "completed",
  "content_id": "xxx",
  "errors": []
}
```

请求头携带 `X-Webhook-Signature: <sha256-hex>` 用于验签。

### 自定义钩子

将继承 `BaseHook` 的 `.py` 文件放入 `~/.iperson/plugins/`，系统自动加载：

```python
# ~/.iperson/plugins/my_hook.py
from iperson.pipeline.hook import BaseHook, HookContext

class MyCustomHook(BaseHook):
    hook_id = "custom.my_hook"
    hook_point = "after.generation"       # 挂载点
    name = "My Custom Hook"
    description = "Does something useful"

    async def execute(self, ctx: HookContext) -> HookContext:
        # 读取配置（来自 pipeline 中 hooks 字段的 config）
        param = ctx.config.get("param", "default")
        # 操作管线上下文
        ctx.pipeline_ctx.data["my_result"] = param
        return ctx
```

### 查看已安装的钩子

```bash
iperson plugin list-plugins
```

同时列出已注册的插件和钩子。

---

## 插件管理

### 内置插件

| 插件 ID | 阶段 | 功能 |
|---------|------|------|
| `research.kb_retrieve` | Research | 从知识库检索 Top-K 相关素材 |
| `generation.article` | Generation | 结合人设与素材生成文章正文 |
| `quality.humanizer` | Quality | AI 痕迹淡化（检测 → 评分 → 改写） |
| `quality.audit` | Quality | 多维度质量审核 |
| `publish.multiplatform` | Publish | 多平台格式适配与内容导出 |

### 安装第三方插件

```bash
# 从 pip 安装（包名需以 iperson_plugin_ 开头）
iperson plugin install iperson_plugin_xxx

# 卸载
iperson plugin remove iperson_plugin_xxx

# 查看已安装的插件和钩子
iperson plugin list-plugins
```

### 开发自定义插件

将文件放入 `~/.iperson/plugins/` 即可自动加载：

```python
# ~/.iperson/plugins/my_plugin.py
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin

class MyPlugin(StagePlugin):
    plugin_id = "custom.my_plugin"
    name = "My Plugin"
    description = "Custom pipeline stage"
    category = "quality"
    version = "1.0.0"
    tags = ["custom"]
    config_schema = {}
    default_config = {}

    def execute(self, ctx: PipelineContext, config: dict) -> PipelineContext:
        # 实现你的阶段逻辑
        return ctx
```

然后在 Pipeline 中引用：

```yaml
stages:
  - plugin: custom.my_plugin
    config:
      your_param: value
```

## CLI 命令参考

| 命令 | 说明 |
|------|------|
| `iperson publish run` | 运行内容生产管线，支持自动选题（核心命令） |
| `iperson publish status` | 查看发布队列状态 |
| `iperson publish schedule` | 设置定时发布 |
| `iperson publish retry` | 重试失败的发布 |
| `iperson kb import` | 导入文档到知识库 |
| `iperson kb search` | 混合检索知识库 |
| `iperson persona create` | 创建/编辑创作者人设 |
| `iperson persona list` | 列出已保存的人设 |
| `iperson audit report` | 查看质量审核报告 |
| `iperson analytics collect` | 记录内容表现数据 |
| `iperson analytics report` | 查看内容表现分析 |
| `iperson topics suggest` | 基于 KB 和分析数据推荐选题 |
| `iperson agent run` | 运行单次自主内容生成 |
| `iperson agent auto` | 自动选题并生成 N 篇内容 |
| `iperson tuning analyze` | 分析人设风格并给出调优建议 |
| `iperson plugin list-plugins` | 列出已安装的插件和钩子 |
| `iperson plugin install` | 从 pip 安装插件 |
| `iperson plugin remove` | 卸载 pip 插件 |
| `iperson --version` | 查看版本号 |

### `iperson publish run` 完整选项

```bash
iperson publish run [TOPIC]                  # 内容主题（可选，留空则自动选题）
  --persona, -p    <name>                    # 人设名称
  --platform       <name>                    # 目标平台，默认 "xiaohongshu"
  --verbose                                  # 显示详细输出（含插件注册、阶段耗时、内容预览等）
```

## 管线架构

内容生产采用 **LangGraph 编排** 架构，每个阶段是一个 Node，Node 支持 pre/post hook 挂载：

```
┌────────────────────────────────────────────────────────────┐
│                       Pipeline                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Research   │→ │    Topic     │→ │  Generation  │     │
│  │   素材检索     │  │   Selection  │  │   内容生成     │     │
│  └──────────────┘  └──────────────┘  └──────┬───────┘     │
│                                              │              │
│                                        post-hook           │
│                                              │              │
│                                    ┌─────────▼────────┐    │
│                                    │  quality.humanizer│    │
│                                    │  AI痕迹淡化       │    │
│                                    └──────────────────┘    │
│                                              │              │
│                                              ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Publish    │← │  pre-hook    │← │  Generation  │     │
│  │  多平台发布    │  │ platformize  │  │  (输出)       │     │
│  │              │  │ 平台化适配    │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────────────────────────────┘
```

### 内置 Node

> 选题（Topic Selection）通过 pipeline-level `topic_selection: true` 开关控制，不由 Node 执行。

| Node | ID | 说明 |
|------|-----|------|
| Research | `research.kb_retrieve` | 从知识库检索 Top-K 相关素材 |
| Generation | `generation.article` | 结合人设与素材生成文章正文 |
| Topic Selection | `pipeline.topic_selection` (flag) | 自动选题（人设+KB匹配，Pipeline 级别开关） |
| Publish | `publish.multiplatform` | 多平台格式适配与内容导出 |

### 内置 Hook

| Hook | 挂载点 | 说明 |
|------|--------|------|
| `quality.humanizer` | `after.generate` | AI 痕迹淡化（检测 → 评分 → 改写迭代） |
| `quality.platformize` | `before.publish` | 按平台风格改写内容 |
| `intelligence.trending_inject` | `before.generate` | 热点话题注入生成上下文 |
| `safety.prompt_guard` | `before.generate` | 生成前安全检查 |
| `intelligence.seo_analyze` | `after.generate` | SEO 分析 |
| `safety.content_scan` | `after.generate` | 内容敏感词扫描 |
| `media.image_gen` | `before.publish` | 自动配图 |
| `webhook.notify` | `after.publish` | 管线完成通知 |

管线支持 CircuitBreaker 熔断保护、Pipeline 预校验、on_error 策略（abort/skip）。

### Pipelines（内容管线）

通过 YAML 编排各阶段插件及其配置。内置一套通用 Pipeline，差异化通过 hook 配置实现：

- **默认管线** (`default.yaml`) — KB搜索(10条) → 自动选题(人设匹配) → 生成 → 人味化 → 平台化适配 → 多平台发布

Pipeline 示例（`default.yaml`）：

```yaml
name: "default"
description: "通用内容管线"
topic_selection: true
nodes:
  - id: research
    node: research.kb_retrieve
    config:
      top_k: 10
  - id: generate
    node: generation.article
    hooks:
      after:
        - hook: quality.humanizer
          config:
            min_score: 0.35
            max_iterations: 2
  - id: publish
    node: publish.multiplatform
    hooks:
      before:
        - hook: quality.platformize
          config:
            platforms: [xiaohongshu, wechat, zhihu]
    config:
      platforms: [xiaohongshu, wechat, zhihu]
```

## 功能模块

### 知识库 (`iperson kb`)

基于 SQLite 的轻量级知识库，支持 BM25 全文检索：

- `kb import <path>` — 导入文档（支持 `.txt`, `.md`, `.py` 等），自动分块与索引
- `kb search <query>` — 检索知识库（BM25 全文搜索）
- 底层组件：`chunker`（文本分块）、`loader`（文件加载）、`bm25`（全文索引）

### 人设引擎 (`iperson persona`)

人设是创作者的数字灵魂，定义生成内容的风格与语气。每个人设是一个目录：

```
~/.iperson/personas/{name}/
├── soul.md       # 人设灵魂（Markdown，直接作为 LLM 系统提示）
└── config.yaml   # 配置（如 is_active）
```

`soul.md` 是自由格式的 Markdown，描述你的写作风格、语气、关注领域等，内容直接作为 LLM 系统提示：

```markdown
# 科技博主小明 的人设灵魂

## 基本定位
科技领域深度内容创作者，专注 AI 和编程。

## 语气风格
- 专业但不枯燥
- 数据驱动，每观点必有依据
- 善用类比解释复杂概念

## 写作规范
- 开头直接切入主题
- 多用短句，段落不超过 5 行
- 避免 AI 套话
```

```bash
# 创建人设（会生成 soul.md 模板）
iperson persona create 科技博主小明

# 编辑人设
vim ~/.iperson/personas/科技博主小明/soul.md

# 列出所有人设
iperson persona list
```

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

基于 Pipeline 编排的最终阶段，将生成内容适配为目标平台格式：

- 支持小红书（`xiaohongshu`）、微信公众号（`wechat`）、知乎（`zhihu`）
- 平台内容输出到 `output/{timestamp}-{topic}/platforms/{platform}.md`
- 管线上下文传递、执行耗时追踪、错误处理（含重试机制）

## 输出目录结构

```
~/.iperson/
├── config.yaml              # 全局配置
├── data/
│   └── iperson.db           # SQLite 数据库
├── personas/                 # 人设目录
│   └── {name}/
│       ├── soul.md          # 人设灵魂
│       └── config.yaml      # 人设配置
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
| `publications` | 发布记录（平台、状态、时间） |
| `kb_docs` | 知识库文档 |
| `kb_chunks` | 文档分块 |
| `content_metrics` | 内容表现数据（阅读/点赞/分享/评论） |

## 技术栈

| 层 | 技术 |
|---|------|
| 语言 | Python 3.12+ |
| CLI 框架 | Typer + Rich |
| 存储 | SQLite (Pydantic 模型) |
| AI | LangChain (OpenAI / Anthropic / Gemini) |
| 搜索 | BM25 全文搜索 |
| 配置 | YAML + 环境变量覆盖 |
| 测试 | pytest, pytest-asyncio |
| 构建 | uv + Hatchling |

## 测试

```bash
# 运行全部测试
uv run pytest

# 带覆盖率报告
uv run pytest --cov=iperson

# 运行特定测试
uv run pytest tests/test_pipeline.py -v
uv run pytest tests/test_audit_gate.py -v
```

当前测试覆盖范围：管线编排（含 CircuitBreaker 熔断）、插件注册、Pipeline 校验、知识库检索/分块/混合搜索、内容生成、人味化（检测/评分/改写）、人设引擎、自动选题、质量审核门控（含加权评分）、LLM 路由、集成测试。

## 开发

```bash
# 安装开发依赖（含所有 extras）
uv sync --all-extras

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
uv run mypy iperson/

# 运行管线（自动选题模式）
uv run iperson publish run --verbose

# 或指定选题
uv run iperson publish run "示例选题" --verbose
```

## 项目结构

```
iperson/
├── pyproject.toml              # 项目元数据与依赖
├── tests/                      # 测试套件（22 个测试文件）
├── iperson/
│   ├── cli/                    # CLI 入口
│   │   ├── app.py             # Typer 应用主入口
│   │   ├── publish_cmd.py     # publish 命令组（run/status/schedule/retry）
│   │   ├── kb_cmd.py          # kb 命令组
│   │   ├── persona_cmd.py     # persona 命令组
│   │   ├── audit_cmd.py       # audit 命令组
│   │   ├── agent_cmd.py       # agent 命令组
│   │   ├── analytics_cmd.py   # analytics 命令组
│   │   ├── topics_cmd.py      # topics 命令组
│   │   ├── tuning_cmd.py      # tuning 命令组
│   │   └── plugin_cmd.py      # plugin 命令组
│   ├── pipeline/               # 管线引擎
│   │   ├── orchestrator.py    # PipelineOrchestrator
│   │   ├── context.py         # PipelineContext（状态传递）
│   │   ├── pipeline.py          # Pipeline 加载与验证
│   │   ├── registry.py        # 插件注册表
│   │   ├── plugin.py          # StagePlugin 基类
│   │   ├── loader.py          # FilePluginLoader / PipPluginLoader
│   │   ├── hook.py            # BaseHook / HookRegistry
│   │   ├── hook_orchestrator.py # HookOrchestrator
│   │   ├── circuit_breaker.py # 熔断保护
│   │   ├── errors.py          # PipelineError
│   │   ├── plugins/           # 内置插件实现
│   │   │   ├── research/kb_retrieve.py
│   │   │   ├── generation/article.py
│   │   │   ├── quality/audit.py
│   │   │   ├── quality/humanizer.py
│   │   │   └── publish/multiplatform.py
│   │   └── hooks/             # 内置钩子实现
│   │       ├── trending_inject.py
│   │       ├── prompt_guard.py
│   │       ├── seo_analyze.py
│   │       ├── content_scan.py
│   │       ├── image_gen.py
│   │       └── webhook_notify.py
│   ├── core/                   # 核心业务逻辑
│   │   ├── persona/           # 人设引擎
│   │   ├── kb/                # 知识库（分块/加载/向量/BM25/混合搜索）
│   │   ├── generation/        # 内容生成
│   │   ├── humanizer/         # AI 痕迹淡化
│   │   ├── audit/             # 质量审核（6 维度）
│   │   ├── media/             # 图像生成
│   │   ├── output/            # 输出 Pydantic 模型
│   │   └── security/          # 屏蔽词列表
│   ├── agent/                 # 数字分身自主代理
│   ├── analytics/             # 内容分析引擎
│   ├── topics/                # 选题建议引擎
│   ├── tuning/                # 风格调优引擎
│   ├── publish/               # 发布引擎 + 平台客户端
│   ├── storage/               # 数据持久化（SQLite + Pydantic）
│   └── utils/                 # 工具库（LLM 工厂、文件输出）
```