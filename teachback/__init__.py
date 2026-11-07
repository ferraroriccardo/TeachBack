"""TeachBack: backend del prototipo.

    from teachback import get_engine
    engine = get_engine("live")     # Claude (serve ANTHROPIC_API_KEY)
    engine = get_engine("offline")  # copione a regole, senza rete

Senza argomento: TEACHBACK_MODE dall'ambiente, altrimenti "live" se ci sono credenziali, sennò "offline".
"""
from __future__ import annotations

import os


def default_mode() -> str:
    from teachback import llm
    env = os.getenv("TEACHBACK_MODE", "").lower()
    if env in ("live", "offline"):
        return env
    return "live" if llm.has_credentials() else "offline"


def get_engine(mode: str | None = None, persist: bool = True):
    from teachback.engine import Engine
    mode = mode or default_mode()
    if mode == "live":
        from teachback.agents.llm_backend import LLMBackend
        return Engine(LLMBackend(), persist=persist)
    from teachback.agents.offline_backend import OfflineBackend
    return Engine(OfflineBackend(), persist=persist)
