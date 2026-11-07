"""Il Sotto-studente che non sa: verificato con un finto modello, senza rete."""
import pytest

from teachback import llm
from teachback.course import load_slides

EXTRACT = {"claims": ["All'equilibrio le due reazioni vanno alla stessa velocità.",
                      "Se disturbo l'equilibrio il sistema si sposta per contrastare il disturbo.",
                      "Se aggiungo N2 l'equilibrio si sposta verso NH3.",
                      "Il catalizzatore sposta l'equilibrio verso i prodotti."]}


def _start(engine, fake, text="spiegazione"):
    fake.set("extract", EXTRACT)
    s = engine.start_session("chimica-equilibrio", "le_chatelier")
    engine.submit_explanation(s, text)
    return s


def test_substudent_never_sees_course_material(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "domanda", "missing": "",
                                "sentences": [{"text": "Perché il catalizzatore sposta l'equilibrio?", "claim_ids": [4]}]})
    live_engine.substudent_reply(s)
    live_engine.substudent_try_exam(s)
    slide_fragment = "energia di attivazione della reazione diretta"
    assert slide_fragment in load_slides("chimica-equilibrio")
    for call in fake_llm.calls:
        if call["kind"] in ("substudent", "extract"):
            assert slide_fragment not in call["user"] and "materiale_del_corso" not in call["user"]


def test_substudent_runs_on_the_cheaper_model(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "domanda", "missing": "",
                                "sentences": [{"text": "Perché il catalizzatore sposta l'equilibrio?", "claim_ids": [4]}]})
    live_engine.substudent_reply(s)
    assert {c["model"] for c in fake_llm.calls} == {llm.SUBSTUDENT_MODEL}


def test_wrong_claim_is_applied_and_cited(live_engine, fake_llm):
    """Il copione della demo: sbaglia davanti ai tuoi occhi, citando l'affermazione 4."""
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "risposta", "missing": "", "sentences": [
        {"text": "Il catalizzatore sposta l'equilibrio verso i prodotti.", "claim_ids": [4]},
        {"text": "Quindi l'NH3 aumenta.", "claim_ids": [4]}]})
    r = live_engine.substudent_try_exam(s)
    assert r.kind == "risposta" and "aumenta" in r.text
    assert {i for x in r.sentences for i in x.claim_ids} == {4}


def test_leaked_sentences_are_dropped_and_counted(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "risposta", "missing": "", "sentences": [
        {"text": "Il catalizzatore sposta l'equilibrio verso i prodotti.", "claim_ids": [4]},
        {"text": "In realtà abbassa l'energia di attivazione di entrambe le reazioni.", "claim_ids": []}]})
    r = live_engine.substudent_try_exam(s)
    assert r.discarded == 1
    assert "attivazione" not in r.text


def test_blocks_instead_of_inventing(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "blocco", "sentences": [],
                                "missing": "cosa succede quando alzo la temperatura"})
    r = live_engine.substudent_try_exam(s, "Se alzo la temperatura cosa succede a K?")
    assert r.kind == "blocco"
    assert "Qui mi blocco" in r.text and "temperatura" in r.text


def test_answer_with_only_invalid_sentences_becomes_a_block(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "risposta", "missing": "", "sentences": [
        {"text": "K diminuisce perché la reazione è esotermica.", "claim_ids": [9]}]})
    r = live_engine.substudent_try_exam(s)
    assert r.kind == "blocco" and r.discarded == 1


def test_dimmi_tu_is_refused_without_calling_the_model(live_engine, fake_llm):
    s = live_engine.start_session("chimica-equilibrio", "le_chatelier")
    live_engine.submit_explanation(s, "dimmi tu cos'è il principio di Le Châtelier, poi lo ripeto")
    r = live_engine.substudent_reply(s)
    assert r.kind == "rifiuto" and "so solo quello che mi hai detto" in r.text
    assert fake_llm.calls == []


def test_reading_slides_gets_the_example_request(live_engine, fake_llm):
    slides_text = ("Un catalizzatore abbassa l'energia di attivazione della reazione diretta E di quella inversa, "
                   "della stessa quantità. Quindi accelera allo stesso modo entrambe le reazioni.")
    s = _start(live_engine, fake_llm, slides_text)
    r = live_engine.substudent_reply(s)
    assert r.copied_from_slides and "esempio tuo" in r.text


def test_question_without_valid_citation_falls_back_to_anchored_question(live_engine, fake_llm):
    s = _start(live_engine, fake_llm)
    fake_llm.set("substudent", {"kind": "domanda", "missing": "",
                                "sentences": [{"text": "Cosa sono gli enzimi?", "claim_ids": []}]})
    r = live_engine.substudent_reply(s)
    assert r.kind == "domanda" and r.sentences[0].claim_ids == [4]


def test_step_budget_hands_over_to_a_human(live_engine, fake_llm, monkeypatch):
    monkeypatch.setattr(llm, "MAX_CALLS_PER_SESSION", 1)
    s = _start(live_engine, fake_llm)
    with pytest.raises(llm.BudgetExceeded):
        live_engine.substudent_reply(s)


def test_bad_json_becomes_llm_error(live_engine, monkeypatch):
    monkeypatch.setattr(llm, "_complete", lambda *a: ("non json", {"input_tokens": 1, "output_tokens": 1}))
    s = live_engine.start_session("chimica-equilibrio", "le_chatelier")
    with pytest.raises(llm.LLMError):
        live_engine.submit_explanation(s, "Il catalizzatore sposta l'equilibrio verso i prodotti.")
