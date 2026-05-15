from __future__ import annotations

from pathlib import Path

# Built-in blocked words
DEFAULT_BLOCKED_WORDS: list[str] = [
    "总的来说", "综上所述", "总而言之", "首先", "其次", "最后",
    "值得注意的是", "需要指出的是", "不可否认", "毋庸置疑",
    "绝对", "一定", "必须", "百分之百", "永远", "完全", "所有",
]


def load_blocked_words() -> list[str]:
    """Load blocked words from config file, falling back to defaults."""
    wordlist_path = Path("~/.iperson/security/blocked_words.txt").expanduser()
    if wordlist_path.exists():
        return [
            line.strip()
            for line in wordlist_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
    return DEFAULT_BLOCKED_WORDS