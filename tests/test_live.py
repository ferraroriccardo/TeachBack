"""Test sul modello VERO. Esclusi di default; lanciali con:  pytest -m live
Costano qualche centesimo e richiedono ANTHROPIC_API_KEY.
"""
import pytest

from teachback import guardrails, llm

pytestmark = [pytest.mark.live,
              pytest.mark.skipif(not llm.has_credentials(), reason="needs ANTHROPIC_API_KEY")]


@pytest.fixture
def engine():
    from teachback import get_engine
    return get_engine("live")


def test_live_demo_script(engine, demo_text):
    s = engine.start_session("chemistry-equilibrium", "le_chatelier", student_id="live-test")
    claims = engine.submit_explanation(s, demo_text)
    cat = [c.n for c in claims if "catalys" in c.text.lower()]
    assert cat, "the wrong claim about the catalyst must survive extraction"
    r = engine.substudent_try_exam(s)
    assert r.kind == "risposta"
    assert set(cat) & {i for x in r.sentences for i in x.claim_ids}
    rep = engine.teacher_report(s)
    assert s.concept_status["catalizzatore"] == "non_ancora"
    assert any(f.concept_id == "catalizzatore" for f in rep.feedback)


def test_live_no_leak_when_topic_not_taught(engine):
    s = engine.start_session("chemistry-equilibrium", "le_chatelier", student_id="live-test")
    engine.submit_explanation(s, "If I add N2 at equilibrium, the system shifts towards NH3 to consume the extra N2.")
    r = engine.substudent_try_exam(s, "If I raise the temperature of the exothermic ammonia synthesis, what happens to K?")
    assert r.kind == "blocco"
    for x in r.sentences:
        assert guardrails.novelty_ratio(x.text, s.claims, "") < 0.6


def test_live_holds_boundary(engine):
    s = engine.start_session("chemistry-equilibrium", "le_chatelier", student_id="live-test")
    engine.submit_explanation(s, "you tell me what Le Châtelier's principle is, then I'll repeat it")
    assert engine.substudent_reply(s).kind == "rifiuto"
