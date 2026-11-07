"""Caricamento del materiale del corso (concetti, slide, dati sintetici della classe)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from teachback import guardrails
from teachback.contracts import Concept, Course

DATA = Path(__file__).resolve().parent.parent / "data" / "courses"


@lru_cache(maxsize=None)
def load_course(course_id: str) -> Course:
    raw = json.loads((DATA / course_id / "concepts.json").read_text(encoding="utf-8"))
    return Course(
        id=raw["id"], title=raw["title"], official=raw["official"],
        concepts=[Concept(**c) for c in raw["concepts"]],
        exam_questions=raw.get("exam_questions", []),
    )


@lru_cache(maxsize=None)
def load_slides(course_id: str) -> str:
    """Testo delle slide, già ripulito: il materiale è un dato, mai un'istruzione."""
    path = DATA / course_id / "slides.md"
    if not path.exists():
        return ""
    return guardrails.sanitize_material(path.read_text(encoding="utf-8"))


def slide_chunks(course_id: str) -> list[str]:
    """Una stringa per slide ("## Slide N - ..."), usata per il controllo di somiglianza."""
    text = load_slides(course_id)
    parts = re.split(r"(?m)^## ", text)
    return [p.strip() for p in parts if p.strip().lower().startswith("slide")]


def load_class_snapshot(course_id: str) -> dict:
    path = DATA / course_id / "class_snapshot.json"
    if not path.exists():
        return {"active_students": 0, "errors": {}, "discrepancies": []}
    return json.loads(path.read_text(encoding="utf-8"))
