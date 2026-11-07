import json
import os

import pytest

os.environ.setdefault("TEACHBACK_LOG_TO_FILE", "0")


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Ogni test usa un database SQLite suo, mai quello della demo."""
    monkeypatch.setenv("TEACHBACK_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("TEACHBACK_LOG_TO_FILE", "0")
    monkeypatch.setenv("TEACHBACK_MODE", "offline")


@pytest.fixture
def offline_engine():
    from teachback import get_engine
    return get_engine("offline")


DEMO = ("Una reazione reversibile arriva all'equilibrio quando la reazione diretta e quella inversa vanno alla stessa "
        "velocità: non si ferma, perché le due reazioni continuano, ma le concentrazioni restano costanti. "
        "Il principio di Le Châtelier dice che se disturbo un equilibrio il sistema si sposta per contrastare il disturbo: "
        "per esempio se aggiungo N2, l'equilibrio si sposta verso NH3 per consumare parte dell'N2 aggiunto. "
        "Anche il catalizzatore sposta l'equilibrio verso i prodotti, per questo si usa per avere più ammoniaca.")


@pytest.fixture
def demo_text():
    return DEMO


class FakeLLM:
    """Sostituisce llm._complete: registra ogni chiamata e restituisce risposte preparate per tipo."""

    def __init__(self):
        self.calls = []
        self.responses = {}   # tipo -> lista di dict (consumate in ordine; l'ultima si ripete)

    @staticmethod
    def kind_of(schema: dict) -> str:
        props = schema.get("properties", {})
        for key, kind in (("claims", "extract"), ("kind", "substudent"), ("concepts", "report"),
                          ("hint_1", "challenge"), ("correct", "grade")):
            if key in props:
                return kind
        raise AssertionError(f"schema sconosciuto: {props}")

    def set(self, kind, *responses):
        self.responses[kind] = list(responses)

    def __call__(self, model, system, user, schema, effort, max_tokens):
        kind = self.kind_of(schema)
        self.calls.append({"kind": kind, "model": model, "system": system, "user": user, "schema": schema})
        queue = self.responses.get(kind)
        if not queue:
            raise AssertionError(f"nessuna risposta preparata per {kind}")
        data = queue.pop(0) if len(queue) > 1 else queue[0]
        return json.dumps(data), {"input_tokens": 10, "output_tokens": 10}


@pytest.fixture
def fake_llm(monkeypatch):
    from teachback import llm
    fake = FakeLLM()
    monkeypatch.setattr(llm, "_complete", fake)
    return fake


@pytest.fixture
def live_engine(fake_llm):
    from teachback import get_engine
    return get_engine("live")
