from __future__ import annotations

import re
from collections import Counter

from iperson.pipeline.hook import BaseHook, HookContext


class SeoAnalyzeHook(BaseHook):
    hook_id: str = "intelligence.seo_analyze"
    hook_point: str = "after.generation"
    name: str = "SEO Analyze"
    description: str = "Analyze content for SEO optimization suggestions"

    async def execute(self, ctx: HookContext) -> HookContext:
        content = ctx.pipeline_ctx.generated_content
        if not content:
            return ctx

        word_count = len(content)
        sentences = re.split(r"[。！？\n]", content)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_len = word_count / max(len(sentences), 1)

        # Readability: shorter sentences = more readable
        readability = min(1.0, 50.0 / max(avg_sentence_len, 1))

        # Title check
        has_title = bool(re.search(r"^#\s+.+", content, re.MULTILINE))
        title_suggestions = []
        if not has_title:
            title_suggestions.append("内容缺少标题 (#)，建议添加")

        # Keyword density (simple: most frequent non-stopword)
        words = re.findall(r"[一-鿿]+", content)
        word_freq = Counter(words)
        top_keywords = word_freq.most_common(5)

        suggestions = title_suggestions
        if readability < 0.5:
            suggestions.append("句子偏长，建议缩短以提高可读性")
        if word_count < 200:
            suggestions.append("内容偏短（不足200字），建议扩充")

        ctx.pipeline_ctx.data["seo_report"] = {
            "word_count": word_count,
            "sentence_count": len(sentences),
            "avg_sentence_length": round(avg_sentence_len, 1),
            "readability_score": round(readability, 2),
            "has_title": has_title,
            "top_keywords": top_keywords,
            "suggestions": suggestions,
        }
        return ctx