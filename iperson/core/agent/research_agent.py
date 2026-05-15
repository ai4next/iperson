from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from iperson.core.agent.tools import fetch_url_tool, kb_search_tool, web_search_tool

SYSTEM_PROMPT = """你是一名研究助手。你的任务是对给定主题进行全面研究。

你可以使用以下工具：
1. kb_search_tool(query) -- 搜索本地知识库
2. web_search_tool(query) -- 搜索互联网
3. fetch_url_tool(url) -- 获取特定URL的完整内容

请按以下步骤操作：
1. 首先在知识库中搜索该主题
2. 如果知识库结果不够充分，在网络上搜索
3. 获取最有前景的结果以获取完整内容
4. 综合一份有结构的研究摘要，包含来源引用

请以以下格式输出：
## INITIAL_CONTEXT
已有的知识库信息

## RESEARCH_FINDINGS
搜索到的补充信息

## INTEGRATED_SUMMARY
综合后的研究摘要"""


class ResearchAgent:
    """Agent that researches a topic using KB search and web search tools."""

    def __init__(
        self,
        llm: BaseChatModel,
        max_iterations: int = 10,
    ) -> None:
        self.llm = llm
        self.max_iterations = max_iterations
        self._agent: Any | None = None

    def _get_agent(self) -> Any:
        if self._agent is None:
            from langgraph.prebuilt import create_react_agent

            self._agent = create_react_agent(
                self.llm,
                [kb_search_tool, web_search_tool, fetch_url_tool],
                prompt=SYSTEM_PROMPT,
            )
        return self._agent

    async def research(self, topic: str, kb_context: str = "") -> str:
        """Research a topic and return enhanced context."""
        agent = self._get_agent()
        try:
            content = (
                f"研究主题：{topic}\n\n"
                f"初始知识库上下文：\n{kb_context if kb_context else '（无）'}"
            )
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=content)]}
            )
            # Extract the last AI message content as the research result
            for msg in reversed(result["messages"]):
                if hasattr(msg, "content") and msg.content and isinstance(msg.content, str):
                    return msg.content
            return kb_context
        except Exception:
            return kb_context