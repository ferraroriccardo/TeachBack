"""The API used by the React frontend, driven through the demo script (offline engine)."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from server.api import app
    return TestClient(app)


def _start(client):
    r = client.post("/api/sessions", json={"course_id": "chemistry-equilibrium", "mode": "offline", "resume": False})
    assert r.status_code == 200
    return r.json()


def test_dashboard_lists_real_and_example_courses(client):
    data = client.get("/api/courses").json()
    real = [c for c in data["courses"] if not c["example"]]
    assert real and real[0]["id"] == "chemistry-equilibrium"
    assert any(c["example"] for c in data["courses"])


def test_unknown_course_and_session(client):
    assert client.post("/api/sessions", json={"course_id": "nope"}).status_code == 404
    assert client.get("/api/sessions/xxx").status_code == 404


def test_demo_script_end_to_end(client):
    from teachback.demo import DEMO_EXPLANATION, DEMO_FIX
    s = _start(client)
    sid = s["id"]
    assert s["phase"] == "spiego" and s["claims"] == []

    s = client.post(f"/api/sessions/{sid}/explain", json={"text": DEMO_EXPLANATION}).json()
    assert s["phase"] == "domande" and s["claims"] and s["reply"]["kind"] in ("domanda", "rifiuto")

    s = client.post(f"/api/sessions/{sid}/exam", json={}).json()
    assert s["phase"] == "prova" and s["reply"]["cited"]

    s = client.post(f"/api/sessions/{sid}/report").json()
    assert s["phase"] == "resoconto"
    assert s["statuses"]["catalizzatore"] == "non_ancora"
    assert any(c["id"] == "catalizzatore" and c["status"] == "non_ancora" for c in s["changes"])

    s = client.post(f"/api/sessions/{sid}/revise", json={"concept_id": "catalizzatore"}).json()
    assert s["phase"] == "spiego" and s["focus"] == "catalizzatore"
    client.post(f"/api/sessions/{sid}/explain", json={"text": DEMO_FIX})
    client.post(f"/api/sessions/{sid}/exam", json={})
    s = client.post(f"/api/sessions/{sid}/report").json()
    assert s["statuses"]["catalizzatore"] == "pronto"

    s = client.post(f"/api/sessions/{sid}/challenge").json()
    assert s["phase"] == "sfide" and s["challenge"]["question"]
    s = client.post(f"/api/sessions/{sid}/answer", json={}).json()
    assert s["step"]["level"] == "indizio_1"


def test_solutions_never_leave_the_server(client):
    s = _start(client)
    sid = s["id"]
    from teachback.demo import DEMO_EXPLANATION
    client.post(f"/api/sessions/{sid}/explain", json={"text": DEMO_EXPLANATION})
    s = client.post(f"/api/sessions/{sid}/challenge").json()
    raw = client.get(f"/api/sessions/{sid}").text
    from server.api import _sessions
    sol = _sessions[sid].hidden["challenges"][s["challenge"]["id"]]["solution"]
    assert sol not in raw and "hidden" not in raw


def test_empty_explanation_is_rejected(client):
    sid = _start(client)["id"]
    assert client.post(f"/api/sessions/{sid}/explain", json={"text": "  "}).status_code == 400
