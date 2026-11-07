"""Agenti a regole, senza rete: la demo di riserva e la base dei test.

Non è "intelligente": riconosce parole chiave e usa una banca di sfide scritta a mano
dal materiale della lezione. Ma rispetta lo stesso contratto del backend vero, e
l'orchestratore applica gli stessi guardrail. In UI è etichettato "Copione offline".
"""
from __future__ import annotations

import re

from teachback.contracts import Claim, Concept, Course, Session
from teachback.guardrails import _norm, content_stems

# --- banca delle sfide (dal materiale: slides.md) -----------------------------------

BANK: dict[str, dict] = {
    "equilibrio_dinamico": {
        "question": "All'equilibrio di N2 + 3H2 ⇌ 2NH3 le reazioni si sono fermate? Perché le concentrazioni non cambiano più?",
        "hint_1": "Pensa a cosa succede alle velocità delle due reazioni, diretta e inversa.",
        "hint_2": "Se due flussi opposti sono uguali, cosa vedi dall'esterno?",
        "solution": "No: le due reazioni continuano. All'equilibrio la velocità della reazione diretta è uguale a quella inversa, quindi tanto NH3 si forma quanto se ne decompone e le concentrazioni restano costanti (Slide 3).",
        "keywords": [["veloc"], ["ugual", "stess"]],
        "alt_case": "una bottiglia di acqua frizzante chiusa (CO2 che entra ed esce dalla soluzione)",
    },
    "costante_equilibrio": {
        "question": "Se all'equilibrio aggiungo altro N2, il valore di Kc cambia? Perché?",
        "hint_1": "Da che cosa dipende il valore di Kc?",
        "hint_2": "Rileggi la Slide 7: cosa cambia K e cosa no?",
        "solution": "No: Kc dipende solo dalla temperatura. Aggiungendo N2 cambiano le concentrazioni e il sistema si sposta finché il rapporto torna uguale allo stesso Kc (Slide 6-7).",
        "keywords": [["non camb", "resta", "stesso", "uguale", "no"], ["temperat"]],
        "alt_case": "la reazione H2 + I2 ⇌ 2HI quando aggiungo HI",
    },
    "quoziente_reazione": {
        "question": "Subito dopo aver aggiunto N2 a N2 + 3H2 ⇌ 2NH3 all'equilibrio, Q è maggiore o minore di K? In che verso procede la reazione?",
        "hint_1": "N2 compare al numeratore o al denominatore di Q?",
        "hint_2": "Se il denominatore di una frazione cresce, la frazione cresce o cala?",
        "solution": "Q diventa minore di K perché N2 sta al denominatore; con Q < K la reazione procede verso destra, cioè verso NH3, finché Q torna uguale a K (Slide 8-9).",
        "keywords": [["minor", "q < k", "q<k", "piu piccol"], ["destra", "prodott", "nh3"]],
        "alt_case": "togliere NH3 dal recipiente man mano che si forma",
    },
    "le_chatelier": {
        "question": "Comprimo il recipiente della reazione N2 + 3H2 ⇌ 2NH3: da che parte si sposta l'equilibrio e perché?",
        "hint_1": "Conta le moli di gas a sinistra e a destra della freccia.",
        "hint_2": "Il sistema contrasta l'aumento di pressione: quale lato ha meno molecole di gas?",
        "solution": "Verso NH3: a sinistra ci sono 4 moli di gas, a destra 2. Aumentando la pressione l'equilibrio si sposta verso il lato con meno moli di gas, contrastando in parte l'aumento di pressione (Slide 11).",
        "keywords": [["nh3", "destra", "prodott"], ["mol", "pression"]],
        "alt_case": "la reazione 2NO2 ⇌ N2O4 quando aumento il volume",
    },
    "effetto_temperatura": {
        "question": "La sintesi dell'ammoniaca è esotermica. Se alzo la temperatura, cosa succede a K e alla resa in NH3?",
        "hint_1": "Prova a trattare il calore come se fosse un prodotto della reazione.",
        "hint_2": "Se aggiungi un 'prodotto', da che parte si sposta l'equilibrio?",
        "solution": "K diminuisce e l'equilibrio si sposta verso i reagenti: in una reazione esotermica il calore è come un prodotto, e aggiungerlo sposta l'equilibrio a sinistra. Quindi la resa in NH3 cala (Slide 12).",
        "keywords": [["diminu", "cala", "scende", "minor", "riduc"]],
        "alt_case": "una reazione endotermica, come la decomposizione di CaCO3",
    },
    "catalizzatore": {
        "question": "Nel processo Haber-Bosch si usa un catalizzatore di ferro. Serve ad avere più NH3 all'equilibrio? Perché lo si usa?",
        "hint_1": "Il catalizzatore agisce sulla reazione diretta, su quella inversa o su entrambe?",
        "hint_2": "Se acceleri allo stesso modo due reazioni opposte, il punto di arrivo cambia?",
        "solution": "No: il catalizzatore abbassa allo stesso modo l'energia di attivazione della reazione diretta e di quella inversa, quindi l'equilibrio si raggiunge prima ma la sua posizione e K non cambiano. Si usa per arrivare prima all'equilibrio (Slide 13).",
        "keywords": [["no", "non"], ["prima", "veloc", "tempo", "rapid"]],
        "alt_case": "un catalizzatore aggiunto alla reazione H2 + I2 ⇌ 2HI",
    },
}

_REASON_MARKERS = ("perch", "esempio", "ad es", "quindi", "infatti", "cioe", "per consum",
                   "per contrast", "poiche", "dato che", "visto che", "siccome")


def _mentions(text: str, concept: Concept) -> bool:
    t = _norm(text)
    return any(re.search(r"\b" + re.escape(_norm(a)) + r"\b", t) for a in concept.aliases + [concept.name])


def _catalyst_wrong(text: str) -> bool:
    t = _norm(text)
    return "catalizz" in t and bool(re.search(r"(sposta|aument|piu (nh3|ammoniaca|prodott))", t)) \
        and not re.search(r"non (sposta|cambia|aumenta|modifica)", t)


def _equilibrium_wrong(text: str) -> bool:
    t = _norm(text)
    return bool(re.search(r"(si ferm|si blocc|smett)", t)) and not re.search(r"non (si ferm|si blocc|smett)", t)


_WRONG_RULES = {"catalizzatore": _catalyst_wrong, "equilibrio_dinamico": _equilibrium_wrong}


class OfflineBackend:
    name = "offline"

    # --- Sotto-studente ---------------------------------------------------------------

    def extract_claims(self, text: str, start_n: int, session: Session) -> list[Claim]:
        parts = re.split(r"(?<=[.!?;])\s+|\n+", text.strip())
        parts = [p.strip(" -•") for p in parts if len(p.split()) >= 2]
        parts = [p for p in parts if not re.search(r"(?i)\bdimmi tu\b|\bspiegami tu\b", p)]
        return [Claim(start_n + i, p) for i, p in enumerate(parts[:12])]

    def ask(self, claims: list[Claim], asked_before: list[str], session: Session) -> dict:
        templates = [
            "Hai detto «{q}». Ma perché succede?",
            "Non ho capito bene «{q}»: mi fai un esempio tuo?",
            "Mi hai insegnato «{q}». Cosa succederebbe nel caso opposto?",
        ]
        asked = " ".join(asked_before)
        target = next((c for c in reversed(claims) if f"«{_short(c.text)}»" not in asked), claims[-1])
        text = templates[len(asked_before) % len(templates)].format(q=_short(target.text))
        return {"kind": "domanda", "sentences": [{"text": text, "claim_ids": [target.n]}], "missing": ""}

    def try_exam(self, claims: list[Claim], question: str, session: Session) -> dict:
        qn = _norm(question)
        if "catalizz" in qn:
            cat = [c for c in claims if "catalizz" in _norm(c.text)]
            if not cat:
                return {"kind": "blocco", "sentences": [], "missing": "cosa fa un catalizzatore a una reazione che è già all'equilibrio"}
            c = cat[0]
            if _catalyst_wrong(c.text):
                return {"kind": "risposta", "missing": "", "sentences": [
                    {"text": "Mi hai insegnato che il catalizzatore sposta l'equilibrio verso i prodotti.", "claim_ids": [c.n]},
                    {"text": "Quindi all'equilibrio la quantità di NH3 aumenta, perché NH3 è il prodotto.", "claim_ids": [c.n]}]}
            return {"kind": "risposta", "missing": "", "sentences": [
                {"text": f"Mi hai detto: «{_short(c.text, 14)}».", "claim_ids": [c.n]},
                {"text": "Quindi la quantità di NH3 all'equilibrio non cambia, arriva solo prima.", "claim_ids": [c.n]}]}
        qs = content_stems(question) - {"equil", "reazi"}
        scored = sorted(((len(content_stems(c.text) & qs), c) for c in claims), key=lambda x: -x[0])
        useful = [c for s, c in scored if s >= 2][:2]
        if not useful:
            return {"kind": "blocco", "sentences": [], "missing": "come si collega quello che mi hai spiegato a questa domanda"}
        return {"kind": "risposta", "missing": "", "sentences": [
            {"text": f"Mi hai insegnato che {_lower_first(c.text.rstrip('.'))}.", "claim_ids": [c.n]} for c in useful]}

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
                            "where": f"L'affermazione {n} su «{concept.name}» non torna con la {concept.slide_ref.split(' - ')[0]}: "
                                     "rileggila e chiediti cosa succede alla reazione inversa.",
                            "why": BANK[concept.id]["solution"]})
            elif any(any(m in _norm(c.text) for m in _REASON_MARKERS) for c in related):
                out.append({"id": concept.id, "verdict": "spiegato",
                            "evidence_claims": [c.n for c in related], "where": "", "why": ""})
            elif related:
                n = related[0].n
                out.append({"id": concept.id, "verdict": "nominato", "evidence_claims": [n],
                            "where": f"Nell'affermazione {n} nomini «{concept.name}», ma senza un perché o un esempio.",
                            "why": ""})
            else:
                out.append({"id": concept.id, "verdict": "assente", "evidence_claims": [], "where": "", "why": ""})
        n_ok = sum(1 for c in out if c["verdict"] == "spiegato")
        n_wrong = sum(1 for c in out if c["verdict"] == "errato")
        summary = (f"Hai spiegato bene {n_ok} concetti con un perché o un esempio. "
                   + ("Guarda i punti segnalati: il Sotto-studente ha applicato alla lettera quello che gli hai detto."
                      if n_wrong else "Il Sotto-studente ha usato bene quello che gli hai insegnato."))
        return {"concepts": out, "discrepancies": [], "summary": summary}

    def make_challenge(self, course: Course, slides: str, concept: Concept, kind: str,
                       avoid_case: str, session: Session) -> dict:
        b = BANK[concept.id]
        if kind == "rispiega":
            q = (f"Rispiega al Sotto-studente «{concept.name}» su un caso diverso da prima: "
                 f"{b['alt_case']}. Cosa succede e perché?")
            return {"question": q, "hint_1": b["hint_1"], "hint_2": b["hint_2"], "solution": b["solution"]}
        return {k: b[k] for k in ("question", "hint_1", "hint_2", "solution")}

    def grade(self, slides: str, concept: Concept, question: str, solution: str, answer: str,
              session: Session) -> dict:
        a = _norm(answer)
        ok = all(any(k in a for k in group) for group in BANK[concept.id]["keywords"]) and len(a.split()) >= 4
        return {"correct": ok,
                "feedback": "Giusto, e hai detto anche perché." if ok
                else "Non ci sei ancora: manca l'idea chiave o il perché."}


def _short(text: str, words: int = 10) -> str:
    w = text.rstrip(".").split()
    return " ".join(w[:words]) + ("…" if len(w) > words else "")


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text
