"""Insegnante: resoconto a livelli, soglia, discrepanze, sfide con indizi, regola "spiegalo tu"."""
from dataclasses import fields

from teachback.contracts import Challenge

IDS = ["equilibrio_dinamico", "costante_equilibrio", "quoziente_reazione", "le_chatelier",
       "effetto_temperatura", "catalizzatore"]


def _report(verdicts, discrepancies=()):
    concepts = [{"id": cid, "verdict": verdicts.get(cid, "assente"), "evidence_claims": [1],
                 "where": f"dove su {cid}", "why": f"perché su {cid}"} for cid in IDS]
    return {"concepts": concepts, "discrepancies": list(discrepancies), "summary": "Bravo."}


def _session(engine, fake):
    fake.set("extract", {"claims": ["Il catalizzatore sposta l'equilibrio verso i prodotti."]})
    fake.set("substudent", {"kind": "risposta", "missing": "",
                            "sentences": [{"text": "Il catalizzatore sposta l'equilibrio.", "claim_ids": [1]}]})
    s = engine.start_session("chimica-equilibrio", "le_chatelier")
    engine.submit_explanation(s, "x")
    engine.substudent_try_exam(s)
    return s


def test_report_maps_verdicts_to_concept_states(live_engine, fake_llm):
    s = _session(live_engine, fake_llm)
    fake_llm.set("report", _report({"equilibrio_dinamico": "spiegato", "le_chatelier": "spiegato",
                                    "catalizzatore": "errato", "costante_equilibrio": "nominato"}))
    rep = live_engine.teacher_report(s)
    assert s.concept_status["catalizzatore"] == "non_ancora"
    assert s.concept_status["le_chatelier"] == "pronto"
    assert s.concept_status["costante_equilibrio"] == "quasi"
    assert s.concept_status["effetto_temperatura"] == "non_visto"
    assert not rep.retry
    wrong = next(f for f in rep.feedback if f.concept_id == "catalizzatore")
    assert wrong.slide_ref.startswith("Slide 13")            # la slide la mette il codice, non il modello
    assert wrong.why == "perché su catalizzatore"
    named = next(f for f in rep.feedback if f.concept_id == "costante_equilibrio")
    assert named.why is None                                 # niente spiegazione per chi ha solo nominato


def test_below_one_third_only_says_what_is_missing(live_engine, fake_llm):
    s = _session(live_engine, fake_llm)
    fake_llm.set("report", _report({"le_chatelier": "spiegato", "catalizzatore": "errato"}))
    rep = live_engine.teacher_report(s)
    assert rep.retry and rep.feedback == []
    assert "catalizzatore" in rep.missing


def test_teacher_sees_material_as_data(live_engine, fake_llm):
    s = _session(live_engine, fake_llm)
    fake_llm.set("report", _report({}))
    live_engine.teacher_report(s)
    call = next(c for c in fake_llm.calls if c["kind"] == "report")
    assert "<materiale_del_corso>" in call["user"] and "Slide 13" in call["user"]


def test_discrepancies_are_phrased_as_questions_to_the_lecturer(live_engine, fake_llm):
    s = _session(live_engine, fake_llm)
    fake_llm.set("report", _report({}, [{"source": "Slide 12", "detail": "la slide è sbagliata su ΔH"}]))
    rep = live_engine.teacher_report(s)
    assert rep.discrepancies[0].note.startswith("Discrepanza con Slide 12, chiedi al docente")
    assert "sbagliata" not in rep.discrepancies[0].note


def test_unknown_concept_ids_from_the_model_are_ignored(live_engine, fake_llm):
    s = _session(live_engine, fake_llm)
    data = _report({})
    data["concepts"].append({"id": "inventato", "verdict": "errato", "evidence_claims": [], "where": "", "why": ""})
    fake_llm.set("report", data)
    live_engine.teacher_report(s)
    assert "inventato" not in s.concept_status


def test_challenge_never_carries_the_solution():
    assert "solution" not in {f.name for f in fields(Challenge)}


def test_hint_ladder_then_solution_then_retell(offline_engine):
    e = offline_engine
    s = e.start_session("chimica-equilibrio", "le_chatelier")
    ch = e.next_challenge(s)
    assert ch.kind == "sfida"
    levels = [e.answer_challenge(s, ch.id, None).level for _ in range(3)]
    assert levels == ["indizio_1", "indizio_2", "soluzione"]
    assert s.concept_status[ch.concept_id] == "non_ancora"
    solution_text = s.chat[-1][1]

    other = e.next_challenge(s)                       # prima un'altra domanda…
    assert other.kind == "sfida" and other.concept_id != ch.concept_id
    e.answer_challenge(s, other.id, None)
    retell = e.next_challenge(s)                      # …poi la rispiegazione, su un caso diverso
    assert retell.kind == "rispiega" and retell.concept_id == ch.concept_id
    assert retell.question != ch.question
    assert all(solution_text != text for _, text in s.chat)   # spiegazione coperta: non è nella pagina

    from teachback.agents.offline_backend import BANK
    ok = BANK[ch.concept_id]
    answer = " ".join(group[0] for group in ok["keywords"]) + " perché lo dice la slide e ho capito"
    step = e.answer_challenge(s, retell.id, answer)
    assert step.level == "corretta"
    assert any(solution_text == text for _, text in s.chat)   # finita la rispiegazione torna visibile


def test_skipping_with_avanti_leaves_the_concept_red(offline_engine):
    e = offline_engine
    s = e.start_session("chimica-equilibrio", "le_chatelier")
    ch = e.next_challenge(s)
    e.next_challenge(s)
    assert s.concept_status[ch.concept_id] == "non_ancora"


def test_correct_answer_after_hints_is_only_quasi(offline_engine):
    e = offline_engine
    s = e.start_session("chimica-equilibrio", "le_chatelier")
    ch = e.next_challenge(s)
    e.answer_challenge(s, ch.id, None)
    from teachback.agents.offline_backend import BANK
    answer = " ".join(group[0] for group in BANK[ch.concept_id]["keywords"]) + " perché ho capito il motivo"
    step = e.answer_challenge(s, ch.id, answer)
    assert step.level == "corretta" and step.new_status == "quasi"
