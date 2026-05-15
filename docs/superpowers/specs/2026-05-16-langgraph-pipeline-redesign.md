# iPerson LangGraph Pipeline 重构设计

> 日期: 2026-05-16
> 状态: 待实现

## 1. 概述

将 iPerson 管线引擎从当前的顺序循环架构重构为 **LangGraph 编排** 架构。每个阶段作为 LangGraph Node，Node 支持 pre-hook / post-hook 挂载，实现更灵活的管线编排和扩展能力。

## 2. 管线流程

```
LangGraph Graph
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  [Research] ──→ [Topic Selection] ──→ [Generate] ──→ [Publish] │
│      │                │                  │              │      │
│      │                │            post-hook        pre-hook     │
│      │                │                  │              │      │
│      │                │          humanizer      platformize     │
└──────────────────────────────────────────────────────────┘
```

### 2.1 阶段说明

| Node | 插件 | 输入 | 输出 |
|------|------|------|------|
| Research | `research.kb_retrieve` | 无（从 KB 检索） | `kb_context` |
| Topic Selection | `builtin.topic_selection` | `kb_context`, persona | `topic` |
| Generate | `generation.article` | `topic`, `kb_context` | `generated_content` |
| Publish | `publish.multiplatform` | `platform_contents` 或 `generated_content` | 输出文件 |

### 2.2 Hook

| Hook | 挂载点 | 输入 | 输出 |
|------|--------|------|------|
| Humanizer | `after.generate` | `generated_content` | 改写后的 `generated_content` |
| Platformize | `before.publish` | `generated_content` | `platform_contents: {platform: content}` |

## 3. State 设计

```python
class PipelineState(TypedDict):
    # 流程控制
    status: str                         # running / completed / error

    # 各阶段产出
    kb_context: str                     # Research → 知识库素材
    topic: str                          # Topic Selection → 选题
    generated_content: str              # Generate → 完整文章
    platform_contents: dict[str, str]   # Platformize → {平台名: 适配后内容}

    # 运行时
    errors: list[dict]
    data: dict                          # 扩展字段（persona_engine, llm_client 等）
```

## 4. Node 接口

每个 Node 是一个异步函数，接收 State 返回 State 的部分更新：

```python
async def research_node(state: PipelineState) -> dict:
    # 从知识库检索素材
    return {"kb_context": "..."}

async def topic_selection_node(state: PipelineState) -> dict:
    # 基于 KB 素材和人设自动选题
    return {"topic": "..."}

async def generate_node(state: PipelineState) -> dict:
    # 结合人设与素材生成文章
    return {"generated_content": "..."}

async def publish_node(state: PipelineState) -> dict:
    # 输出到各平台文件
    return {"status": "completed"}
```

## 5. Hook 机制

每个 Node 支持 pre-hooks 和 post-hooks，在 Node 执行前后按序修改 State：

```
execute_node(node_id, state, pre_hooks, post_hooks):
    for hook in pre_hooks:
        state = hook.execute(state)
    state = node_fn(state)
    for hook in post_hooks:
        state = hook.execute(state)
    return state
```

### 5.1 Humanizer Hook

- Hook Point: `after.generate`
- 读取 `state.generated_content`
- 淡化 AI 痕迹（检测 → 评分 → 改写迭代）
- 写回 `state.generated_content`

### 5.2 Platformize Hook

- Hook Point: `before.publish`
- 读取 `state.generated_content`
- 按各平台风格改写（小红书口语化、公众号深度叙事、知乎专业严谨）
- 写入 `state.platform_contents = {xiaohongshu: "...", wechat: "...", zhihu: "..."}`

## 6. Pipeline YAML 格式

```yaml
name: "完整模式"
description: "深度内容，从KB检索到多平台发布"
topic_selection: true
nodes:
  - id: research
    node: research.kb_retrieve
    config:
      top_k: 10

  - id: topic_selection
    node: builtin.topic_selection

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

## 7. 架构变化

### 移除
- `quality.audit` 阶段插件
- `PipelineOrchestrator` 顺序循环编排（由 LangGraph 替代）

### 改造
- `quality.humanizer` → 从 StagePlugin 改为 BaseHook
- `publish.multiplatform` → 支持读取 `platform_contents`，fallback 到 `generated_content`
- Pipeline YAML 中 `stages` → `nodes`，`plugin` → `node`

### 新增
- `quality.platformize` hook 实现
- LangGraph Graph 组装逻辑
- Node pre/post hook 执行机制

## 8. 默认 Pipeline

一套通用流程，差异化通过 hook 配置实现：

```yaml
name: "default"
description: "通用内容管线：检索 → 选题 → 生成 → 发布"
topic_selection: true
nodes:
  - id: research
    node: research.kb_retrieve
    config:
      top_k: 10

  - id: topic_selection
    node: builtin.topic_selection

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

### 文件变更

- `pipelines/full.yaml` → 删除
- `pipelines/quick.yaml` → 删除
- `pipelines/trending.yaml` → 删除
- `pipelines/default.yaml` → 新增（默认管线）
- `README.md` → 更新架构图、内置 Pipeline 表、示例、项目结构

用户通过 CLI 参数或全局配置覆盖 hook 配置来实现差异化（如只发小红书、调整 humanizer 参数等）。