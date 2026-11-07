"""I due agenti (Sotto-studente e Insegnante) in due implementazioni con la stessa interfaccia.

- `LLMBackend`: Claude via API, con i prompt di prompts/.
- `OfflineBackend`: regole e copione, senza rete. Serve per la demo di riserva e per i test.

Restituiscono dati GREZZI (dict). Guardrail, stati dei concetti e soglie li applica sempre
l'orchestratore (teachback/engine.py), quindi valgono identici nei due casi.
"""

BACKEND_METHODS = ("extract_claims", "ask", "try_exam", "report", "make_challenge", "grade")


def claims_block(claims) -> str:
    if not claims:
        return "AFFERMAZIONI DELLO STUDENTE: (nessuna)"
    return "AFFERMAZIONI DELLO STUDENTE:\n" + "\n".join(f"{c.n}. {c.text}" for c in claims)
