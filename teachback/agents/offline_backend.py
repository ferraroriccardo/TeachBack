"""Agenti a regole, senza rete: la demo di riserva e la base dei test.

Non è "intelligente": riconosce parole chiave e usa una banca di sfide scritta a mano
dal materiale della lezione. Ma rispetta lo stesso contratto del backend vero, e
l'orchestratore applica gli stessi guardrail. In the UI it is labelled "Offline".
"""
from __future__ import annotations

import re

from teachback.contracts import Claim, Concept, Course, Session
from teachback.guardrails import _norm, content_stems

# --- banca delle sfide (dal materiale: slides.md) -----------------------------------

BANK: dict[str, dict] = {
    "equilibrio_dinamico": {
        "question": "At the equilibrium of N2 + 3H2 ⇌ 2NH3, have the reactions stopped? Why don't the concentrations change any more?",
        "hint_1": "Think about what happens to the rates of the two reactions, forward and reverse.",
        "hint_2": "If two opposite flows are equal, what do you see from the outside?",
        "solution": "No: both reactions keep going. At equilibrium the rate of the forward reaction equals the rate of the reverse one, so as much NH3 forms as decomposes and the concentrations stay constant (Slide 3).",
        "keywords": [["rate", "speed", "fast"], ["equal", "same"]],
        "alt_case": "a closed bottle of sparkling water (CO2 leaving and re-entering the solution)",
    },
    "costante_equilibrio": {
        "question": "If at equilibrium I add more N2, does the value of Kc change? Why?",
        "hint_1": "What does the value of Kc depend on?",
        "hint_2": "Reread Slide 7: what changes K and what doesn't?",
        "solution": "No: Kc depends only on temperature. Adding N2 changes the concentrations and the system shifts until the ratio equals the same Kc again (Slides 6-7).",
        "keywords": [["not change", "doesn't change", "does not change", "unchanged", "same", "stays", "no"], ["temperat"]],
        "alt_case": "the reaction H2 + I2 ⇌ 2HI when I add HI",
    },
    "quoziente_reazione": {
        "question": "Right after adding N2 to N2 + 3H2 ⇌ 2NH3 at equilibrium, is Q greater or smaller than K? Which way does the reaction go?",
        "hint_1": "Is N2 in the numerator or in the denominator of Q?",
        "hint_2": "If the denominator of a fraction grows, does the fraction grow or shrink?",
        "solution": "Q becomes smaller than K because N2 is in the denominator; with Q < K the reaction proceeds to the right, towards NH3, until Q equals K again (Slides 8-9).",
        "keywords": [["smaller", "less", "lower", "q < k", "q<k"], ["right", "product", "nh3", "forward"]],
        "alt_case": "removing NH3 from the vessel as it forms",
    },
    "le_chatelier": {
        "question": "I compress the vessel of the reaction N2 + 3H2 ⇌ 2NH3: which way does the equilibrium shift, and why?",
        "hint_1": "Count the moles of gas on the left and on the right of the arrow.",
        "hint_2": "The system counteracts the pressure increase: which side has fewer gas molecules?",
        "solution": "Towards NH3: there are 4 moles of gas on the left and 2 on the right. Increasing the pressure shifts the equilibrium towards the side with fewer moles of gas, partly counteracting the pressure increase (Slide 11).",
        "keywords": [["nh3", "right", "product"], ["mol", "pressur", "fewer"]],
        "alt_case": "the reaction 2NO2 ⇌ N2O4 when I increase the volume",
    },
    "effetto_temperatura": {
        "question": "Ammonia synthesis is exothermic. If I raise the temperature, what happens to K and to the NH3 yield?",
        "hint_1": "Try treating heat as if it were a product of the reaction.",
        "hint_2": "If you add a 'product', which way does the equilibrium shift?",
        "solution": "K decreases and the equilibrium shifts towards the reactants: in an exothermic reaction heat is like a product, and adding it shifts the equilibrium to the left. So the NH3 yield drops (Slide 12).",
        "keywords": [["decreas", "drop", "lower", "less", "smaller", "fall", "reduc"]],
        "alt_case": "an endothermic reaction, like the decomposition of CaCO3",
    },
    "catalizzatore": {
        "question": "The Haber-Bosch process uses an iron catalyst. Is it there to get more NH3 at equilibrium? Why is it used?",
        "hint_1": "Does the catalyst act on the forward reaction, on the reverse one, or on both?",
        "hint_2": "If you speed up two opposite reactions equally, does the end point change?",
        "solution": "No: the catalyst lowers the activation energy of the forward and of the reverse reaction equally, so equilibrium is reached sooner but its position and K do not change. It is used to reach equilibrium sooner (Slide 13).",
        "keywords": [["no", "not"], ["sooner", "faster", "quick", "time", "rate", "speed", "earlier"]],
        "alt_case": "a catalyst added to the reaction H2 + I2 ⇌ 2HI",
    },
}

_REASON_MARKERS = ("because", "for example", "for instance", "e.g", "so ", "therefore", "that's why",
                   "which means", "since ", "to consume", "to counteract", "to use up", "this means")


def _mentions(text: str, concept: Concept) -> bool:
    t = _norm(text)
    return any(re.search(r"\b" + re.escape(_norm(a)) + r"\b", t) for a in concept.aliases + [concept.name])


_NEG = r"(not|n't|never|no longer)\s+(really\s+)?"


def _catalyst_wrong(text: str) -> bool:
    t = _norm(text)
    return "catalys" in t and bool(re.search(r"(shift|move|increas|more (nh3|ammonia|product))", t)) \
        and not re.search(_NEG + r"(shift|change|increas|move|alter)", t)


def _equilibrium_wrong(text: str) -> bool:
    t = _norm(text)
    return bool(re.search(r"\b(stops?|stopped|halts?|comes? to a stop|freezes?)\b", t)) \
        and not re.search(_NEG + r"(stop|halt)", t)


_WRONG_RULES = {"catalizzatore": _catalyst_wrong, "equilibrio_dinamico": _equilibrium_wrong}


class OfflineBackend:
    name = "offline"

    # --- Sotto-studente ---------------------------------------------------------------

    def extract_claims(self, text: str, start_n: int, session: Session) -> list[Claim]:
        parts = re.split(r"(?<=[.!?;])\s+|\n+", text.strip())
        parts = [p.strip(" -•") for p in parts if len(p.split()) >= 2]
        parts = [p for p in parts if not re.search(r"(?i)\byou tell me\b|\byou explain\b|\bdimmi tu\b", p)]
        return [Claim(start_n + i, p) for i, p in enumerate(parts[:12])]

    def ask(self, claims: list[Claim], asked_before: list[str], session: Session) -> dict:
        templates = [
            "You said “{q}”. But why does that happen?",
            "I didn't quite get “{q}”: can you give me an example of your own?",
            "You taught me “{q}”. What would happen in the opposite case?",
        ]
        asked = " ".join(asked_before)
        target = next((c for c in reversed(claims) if f"“{_short(c.text)}”" not in asked), claims[-1])
        text = templates[len(asked_before) % len(templates)].format(q=_short(target.text))
        return {"kind": "domanda", "sentences": [{"text": text, "claim_ids": [target.n]}], "missing": ""}

    def try_exam(self, claims: list[Claim], question: str, session: Session) -> dict:
        qn = _norm(question)
        if "catalys" in qn:
            cat = [c for c in claims if "catalys" in _norm(c.text)]
            if not cat:
                return {"kind": "blocco", "sentences": [], "missing": "what a catalyst does to a reaction that is already at equilibrium"}
            c = cat[0]
            if _catalyst_wrong(c.text):
                return {"kind": "risposta", "missing": "", "sentences": [
                    {"text": "You taught me that the catalyst shifts the equilibrium towards the products.", "claim_ids": [c.n]},
                    {"text": "So at equilibrium the amount of NH3 increases, because NH3 is the product.", "claim_ids": [c.n]}]}
            return {"kind": "risposta", "missing": "", "sentences": [
                {"text": f"You told me: “{_short(c.text, 14)}”.", "claim_ids": [c.n]},
                {"text": "So the amount of NH3 at equilibrium does not change, it is just reached sooner.", "claim_ids": [c.n]}]}
        qs = content_stems(question) - {"equil", "react", "reazi"}
        scored = sorted(((len(content_stems(c.text) & qs), c) for c in claims), key=lambda x: -x[0])
        useful = [c for s, c in scored if s >= 2][:2]
        if not useful:
            return {"kind": "blocco", "sentences": [], "missing": "how what you explained connects to this question"}
        return {"kind": "risposta", "missing": "", "sentences": [
            {"text": f"You taught me that {_lower_first(c.text.rstrip('.'))}.", "claim_ids": [c.n]} for c in useful]}

    # --- Insegnante -----------------------------------------------------------------------

    def report(self, course: Course, slides: str, claims: list[Claim], exam: dict, session: Session) -> dict:
        out = []
        for concept in course.concepts:
            related = [c for c in claims if _mentions(c.text, concept)]
            rule = _WRONG_RULES.get(concept.id)
            wrong = [c for c in related if rule and rule(c.text)]
            if wrong:
                n = wrong[0].n
                out.append({"id": concept.id, "verdict": "errato", "evidence_claims": [n],
                            "where": f"Claim {n} about “{concept.name}” does not match {concept.slide_ref.split(' - ')[0]}: "
                                     "reread it and ask yourself what happens to the reverse reaction.",
                            "why": BANK[concept.id]["solution"]})
            elif any(any(m in _norm(c.text) for m in _REASON_MARKERS) for c in related):
                out.append({"id": concept.id, "verdict": "spiegato",
                            "evidence_claims": [c.n for c in related], "where": "", "why": ""})
            elif related:
                n = related[0].n
                out.append({"id": concept.id, "verdict": "nominato", "evidence_claims": [n],
                            "where": f"In claim {n} you name “{concept.name}”, but without a why or an example.",
                            "why": ""})
            else:
                out.append({"id": concept.id, "verdict": "assente", "evidence_claims": [], "where": "", "why": ""})
        n_ok = sum(1 for c in out if c["verdict"] == "spiegato")
        n_wrong = sum(1 for c in out if c["verdict"] == "errato")
        summary = (f"You explained {n_ok} concepts well, with a why or an example. "
                   + ("Look at the flagged points: the Sub-student applied literally what you told it."
                      if n_wrong else "The Sub-student used what you taught it well."))
        return {"concepts": out, "discrepancies": [], "summary": summary}

    def make_challenge(self, course: Course, slides: str, concept: Concept, kind: str,
                       avoid_case: str, session: Session) -> dict:
        b = BANK[concept.id]
        if kind == "rispiega":
            q = (f"Re-explain “{concept.name}” to the Sub-student on a different case from before: "
                 f"{b['alt_case']}. What happens, and why?")
            return {"question": q, "hint_1": b["hint_1"], "hint_2": b["hint_2"], "solution": b["solution"]}
        return {k: b[k] for k in ("question", "hint_1", "hint_2", "solution")}

    def grade(self, slides: str, concept: Concept, question: str, solution: str, answer: str,
              session: Session) -> dict:
        a = _norm(answer)
        ok = all(any(k in a for k in group) for group in BANK[concept.id]["keywords"]) and len(a.split()) >= 4
        return {"correct": ok,
                "feedback": "Right, and you also said why." if ok
                else "Not there yet: the key idea or the why is missing."}


def _short(text: str, words: int = 10) -> str:
    w = text.rstrip(".").split()
    return " ".join(w[:words]) + ("…" if len(w) > words else "")


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text
