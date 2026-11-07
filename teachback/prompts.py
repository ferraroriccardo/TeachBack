"""Carica i system prompt versionati in prompts/*.md."""
from functools import lru_cache
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache(maxsize=None)
def load(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
