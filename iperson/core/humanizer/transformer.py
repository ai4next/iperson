from __future__ import annotations

from typing import Any

# Ordered list of (old, new) replacement pairs.
# Order matters -- more specific/longer matches should come first.
REPLACEMENTS: list[tuple[str, str]] = [
    ("值得注意的是，", "其实"),
    ("值得注意的是 ", "有意思的是 "),
    ("总的来说，", "简单来说"),
    ("总的来说 ", "简单来说 "),
    ("综上所述，", "所以"),
    ("综上所述 ", "所以 "),
    ("毋庸置疑，", "毫无疑问"),
    ("不言而喻，", "很明显"),
    ("显而易见，", "很明显"),
    ("值得一提的是，", "对了"),
    ("不可否认，", "说实话"),
    ("从这个角度来看", "换个角度"),
    ("首先，", ""),
    ("其次，", ""),
    ("最后，", ""),
]


def replace_ai_phrases(text: str) -> dict[str, Any]:
    """Replace known AI phrases in the text with more natural alternatives.

    Args:
        text: The input text to transform.

    Returns:
        A dict with:
        - "text": the modified text
        - "changes": list of {"from": str, "to": str, "count": int} for each replacement applied
    """
    changes: list[dict[str, Any]] = []
    modified = text

    for old, new in REPLACEMENTS:
        if old in modified:
            count = modified.count(old)
            modified = modified.replace(old, new)
            changes.append({
                "from": old,
                "to": new,
                "count": count,
            })

    return {
        "text": modified,
        "changes": changes,
    }
