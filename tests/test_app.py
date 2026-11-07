"""L'interfaccia, guidata come un utente con streamlit.testing (motore offline)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py")


@pytest.fixture
def at():
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception, app.exception
    return app


def _click(app, key):
    app.button(key=key).click().run()
    assert not app.exception, app.exception


def test_dashboard_renders(at):
    text = " ".join(m.value for m in at.markdown)
    assert "La tua dashboard" in text and "Chimica Generale I" in text


@pytest.mark.parametrize("page", ["views/loop.py", "views/grafo.py", "views/ripasso.py",
                                  "views/esame.py", "views/docente.py"])
def test_every_page_renders(at, page):
    at.switch_page(page).run()
    assert not at.exception, at.exception


def test_full_demo_through_the_ui(at):
    at.switch_page("views/loop.py").run()
    _click(at, "demo_text")
    assert "catalizzatore" in at.text_area(key="explanation").value
    _click(at, "teach")
    s = at.session_state["tb_session"]
    assert s.phase == "domande" and s.claims
    _click(at, "try_exam")
    assert s.phase == "prova" and "aumenta" in s.chat[-1][1]
    _click(at, "ask_report")
    assert s.phase == "resoconto" and s.concept_status["catalizzatore"] == "non_ancora"
    page_text = " ".join(m.value for m in at.markdown)
    assert "Punti critici" in page_text and "Slide 13" in page_text
    _click(at, "to_challenges")
    assert s.phase == "sfide" and at.session_state["challenge"] is not None
    _click(at, "dunno")
    assert at.session_state["last_step"].level == "indizio_1"
    _click(at, "next_ch")

    at.switch_page("views/docente.py").run()
    assert not at.exception
    assert "Catalizzatore" in " ".join(m.value for m in at.markdown)

    at.switch_page("views/grafo.py").run()
    _click(at, "ex_2")
    q, ans = at.session_state["graph_answer"]
    assert not ans.found


def test_fix_the_mistake_from_the_report(at):
    """Errore → resoconto → «Rispiega questo concetto» → correzione → il catalizzatore diventa verde."""
    at.switch_page("views/loop.py").run()
    _click(at, "demo_text")
    _click(at, "teach")
    _click(at, "try_exam")
    _click(at, "ask_report")
    s = at.session_state["tb_session"]
    assert s.concept_status["catalizzatore"] == "non_ancora"
    _click(at, "revise_catalizzatore")
    assert s.phase == "spiego" and not any("catalizzatore sposta" in c.text for c in s.claims)
    _click(at, "demo_fix")
    _click(at, "teach")
    _click(at, "try_exam")
    assert "non cambia" in s.chat[-1][1]
    _click(at, "ask_report")
    assert s.concept_status["catalizzatore"] == "pronto"


def test_presenter_can_jump_to_a_phase(at):
    _click(at, "jump_resoconto")
    assert at.session_state["tb_session"].phase == "resoconto"
