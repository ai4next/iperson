# iPerson 平台架构优化设计

> 日期: 2026-05-15
> 状态: 待实现
> 优先级: P0-P3

## 1. 概述

本文档定义 iPerson 通用全自动个人 IP 运营平台在 Phase 1-4 基础上的架构优化方案，涵盖自动配图生成、平台集成与自动发布、插件生态与可扩展性、内容智能深化四个方向。

## 2. 自动配图生成 (P0)

### 2.1 设计目标

在内容生成管线中自动为文章生成配图，提升内容视觉表现力。

### 2.2 架构

新增 `media.image_gen` 插件，插入 Pipeline 中 audit 之后、publish 之前：

```
research → generation → humanizer → audit → [image_gen] → publish
```

### 2.3 插件定义

```yaml
- plugin: media.image_gen
  config:
    provider: openai              # openai / stability
    model: dall-e-3
    style: "flat illustration, warm tones"
    count: 2                      # 生成配图数量
    cover: true                   # 是否生成封面图
    aspect_ratio: "16:9"          # 封面图比例
```

### 2.4 模块结构

```
iperson/core/media/
├── __init__.py
├── image_gen.py          # ImageGenerator 基类
├── providers/
│   ├── openai.py         # DALL-E 3 适配器
│   └── stability.py      # Stability AI 适配器
└── schemas.py            # 图片元数据模型

iperson/pipeline/plugins/media/
├── __init__.py
└── image_gen.py          # ImageGenPlugin
```

### 2.5 核心逻辑

1. **主题提取**: 从 `ctx.generated_content` 中提取 2-3 个关键主题/段落作为图片 prompt
2. **Prompt 构建**: 结合人设风格 + 配置的 style 参数生成图片描述
3. **图片生成**: 调用外部 API 生成图片，下载到本地
4. **注入文章**: 将 `![img](path)` 插入文章对应位置
5. **存储**: 图片存入 `output/{topic}/media/`，封面图命名为 `cover.{ext}`

### 2.6 数据模型

```python
@dataclass
class GeneratedImage:
    path: Path
    prompt: str
    alt_text: str
    is_cover: bool
    position: int  # 在文章中的插入位置
```

### 2.7 错误处理

- API 调用失败: 跳过图片生成，不影响管线主流程
- 图片下载失败: 记录错误，继续管线
- 所有错误标记为 `recoverable`

## 3. 平台集成与自动发布 (P0)

### 3.1 设计目标

将发布从"写文件"升级为真正的发布管理系统，支持发布状态追踪、队列调度、定时发布。

### 3.2 两阶段策略

#### Phase A — 发布引擎重构

**发布状态机**:

```
draft → queued → publishing → published
                    ↓
                  failed → retry → publishing
```

**新增 CLI 命令**:

```bash
iperson publish run ...           # 生成 + 加入发布队列（现有增强）
iperson publish status [id]       # 查看发布队列状态
iperson publish schedule <id> --at "2026-05-16 10:00"  # 定时发布
iperson publish retry <id>        # 重试失败的发布
```

**存储增强**: `publications` 表新增字段:
- `scheduled_at` — 定时发布时间
- `retry_count` — 重试次数
- `error_message` — 失败原因

#### Phase B — 平台适配器

各平台适配器实现 `PlatformClient.publish()` 抽象方法:

| 平台 | API 方式 | 认证 |
|------|----------|------|
| 知乎 | 知乎专栏 API | Access Token |
| 小红书 | 小红书开放平台 | OAuth 2.0 |
| 微信 | 公众号素材管理 | AppID + AppSecret |
| 微博 | 微博开放平台 | OAuth 2.0 |
| 抖音 | 抖音开放平台 | OAuth 2.0 |

### 3.3 重试与限流

- 可重试错误: 网络超时、速率限制（429）、临时服务不可用
- 不可重试错误: 认证失败、内容违规、参数错误
- 限流: 每个平台独立令牌桶，配置 `requests_per_minute`

## 4. 插件生态与可扩展性 (P1)

### 4.1 设计目标

开放插件加载机制，支持第三方插件和 Webhook 事件系统。

### 4.2 插件加载器

```
PluginRegistry
  ├── builtin/        # 内置插件（现有）
  ├── file/           # 从 ~/.iperson/plugins/*.py 动态加载
  └── pip/            # 从 pip 包加载（命名约定 iperson-plugin-*）
```

**加载优先级**: builtin > file > pip（同名时内置优先，防止覆盖）

**插件协议**（复用现有 `StagePlugin` 基类）:

```python
class ExternalPlugin(StagePlugin):
    """第三方插件只需继承 StagePlugin + 实现 execute"""
    plugin_id: str = "custom.xxx"
```

### 4.3 CLI 命令

```bash
iperson plugin list                # 列出所有已安装插件
iperson plugin install <package>   # pip 安装 + 注册
iperson plugin remove <name>       # 卸载
```

### 4.4 Webhook 系统

**事件类型**:

| 事件 | 触发时机 | Payload |
|------|----------|---------|
| `pipeline.start` | 管线开始运行 | topic, recipe, persona |
| `pipeline.stage_complete` | 每个阶段完成 | stage, duration, status |
| `pipeline.error` | 管线出错 | stage, error_code, message |
| `pipeline.complete` | 管线完成 | status, content_id, errors |

**配置**:

```yaml
webhooks:
  - url: "https://hooks.example.com/iperson"
    events: ["pipeline.complete", "pipeline.error"]
    secret: "whsec_xxx"
```

## 5. 内容智能深化 (P1-P3)

### 5.1 外部趋势检测 (P2)

新增 `iperson/topics/trending.py`:

```bash
iperson topics trending                    # 全平台热点
iperson topics trending --source zhihu     # 指定平台
iperson topics trending --category tech    # 指定领域
```

- 各平台热点抓取器（知乎热榜、微博热搜、百度指数）
- 与现有 `TopicSuggestionEngine` 融合，trending 来源权重更高
- 缓存策略: 每小时刷新一次，避免频繁请求

### 5.2 内容安全护栏 (P1)

在 `quality.audit` 中增强:

- 敏感词库: `~/.iperson/security/blocked_words.txt`（可配置）
- 新增 `safety` 审核维度
- 新增 `on_fail: block` 策略（阻止发布，区别于 abort）

### 5.3 SEO 分析 (P3)

新增可选插件 `quality.seo`:

- 关键词密度分析
- 标题优化建议（长度、关键词位置）
- 可读性评分（段落长度、句式复杂度）
- 仅输出建议，不自动修改内容

## 6. 实施计划

| 优先级 | 方向 | 模块 | 工作量 |
|--------|------|------|--------|
| P0 | 自动配图生成 | `core/media/`, `plugins/media/image_gen.py` | 2-3天 |
| P0 | 发布引擎 Phase A | 状态机、CLI 增强、DB 迁移 | 2-3天 |
| P1 | 插件加载器 | `pipeline/loader.py`, CLI | 3-4天 |
| P1 | 内容安全护栏 | `audit` 增强、词库 | 1-2天 |
| P2 | 外部趋势检测 | `topics/trending.py` | 2-3天 |
| P2 | 平台适配器 Phase B | 各平台 client 实现 | 每平台 2-3天 |
| P3 | Webhook 系统 | `pipeline/hooks.py` | 2天 |
| P3 | SEO 分析 | `plugins/quality/seo.py` | 2天 |

## 7. 不变项

以下内容不在本次优化范围内:
- 数据驱动反馈闭环（用户明确暂缓）
- 内容生命周期管理（日历、版本、复用）
- 可观测性与可靠性（日志、监控、告警）