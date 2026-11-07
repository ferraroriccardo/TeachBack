"""Log di ogni passo: in memoria nella sessione e su logs/<studente>.jsonl.

Servono per il debug, per la valutazione (eval/) e per generare docs/EXAMPLES.md.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from teachback.contracts import Session

LOG_DIR = Path(os.getenv("TEACHBACK_LOG_DIR", Path(__file__).resolve().parent.parent / "logs"))


def log(session: Session | None, step: str, **data) -> dict:
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "step": step, **data}
    if session is not None:
        session.log.append(entry)
        if os.getenv("TEACHBACK_LOG_TO_FILE", "1") == "1":
            try:
                LOG_DIR.mkdir(parents=True, exist_ok=True)
                with open(LOG_DIR / f"{session.student_id}.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            except OSError:
                pass  # il log su file non deve mai rompere la demo
    return entry
