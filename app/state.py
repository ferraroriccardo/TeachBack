"""Stato dell'interfaccia: motore scelto, sessione, chiamate protette."""
from __future__ import annotations

import streamlit as st

from teachback import default_mode, get_engine, llm
from teachback.contracts import Session

COURSE_ID = "chimica-equilibrio"
TOPIC_ID = "le_chatelier"

DEMO_EXPLANATION = (
    "Una reazione reversibile arriva all'equilibrio quando la reazione diretta e quella inversa vanno "
    "alla stessa velocità: non si ferma, perché le due reazioni continuano, ma le concentrazioni restano costanti. "
    "Il principio di Le Châtelier dice che se disturbo un equilibrio il sistema si sposta per contrastare il disturbo: "
    "per esempio se aggiungo N2 alla sintesi dell'ammoniaca, l'equilibrio si sposta verso NH3 per consumare parte "
    "dell'N2 aggiunto. Anche il catalizzatore sposta l'equilibrio verso i prodotti, per questo nell'industria "
    "si usa per avere più ammoniaca."
)

DEMO_FIX = (
    "Il catalizzatore non sposta l'equilibrio, perché accelera allo stesso modo la reazione diretta e quella "
    "inversa: si arriva prima all'equilibrio, ma la quantità di NH3 è la stessa. Nell'industria si usa per "
    "risparmiare tempo, non per avere più ammoniaca."
)


def mode() -> str:
    if "mode" not in st.session_state:
        st.session_state.mode = default_mode()
    return st.session_state.mode


def engine():
    key = f"engine_{mode()}"
    if key not in st.session_state:
        st.session_state[key] = get_engine(mode())
    return st.session_state[key]


def session() -> Session:
    if "tb_session" not in st.session_state:
        st.session_state.tb_session = engine().start_session(COURSE_ID, TOPIC_ID)
        st.session_state.last_reply = None
        st.session_state.challenge = None
        st.session_state.last_step = None
        target = st.query_params.get("demo")
        if target:
            fast_forward(target)
    return st.session_state.tb_session


def fast_forward(target: str) -> None:
    """?demo=domande|prova|resoconto|sfide: porta la sessione a quella fase con il copione.

    Per provare la demo da un punto preciso (o ripartire se qualcosa va storto davanti ai giudici).
    """
    e, s, ss = engine(), st.session_state.tb_session, st.session_state
    order = ["domande", "prova", "resoconto", "sfide"]
    if target not in order:
        return
    steps = order[: order.index(target) + 1]
    e.submit_explanation(s, DEMO_EXPLANATION)
    ss.last_reply = e.substudent_reply(s)
    if "prova" in steps:
        ss.last_reply = e.substudent_try_exam(s)
    if "resoconto" in steps:
        e.teacher_report(s)
    if "sfide" in steps:
        ss.challenge = e.next_challenge(s)


def reset() -> None:
    for k in ("tb_session", "last_reply", "challenge", "last_step", "graph_answer", "explanation", "toasts"):
        st.session_state.pop(k, None)


def jump(target: str) -> None:
    """Nuova sessione portata subito alla fase `target` (per chi presenta)."""
    reset()
    session()
    fast_forward(target)


_ICON = {"pronto": "🟢", "quasi": "🟡", "non_ancora": "🔴", "non_visto": "⚪"}
_LABEL = {"pronto": "pronto", "quasi": "quasi", "non_ancora": "non ancora", "non_visto": "non visto"}


def act(label: str, fn, *args, **kwargs):
    """Come `run`, ma annuncia i concetti che hanno cambiato stato (notifica alla pagina successiva)."""
    s = session()
    before = dict(s.concept_status)
    out = run(label, fn, *args, **kwargs)
    course = engine().load_course(s.course_id)
    for cid, st_new in s.concept_status.items():
        if before.get(cid) != st_new:
            st.session_state.setdefault("toasts", []).append(
                (f"{course.concept(cid).name} → {_LABEL[st_new]}", _ICON[st_new]))
    return out


def flush_toasts() -> None:
    for text, icon in st.session_state.pop("toasts", []):
        st.toast(text, icon=icon)


def set_mode(new: str) -> None:
    if new != st.session_state.get("mode"):
        st.session_state.mode = new
        reset()


def run(label: str, fn, *args, **kwargs):
    """Esegue una chiamata al motore mostrando uno spinner; gli errori diventano messaggi, non crash."""
    try:
        with st.spinner(label):
            return fn(*args, **kwargs)
    except llm.BudgetExceeded as e:
        st.error(f"🙋 Passo a un umano: {e}")
    except llm.LLMError as e:
        st.error(f"Il modello non risponde ({e}). Puoi continuare con il **copione offline** dalla barra laterale.")
    return None


def live_available() -> bool:
    return llm.has_credentials()
