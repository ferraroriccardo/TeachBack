"""HTTP API on top of the TeachBack engine, used by the React frontend (web/).

The engine (teachback/) is unchanged: this module keeps sessions in memory and turns
each loop step into a JSON "snapshot" that the UI renders as is.
Challenge solutions and everything else in `Session.hidden` never leave this module.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from teachback import course as course_mod  # noqa: E402
from teachback import default_mode, get_engine, llm, memory  # noqa: E402
from teachback.contracts import Session  # noqa: E402
from teachback.demo import DEMO_EXPLANATION, DEMO_FIX  # noqa: E402

app = FastAPI(title="TeachBack API")

_engines: dict[str, object] = {}
_sessions: dict[str, Session] = {}
_ui: dict[str, dict] = {}            # UI-only state per session (last reply, challenge, …)
_locks: dict[str, threading.Lock] = {}
STUDENT = "demo"

# Example courses shown on the dashboard: labelled as such, cannot be opened.
EXAMPLE_COURSES = [
    {"id": "physics-1", "title": "Physics I", "subtitle": "Dynamics and work",
     "official": False, "example": True, "concepts": 9, "ready": 4},
    {"id": "calculus-1", "title": "Calculus I", "subtitle": "Limits and continuity",
     "official": True, "example": True, "concepts": 11, "ready": 1},
]


def engine(mode: str | None = None):
    mode = mode or default_mode()
    if mode == "live" and not llm.has_credentials():
        mode = "offline"
    if mode not in _engines:
        _engines[mode] = get_engine(mode)
    return _engines[mode]


def _course_ids() -> list[str]:
    return sorted(p.name for p in course_mod.DATA.iterdir() if (p / "concepts.json").exists())


# --- snapshot -------------------------------------------------------------------------

def _snapshot(sid: str, changes: list[dict] | None = None) -> dict:
    s, ui = _sessions[sid], _ui[sid]
    eng = ui["engine"]
    course = eng.load_course(s.course_id)
    view = eng.get_graph(s)
    rep = s.hidden.get("report")
    ch = ui.get("challenge")
    ch_out = None
    if ch is not None:
        data = s.hidden["challenges"][ch.id]
        ch_out = {"id": ch.id, "concept_id": ch.concept_id, "question": ch.question, "kind": ch.kind,
                  "hints_used": data["hints_used"], "closed": data["closed"]}
    reply = ui.get("reply")
    return {
        "id": sid,
        "mode": eng.mode,
        "live_available": llm.has_credentials(),
        "phase": s.phase,
        "focus": s.hidden.get("focus"),
        "course": {"id": course.id, "title": course.title, "official": course.official,
                   "exam_questions": course.exam_questions,
                   "concepts": [{"id": c.id, "name": c.name, "slide_ref": c.slide_ref} for c in course.concepts]},
        "claims": [asdict(c) for c in s.claims],
        "chat": [{"role": r, "text": t} for r, t in s.chat],
        "statuses": dict(s.concept_status),
        "graph": asdict(view),
        "reply": None if reply is None else {
            "kind": reply.kind, "text": reply.text, "discarded": reply.discarded,
            "copied": reply.copied_from_slides,
            "cited": sorted({i for x in reply.sentences for i in x.claim_ids})},
        "report": None if rep is None else asdict(rep),
        "challenge": ch_out,
        "step": None if ui.get("step") is None else asdict(ui["step"]),
        "changes": changes or [],
        "llm_calls": s.llm_calls,
    }


def _get(sid: str) -> Session:
    if sid not in _sessions:
        raise HTTPException(404, "Session not found: start again from the dashboard.")
    return _sessions[sid]


def _act(sid: str, fn):
    """Runs an engine step, records the concepts whose status changed, translates errors."""
    s = _get(sid)
    with _locks[sid]:
        before = dict(s.concept_status)
        try:
            fn(s, _ui[sid])
        except llm.BudgetExceeded as e:
            raise HTTPException(429, f"Handing over to a human: {e}")
        except llm.LLMError as e:
            raise HTTPException(503, f"The model is not responding ({e}). You can continue in offline mode.")
        course = _ui[sid]["engine"].load_course(s.course_id)
        changes = [{"id": cid, "name": course.concept(cid).name, "status": st}
                   for cid, st in s.concept_status.items() if before.get(cid) != st]
        return _snapshot(sid, changes)


# --- courses and sessions ------------------------------------------------------------------

@app.get("/api/courses")
def courses():
    eng = engine()
    out = []
    for cid in _course_ids():
        c = eng.load_course(cid)
        st = memory.load_statuses(STUDENT, cid)
        out.append({
            "id": c.id, "title": c.title, "subtitle": "Le Châtelier's principle", "official": c.official,
            "example": False, "concepts": len(c.concepts),
            "ready": sum(1 for v in st.values() if v == "pronto"),
            "statuses": {k.id: st.get(k.id, "non_visto") for k in c.concepts},
            "names": {k.id: k.name for k in c.concepts},
            "reviews": [asdict(r) for r in memory.due_reviews(STUDENT, c)],
        })
    return {"mode": eng.mode, "live_available": llm.has_credentials(),
            "courses": out + EXAMPLE_COURSES}


class StartBody(BaseModel):
    course_id: str
    mode: str | None = None
    resume: bool = True


@app.post("/api/sessions")
def start(body: StartBody):
    if body.course_id not in _course_ids():
        raise HTTPException(404, "Course not found.")
    eng = engine(body.mode)
    s = eng.start_session(body.course_id, "le_chatelier", STUDENT, resume=body.resume)
    sid = uuid.uuid4().hex[:12]
    _sessions[sid], _locks[sid] = s, threading.Lock()
    _ui[sid] = {"engine": eng, "reply": None, "challenge": None, "step": None}
    return _snapshot(sid)


@app.get("/api/sessions/{sid}")
def get_session(sid: str):
    _get(sid)
    return _snapshot(sid)


class Text(BaseModel):
    text: str | None = None


@app.post("/api/sessions/{sid}/explain")
def explain(sid: str, body: Text):
    if not (body.text or "").strip():
        raise HTTPException(400, "Write an explanation first.")

    def step(s, ui):
        e = ui["engine"]
        e.submit_explanation(s, body.text)
        ui["reply"] = e.substudent_reply(s)
    return _act(sid, step)


@app.post("/api/sessions/{sid}/reply")
def reply(sid: str, body: Text):
    if not (body.text or "").strip():
        raise HTTPException(400, "Write an answer.")

    def step(s, ui):
        s.phase = "domande"
        ui["reply"] = ui["engine"].substudent_reply(s, body.text)
    return _act(sid, step)


@app.post("/api/sessions/{sid}/exam")
def exam(sid: str, body: Text):
    def step(s, ui):
        ui["reply"] = ui["engine"].substudent_try_exam(s, body.text or None)
    return _act(sid, step)


@app.post("/api/sessions/{sid}/report")
def report(sid: str):
    return _act(sid, lambda s, ui: ui["engine"].teacher_report(s))


class ConceptBody(BaseModel):
    concept_id: str


@app.post("/api/sessions/{sid}/revise")
def revise(sid: str, body: ConceptBody):
    def step(s, ui):
        ui["engine"].revise_concept(s, body.concept_id)
        ui["reply"] = None
    return _act(sid, step)


@app.post("/api/sessions/{sid}/explain-again")
def explain_again(sid: str):
    def step(s, ui):
        s.phase = "spiego"
    return _act(sid, step)


@app.post("/api/sessions/{sid}/challenge")
def challenge(sid: str):
    def step(s, ui):
        ui["challenge"] = ui["engine"].next_challenge(s)
        ui["step"] = None
    return _act(sid, step)


@app.post("/api/sessions/{sid}/answer")
def answer(sid: str, body: Text):
    def step(s, ui):
        ch = ui.get("challenge")
        if ch is None:
            raise HTTPException(400, "No open challenge.")
        ui["step"] = ui["engine"].answer_challenge(s, ch.id, body.text or None)
    return _act(sid, step)


@app.get("/api/demo")
def demo():
    return {"explanation": DEMO_EXPLANATION, "fix": DEMO_FIX}


# --- presentation and built frontend ----------------------------------------------------

PRESENTATION = Path(__file__).resolve().parent.parent / "presentation"
if PRESENTATION.exists():
    app.mount("/presentation", StaticFiles(directory=PRESENTATION, html=True), name="presentation")

DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
