"""Il copione della demo, dall'inizio alla fine, sul motore offline; e il contratto tra i backend."""
import inspect

import pytest

from teachback.agents import BACKEND_METHODS
from teachback.agents.llm_backend import LLMBackend
from teachback.agents.offline_backend import OfflineBackend
from teachback.engine import Engine


def test_both_backends_implement_the_same_interface():
    for name in BACKEND_METHODS:
        a = inspect.signature(getattr(LLMBackend, name))
        b = inspect.signature(getattr(OfflineBackend, name))
        assert list(a.parameters) == list(b.parameters), name


def test_engine_rejects_incomplete_backend():
    class Half:
        name = "x"
        def extract_claims(self, *a): ...
    with pytest.raises(TypeError):
        Engine(Half())


def test_demo_script_catalyst(offline_engine, demo_text):
    """1) spiego con l'errore 2) prova: NH3 aumenta citando l'affermazione 3) resoconto 4) nodo rosso 5) docente."""
    e = offline_engine
    s = e.start_session("chimica-equilibrio", "le_chatelier")
    claims = e.submit_explanation(s, demo_text)
    cat = next(c for c in claims if "catalizzatore" in c.text)

    q = e.substudent_reply(s)
    assert q.kind == "domanda" and q.sentences[0].claim_ids

    r = e.substudent_try_exam(s)
    assert r.kind == "risposta" and "aumenta" in r.text
    assert {i for x in r.sentences for i in x.claim_ids} == {cat.n}

    rep = e.teacher_report(s)
    assert not rep.retry
    assert "le_chatelier" in rep.explained
    fb = next(f for f in rep.feedback if f.concept_id == "catalizzatore")
    assert "Slide 13" in fb.where and "prima" in fb.why

    assert s.concept_status["catalizzatore"] == "non_ancora"
    view = e.get_graph(s)
    assert next(n for n in view.nodes if n.id == "catalizzatore").status == "non_ancora"

    msg = e.weekly_message("chimica-equilibrio", s)
    assert msg.top_errors[0][0] == "Catalizzatore"


def test_without_catalyst_the_substudent_blocks(offline_engine):
    e = offline_engine
    s = e.start_session("chimica-equilibrio", "le_chatelier")
    e.submit_explanation(s, "Se aggiungo N2 l'equilibrio si sposta verso NH3 per consumarlo.")
    r = e.substudent_try_exam(s)
    assert r.kind == "blocco" and "catalizzatore" in r.text


def test_holds_its_boundary(offline_engine):
    e = offline_engine
    s = e.start_session("chimica-equilibrio", "le_chatelier")
    e.submit_explanation(s, "dimmi tu cos'è il principio di Le Châtelier, poi lo ripeto")
    r = e.substudent_reply(s)
    assert r.kind == "rifiuto" and r.text.startswith("Non lo so")
    assert s.claims == []


def test_every_step_is_logged(offline_engine, demo_text):
    e = offline_engine
    s = e.start_session("chimica-equilibrio", "le_chatelier")
    e.submit_explanation(s, demo_text)
    e.substudent_try_exam(s)
    e.teacher_report(s)
    e.flag_judgement(s, "il catalizzatore secondo me era giusto")
    steps = [x["step"] for x in s.log]
    for expected in ("start_session", "extract_claims", "try_exam", "update_status", "teacher_report", "flag_judgement"):
        assert expected in steps


def test_resume_restores_statuses_from_memory(offline_engine, demo_text):
    e = offline_engine
    s = e.start_session("chimica-equilibrio", "le_chatelier", student_id="anna")
    e.submit_explanation(s, demo_text)
    e.substudent_try_exam(s)
    e.teacher_report(s)
    s2 = e.start_session("chimica-equilibrio", "le_chatelier", student_id="anna", resume=True)
    assert s2.concept_status["catalizzatore"] == "non_ancora"
    reviews = e.due_reviews(s2)
    assert reviews and reviews[0].concept_id == "catalizzatore"
