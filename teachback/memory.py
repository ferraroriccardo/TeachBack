"""Memoria strutturata (SQLite): stato di ogni concetto per studente e date dei ripassi.

Ripasso a intervalli: un concetto "pronto" torna dopo 1, 2, 4, 8… giorni (tetto 30);
"quasi" torna il giorno dopo; "non ancora" è da riaprire subito nel loop.
Tetto giornaliero di avvisi (default 3) per non sommergere chi segue più corsi.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from teachback.contracts import Course, ReviewItem

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "teachback.db"
DAILY_CAP = 3
MAX_INTERVAL = 30
_PRIORITY = {"non_ancora": 0, "quasi": 1, "pronto": 2}


def _db_path() -> str:
    return os.getenv("TEACHBACK_DB", str(DEFAULT_DB))


def connect(path: str | None = None) -> sqlite3.Connection:
    con = sqlite3.connect(path or _db_path())
    con.execute("""CREATE TABLE IF NOT EXISTS concept_state (
        student TEXT, course TEXT, concept TEXT, status TEXT,
        interval_days INTEGER, due TEXT, attempts INTEGER DEFAULT 0, updated TEXT,
        PRIMARY KEY (student, course, concept))""")
    return con


def next_interval(status: str, previous: int | None) -> int:
    if status == "pronto":
        return min(MAX_INTERVAL, max(1, (previous or 0) * 2) if previous else 1)
    if status == "quasi":
        return 1
    return 0  # non_ancora: subito


def save_status(student: str, course: str, concept: str, status: str,
                today: date | None = None, path: str | None = None) -> tuple[int, str]:
    today = today or date.today()
    with connect(path) as con:
        row = con.execute("SELECT interval_days, attempts FROM concept_state WHERE student=? AND course=? AND concept=?",
                          (student, course, concept)).fetchone()
        prev, attempts = (row if row else (None, 0))
        interval = next_interval(status, prev)
        due = (today + timedelta(days=interval)).isoformat()
        con.execute("INSERT OR REPLACE INTO concept_state VALUES (?,?,?,?,?,?,?,?)",
                    (student, course, concept, status, interval, due, attempts + 1, today.isoformat()))
    return interval, due


def load_statuses(student: str, course: str, path: str | None = None) -> dict[str, str]:
    with connect(path) as con:
        rows = con.execute("SELECT concept, status FROM concept_state WHERE student=? AND course=?",
                           (student, course)).fetchall()
    return dict(rows)


def _rows(student: str, course: str, path: str | None) -> list[tuple[str, str, int, str]]:
    with connect(path) as con:
        return con.execute("SELECT concept, status, interval_days, due FROM concept_state "
                           "WHERE student=? AND course=?", (student, course)).fetchall()


def review_items(course: Course, rows: list[tuple[str, str, int, str]], today: date,
                 cap: int = DAILY_CAP) -> list[ReviewItem]:
    """Funzione pura: dai record ai ripassi di oggi, ordinati per urgenza e tagliati al tetto."""
    due = [r for r in rows if r[1] in _PRIORITY and r[3] <= today.isoformat()]
    due.sort(key=lambda r: (_PRIORITY[r[1]], r[3]))
    items = []
    for cid, status, interval, d in due[:cap]:
        c = course.concept(cid)
        if c:
            items.append(ReviewItem(cid, c.name, status, d, interval,
                                    "riapri_loop" if status == "non_ancora" else "sfida"))
    return items


def due_reviews(student: str, course: Course, today: date | None = None, cap: int = DAILY_CAP,
                path: str | None = None) -> list[ReviewItem]:
    return review_items(course, _rows(student, course.id, path), today or date.today(), cap)


def upcoming(student: str, course: Course, path: str | None = None) -> list[tuple[str, str, str]]:
    """(nome, stato, data) di tutti i ripassi programmati, per la pagina Ripasso."""
    out = []
    for cid, status, _, d in sorted(_rows(student, course.id, path), key=lambda r: r[3]):
        c = course.concept(cid)
        if c:
            out.append((c.name, status, d))
    return out


def reset(student: str, course: str, path: str | None = None) -> None:
    with connect(path) as con:
        con.execute("DELETE FROM concept_state WHERE student=? AND course=?", (student, course))
