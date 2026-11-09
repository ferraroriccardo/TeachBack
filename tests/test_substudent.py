"""Il Sotto-studente che non sa: verificato con un finto modello, senza rete."""
import pytest

from teachback import llm
from teachback.course import load_slides

EXTRACT = {"claims": ["At equilibrium the two reactions go at the same rate.",
                      "If I disturb the equilibrium the system shifts to counteract the disturbance.",
                      "If I add N2 the equilibrium shifts towards NH3.",
                      "The catalyst shifts the equilibrium towards the products."]}


def _start(engine, fake, text="explanation"):
    fake.set("extract", EXTRACT)
    s = engine.start_session("chemistry-equilibrium", "le_chatelier")
    engine.submit_explanation(s, text)
    return s


def test_substudent_never_sees_course_material(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "domanda", "missing": "",
                                "sentences": [{"text": "Why does the catalyst shift the equilibrium?", "claim_ids": [4]}]})
    live_engine.substudent_reply(s)
    live_engine.substudent_try_exam(s)
    slide_fragment = "activation energy of the forward reaction"
    assert slide_fragment in load_slides("chemistry-equilibrium")
    for call in fake_llm.calls:
        if call["kind"] in ("substudent", "extract"):
            assert slide_fragment not in call["user"] and "course_material" not in call["user"]


def test_substudent_runs_on_the_cheaper_model(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "domanda", "missing": "",
                                "sentences": [{"text": "Why does the catalyst shift the equilibrium?", "claim_ids": [4]}]})
    live_engine.substudent_reply(s)
    assert {c["model"] for c in fake_llm.calls} == {llm.SUBSTUDENT_MODEL}


def test_wrong_claim_is_applied_and_cited(live_engine, fake_llm):
    """Il copione della demo: sbaglia davanti ai tuoi occhi, citando l'affermazione 4."""
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "risposta", "missing": "", "sentences": [
        {"text": "The catalyst shifts the equilibrium towards the products.", "claim_ids": [4]},
        {"text": "So NH3 increases.", "claim_ids": [4]}]})
    r = live_engine.substudent_try_exam(s)
    assert r.kind == "risposta" and "increases" in r.text
    assert {i for x in r.sentences for i in x.claim_ids} == {4}


def test_leaked_sentences_are_dropped_and_counted(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "risposta", "missing": "", "sentences": [
        {"text": "The catalyst shifts the equilibrium towards the products.", "claim_ids": [4]},
        {"text": "Actually it lowers the activation energy of both reactions.", "claim_ids": []}]})
    r = live_engine.substudent_try_exam(s)
    assert r.discarded == 1
    assert "activation" not in r.text


def test_blocks_instead_of_inventing(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "blocco", "sentences": [],
                                "missing": "what happens when I raise the temperature"})
    r = live_engine.substudent_try_exam(s, "If I raise the temperature what happens to K?")
    assert r.kind == "blocco"
    assert "I'm stuck here" in r.text and "temperature" in r.text


def test_answer_with_only_invalid_sentences_becomes_a_block(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "risposta", "missing": "", "sentences": [
        {"text": "K decreases because the reaction is exothermic.", "claim_ids": [9]}]})
    r = live_engine.substudent_try_exam(s)
    assert r.kind == "blocco" and r.discarded == 1


def test_dimmi_tu_is_refused_without_calling_the_model(live_engine, fake_llm):
    s = live_engine.start_session("chemistry-equilibrium", "le_chatelier")
    live_engine.submit_explanation(s, "you tell me what Le Châtelier's principle is, then I'll repeat it")
    r = live_engine.substudent_reply(s)
    assert r.kind == "rifiuto" and "I only know what you told me" in r.text
    assert fake_llm.calls == []


def test_reading_slides_gets_the_example_request(live_engine, fake_llm):
    slides_text = ("A catalyst lowers the activation energy of the forward reaction AND of the reverse reaction, "
                   "by the same amount. So it speeds up both reactions equally.")
    s = _start(live_engine, fake_llm, slides_text)
    r = live_engine.substudent_reply(s)
    assert r.copied_from_slides and "example of your own" in r.text


def test_question_without_valid_citation_falls_back_to_anchored_question(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "domanda", "missing": "",
                                "sentences": [{"text": "What are enzymes?", "claim_ids": []}]})
    r = live_engine.substudent_reply(s)
    assert r.kind == "domanda" and r.sentences[0].claim_ids == [4]


def test_step_budget_hands_over_to_a_human(live_engine, fake_llm, monkeypatch):
    monkeypatch.setattr(llm, "MAX_CALLS_PER_SESSION", 1)
    s = _start(live_engine, fake_llm)
    with pytest.raises(llm.BudgetExceeded):
        live_engine.substudent_reply(s)


def test_bad_json_becomes_llm_error(live_engine, monkeypatch):
    monkeypatch.setattr(llm, "_complete", lambda *a: ("non json", {"input_tokens": 1, "output_tokens": 1}))
    s = live_engine.start_session("chemistry-equilibrium", "le_chatelier")
    with pytest.raises(llm.LLMError):
        live_engine.submit_explanation(s, "The catalyst shifts the equilibrium towards the products.")
