# iPerson 平台架构优化设计

> 日期: 2026-05-15
> 状态: 待实现
> 优先级: P0-P3

## 1. 概述

本文档定义 iPerson 通用全自动个人 IP 运营平台在 Phase 1-4 基础上的架构优化方案，核心设计理念是 **Hook 化**——所有"智能"能力作为 Hook 与管线解耦，通过 Hook Point 机制实现可组合、可配置、可插拔的扩展体系。

## 2. Hook 架构

### 2.1 设计目标

- 所有内容智能能力通过 Hook 实现，与 Pipeline 解耦
- 新增能力只需写一个新 Hook 类，无需改管线
- 同一个 Hook Point 可挂多个 Hook，按序执行
- Recipe 中声明哪些 Hook 启用，粒度到每个 stage
- Hook 通过插件系统加载，第三方可写自定义 Hook

### 2.2 Hook 定义

```python
@dataclass
class HookContext:
    pipeline_ctx: PipelineContext  # 完整管线上下文
    hook_point: str                # 当前 hook 点
    config: dict                   # 该 hook 的配置

class BaseHook(ABC):
    hook_id: str = ""
    hook_point: str = ""    # 绑定到哪个 hook 点
    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, ctx: HookContext) -> HookContext:
        ...
```

### 2.3 Hook Points

| Hook Point | 触发时机 | 可修改 | 用途 |
|---|---|---|---|
| `before.generation` | 生成前，prompt 已组装好 | 修改 `ctx.data["persona_engine"]`、注入额外 context | 趋势注入、安全护栏、风格调优 |
| `after.generation` | 生成后，内容已写入 `ctx.generated_content` | 修改 `ctx.generated_content`、写分析报告 | SEO 分析、内容扫描、自动配图触发 |
| `before.publish` | 发布前，内容已终稿 | 修改 `ctx.humanized_content` | 图片注入、格式微调 |
| `after.publish` | 发布后 | 只读，触发副作用 | Webhook 通知、数据采集 |

### 2.4 Recipe 集成

```yaml
stages:
  - plugin: research.kb_retrieve
  - plugin: generation.article
    hooks:
      before:
        - hook: intelligence.trending_inject
          config: { source: zhihu }
        - hook: safety.prompt_guard
      after:
        - hook: intelligence.seo_analyze
        - hook: safety.content_scan
  - plugin: quality.humanizer
  - plugin: publish.multiplatform
    hooks:
      before:
        - hook: media.image_gen
          config: { provider: openai, style: "flat illustration" }
      after:
        - hook: webhook.notify
```

### 2.5 模块结构

```
iperson/pipeline/
├── hook.py                # BaseHook, HookContext, HookRegistry
├── hook_orchestrator.py   # HookOrchestrator — 执行指定 hook point 的所有 hook
├── hooks/                 # 内置 hook 实现
│   ├── __init__.py
│   ├── trending_inject.py
│   ├── prompt_guard.py
│   ├── content_scan.py
│   ├── seo_analyze.py
│   ├── image_gen.py
│   └── webhook_notify.py
├── orchestrator.py        # 增强：在 stage 前后执行 hooks
```

### 2.6 HookOrchestrator

```python
class HookOrchestrator:
    def __init__(self, registry: HookRegistry):
        self.registry = registry

    async def execute_hooks(
        self,
        hook_point: str,
        pipeline_ctx: PipelineContext,
        stage_config: dict,
    ) -> PipelineContext:
        """Execute all hooks registered for a given hook point."""
        hooks = self.registry.get_hooks_for_point(hook_point)
        for hook_cls in hooks:
            hook_config = stage_config.get("hooks", {}).get(hook_point.split(".")[-1], {})
            hook_ctx = HookContext(
                pipeline_ctx=pipeline_ctx,
                hook_point=hook_point,
                config=hook_config,
            )
            result = await hook_cls().execute(hook_ctx)
            pipeline_ctx = result.pipeline_ctx
        return pipeline_ctx
```

### 2.7 Pipeline 集成

在 `PipelineOrchestrator.run()` 中，每个 stage 执行前后插入 hook 调用：

```python
for stage_def in stages:
    # Before hooks
    ctx = await hook_orch.execute_hooks(f"before.{plugin_id}", ctx, stage_config)

    # Stage execution (existing)
    ctx = await plugin_instance.execute(ctx, stage_config)

    # After hooks
    ctx = await hook_orch.execute_hooks(f"after.{plugin_id}", ctx, stage_config)
```

## 3. 内置 Hook 实现

### 3.1 趋势注入 (`intelligence.trending_inject`)

- Hook Point: `before.generation`
- 抓取各平台热点（知乎热榜、微博热搜）
- 将热点话题注入到 generation 的 prompt context 中
- 缓存策略: 每小时刷新一次

### 3.2 安全护栏 (`safety.prompt_guard` + `safety.content_scan`)

- Hook Point: `before.generation` + `after.generation`
- `prompt_guard`: 在生成前检查 prompt 是否包含违规内容
- `content_scan`: 在生成后扫描内容，匹配敏感词库
- 敏感词库: `~/.iperson/security/blocked_words.txt`（可配置）
- 支持 `action: block | flag` 策略

### 3.3 SEO 分析 (`intelligence.seo_analyze`)

- Hook Point: `after.generation`
- 关键词密度分析
- 标题优化建议（长度、关键词位置）
- 可读性评分（段落长度、句式复杂度）
- 仅输出建议到 `ctx.data["seo_report"]`，不自动修改内容

### 3.4 自动配图 (`media.image_gen`)

- Hook Point: `before.publish`
- 从 `ctx.generated_content` 提取关键主题作为图片 prompt
- 调用 DALL-E 3 / Stability AI 生成配图
- 图片存入 `output/{topic}/media/`
- 将 `![img](path)` 注入到 `ctx.humanized_content`

### 3.5 Webhook 通知 (`webhook.notify`)

- Hook Point: `after.publish`
- 发送 HTTP POST 请求到配置的 URL
- 事件: `pipeline.complete`, `pipeline.error`
- Payload: topic, status, content_id, errors

## 4. 平台集成与自动发布 (P0)

### 4.1 设计目标

将发布从"写文件"升级为真正的发布管理系统，支持发布状态追踪、队列调度、定时发布。

### 4.2 两阶段策略

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

### 4.3 重试与限流

- 可重试错误: 网络超时、速率限制（429）、临时服务不可用
- 不可重试错误: 认证失败、内容违规、参数错误
- 限流: 每个平台独立令牌桶，配置 `requests_per_minute`

## 5. 插件生态与可扩展性 (P1)

### 5.1 设计目标

开放插件加载机制，支持第三方插件和 Hook。

### 5.2 插件加载器

```
PluginRegistry
  ├── builtin/        # 内置插件（现有）
  ├── file/           # 从 ~/.iperson/plugins/*.py 动态加载
  └── pip/            # 从 pip 包加载（命名约定 iperson-plugin-*）

HookRegistry
  ├── builtin/        # 内置 hook（同上）
  ├── file/           # 从 ~/.iperson/hooks/*.py 动态加载
  └── pip/            # 从 pip 包加载
```

**加载优先级**: builtin > file > pip（同名时内置优先，防止覆盖）

### 5.3 CLI 命令

```bash
iperson plugin list                # 列出所有已安装插件
iperson plugin install <package>   # pip 安装 + 注册
iperson plugin remove <name>       # 卸载
iperson hook list                  # 列出所有已安装 hook
```

## 6. 实施计划

| 优先级 | 方向 | 模块 | 工作量 |
|--------|------|------|--------|
| P0 | Hook 核心框架 | `hook.py`, `hook_orchestrator.py`, 管线集成 | 2天 |
| P0 | 发布引擎 Phase A | 状态机、CLI 增强、DB 迁移 | 2-3天 |
| P1 | 内置 Hook 实现 | 5 个内置 hook | 3-4天 |
| P1 | 插件/Hook 加载器 | `loader.py`, CLI | 2-3天 |
| P2 | 平台适配器 Phase B | 各平台 client 实现 | 每平台 2-3天 |

## 7. 不变项

以下内容不在本次优化范围内:
- 数据驱动反馈闭环（用户明确暂缓）
- 内容生命周期管理（日历、版本、复用）
- 可观测性与可靠性（日志、监控、告警）