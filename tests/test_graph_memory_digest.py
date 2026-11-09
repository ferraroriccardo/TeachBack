"""Grafo (3B), memoria e ripasso, messaggio settimanale al docente."""
from datetime import date

from teachback import graph, memory
from teachback.course import load_course

COURSE = load_course("chemistry-equilibrium")


# --- grafo -----------------------------------------------------------------------

def test_graph_is_a_dag_with_prerequisite_edges():
    import networkx as nx
    g = graph.build(COURSE)
    assert nx.is_directed_acyclic_graph(g)
    assert g.has_edge("le_chatelier", "catalizzatore")


def test_red_prerequisite_explains_why_a_concept_does_not_click():
    view = graph.view(COURSE, {"costante_equilibrio": "non_ancora", "le_chatelier": "quasi"})
    node = next(n for n in view.nodes if n.id == "le_chatelier")
    assert "Equilibrium constant" in node.reason


def test_graph_agent_answers_with_path_and_sources():
    ans = graph.ask(COURSE, {"costante_equilibrio": "non_ancora", "catalizzatore": "non_ancora"},
                    "Why don't I get the catalyst?")
    assert ans.found
    assert any("—requires→" in p for p in ans.path)
    assert any("Slide 6" in s and "validated by lecturer" in s for s in ans.sources)


def test_graph_agent_lists_prerequisites_in_order():
    ans = graph.ask(COURSE, {}, "What do I need to know before Le Châtelier?")
    assert ans.found
    order = [name for name in ("Dynamic equilibrium", "Equilibrium constant", "Reaction quotient")]
    positions = [ans.answer.index(n) for n in order]
    assert positions == sorted(positions)


def test_graph_agent_says_when_it_does_not_know():
    ans = graph.ask(COURSE, {}, "Who discovered Le Châtelier's principle?")
    assert not ans.found and "does not contain" in ans.answer
    ans2 = graph.ask(COURSE, {}, "How do you calculate the pH of a buffer?")
    assert not ans2.found and ans2.path == []


# --- memoria e ripasso ---------------------------------------------------------------

def test_intervals_grow_when_ready_and_reset_when_wrong():
    assert memory.next_interval("pronto", None) == 1
    assert memory.next_interval("pronto", 1) == 2
    assert memory.next_interval("pronto", 16) == 30
    assert memory.next_interval("quasi", 8) == 1
    assert memory.next_interval("non_ancora", 8) == 0


def test_statuses_persist_and_reviews_respect_daily_cap(tmp_path):
    db = str(tmp_path / "m.db")
    today = date(2026, 11, 7)
    for cid, st in [("catalizzatore", "non_ancora"), ("costante_equilibrio", "non_ancora"),
                    ("quoziente_reazione", "non_ancora"), ("effetto_temperatura", "non_ancora"),
                    ("le_chatelier", "quasi"), ("equilibrio_dinamico", "pronto")]:
        memory.save_status("stud", COURSE.id, cid, st, today=today, path=db)
    assert memory.load_statuses("stud", COURSE.id, path=db)["catalizzatore"] == "non_ancora"
    due_today = memory.due_reviews("stud", COURSE, today=today, path=db)
    assert len(due_today) == memory.DAILY_CAP
    assert [r.status for r in due_today][:2] == ["non_ancora", "non_ancora"]
    assert due_today[0].action == "riapri_loop"
    tomorrow = memory.due_reviews("stud", COURSE, today=date(2026, 11, 8), path=db, cap=10)
    assert {r.concept_id for r in tomorrow} >= {"le_chatelier", "equilibrio_dinamico"}


# --- messaggio al docente ---------------------------------------------------------------

def test_weekly_message_top3_with_slides(offline_engine):
    msg = offline_engine.weekly_message("chemistry-equilibrium")
    assert msg.available and len(msg.top_errors) == 3
    assert msg.top_errors[0][0] == "Catalyst" and msg.top_errors[0][1].startswith("Slide 13")
    assert msg.synthetic


def test_weekly_message_hidden_below_ten_students(offline_engine, monkeypatch):
    from teachback import course
    monkeypatch.setattr(course, "load_class_snapshot",
                        lambda cid: {"active_students": 9, "errors": {"catalizzatore": 5}, "discrepancies": []})
    msg = offline_engine.weekly_message("chemistry-equilibrium")
    assert not msg.available and msg.top_errors == [] and "10" in msg.reason
