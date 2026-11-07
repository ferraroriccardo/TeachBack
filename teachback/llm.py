"""Unico punto di contatto con il modello (Claude, via SDK ufficiale `anthropic`).

- Output sempre in JSON con schema (structured outputs): niente parsing fragile.
- Budget di passi per sessione: oltre il limite l'orchestratore passa la mano a un umano.
- Ogni chiamata è registrata nel log (modello, latenza, token).
- I test sostituiscono `_complete` con un finto modello: nessuna chiamata di rete.
"""
from __future__ import annotations

import json
import os
import time

from teachback import logger
from teachback.contracts import Session

TEACHER_MODEL = os.getenv("TEACHBACK_TEACHER_MODEL", "claude-opus-5-5")
# Il Sotto-studente gira su un modello più economico (vedi "Costi" nella documentazione).
SUBSTUDENT_MODEL = os.getenv("TEACHBACK_SUBSTUDENT_MODEL", "claude-haiku-5-5")
MAX_CALLS_PER_SESSION = int(os.getenv("TEACHBACK_MAX_CALLS", "60"))

_FALLBACK_MODELS = ("claude-opus-5-5", "claude-opus-5", "claude-fable-5-1")


class LLMError(RuntimeError):
    """Il modello non ha risposto in modo utilizzabile (rete, rifiuto, JSON non valido)."""


class BudgetExceeded(RuntimeError):
    """Superato il budget di chiamate della sessione: serve un umano."""


def has_credentials() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(max_retries=2, timeout=90.0)
    return _client


def _complete(model: str, system: str, user: str, schema: dict, effort: str, max_tokens: int) -> tuple[str, dict]:
    """Una chiamata al modello. Restituisce (testo JSON, usage). Sostituita nei test."""
    import anthropic

    kwargs = dict(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    )
    try:
        if model in _FALLBACK_MODELS:
            # Se un classificatore di sicurezza rifiuta, il server ripete la richiesta su un modello di riserva.
            resp = _get_client().beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
        else:
            resp = _get_client().messages.create(**kwargs)
    except anthropic.AuthenticationError as e:
        raise LLMError("Chiave API non valida o mancante (ANTHROPIC_API_KEY).") from e
    except anthropic.RateLimitError as e:
        raise LLMError("Limite di richieste raggiunto: riprova tra poco.") from e
    except anthropic.APIStatusError as e:
        raise LLMError(f"Errore del servizio ({e.status_code}).") from e
    except anthropic.APIConnectionError as e:
        raise LLMError("Rete non raggiungibile.") from e

    if resp.stop_reason == "refusal":
        raise LLMError("Il modello ha rifiutato la richiesta.")
    if resp.stop_reason == "max_tokens":
        raise LLMError("Risposta troncata (max_tokens).")
    text = next((b.text for b in resp.content if b.type == "text"), "")
    usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
    return text, usage


def call_json(
    *, role: str, step: str, system: str, user: str, schema: dict,
    session: Session | None = None, effort: str = "low", max_tokens: int = 8000,
) -> dict:
    """Chiede al modello un oggetto JSON conforme a `schema`. `role`: 'teacher' o 'substudent'."""
    if session is not None:
        if session.llm_calls >= MAX_CALLS_PER_SESSION:
            logger.log(session, "budget_exceeded", calls=session.llm_calls)
            raise BudgetExceeded(
                f"Raggiunto il limite di {MAX_CALLS_PER_SESSION} passi per sessione. "
                "Segnala la domanda al docente o riprendi più tardi.")
        session.llm_calls += 1

    model = TEACHER_MODEL if role == "teacher" else SUBSTUDENT_MODEL
    t0 = time.perf_counter()
    text, usage = _complete(model, system, user, schema, effort, max_tokens)
    latency = round(time.perf_counter() - t0, 2)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.log(session, "llm_bad_json", model=model, step_name=step)
        raise LLMError("Il modello ha restituito JSON non valido.") from e
    logger.log(session, "llm_call", call=step, model=model, latency_s=latency, **usage)
    return data
