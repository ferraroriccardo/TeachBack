"""TeachBack · interfaccia Streamlit.

Avvio dalla radice del repository:
    .venv/Scripts/streamlit run app/streamlit_app.py        (Windows)
    .venv/bin/streamlit run app/streamlit_app.py            (macOS/Linux)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import streamlit as st  # noqa: E402

from app import state, ui  # noqa: E402

st.set_page_config(page_title="TeachBack", page_icon="🎓", layout="wide")
ui.inject_css()

pages = {
    "Studente": [
        st.Page("views/home.py", title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page("views/loop.py", title="Il loop", icon=":material/school:", url_path="loop"),
        st.Page("views/grafo.py", title="Grafo di conoscenza", icon=":material/hub:", url_path="grafo"),
        st.Page("views/ripasso.py", title="Ripasso", icon=":material/event_repeat:", url_path="ripasso"),
        st.Page("views/esame.py", title="Esame interno", icon=":material/quiz:", url_path="esame"),
    ],
    "Docente": [
        st.Page("views/docente.py", title="Messaggio settimanale", icon=":material/mail:", url_path="docente"),
    ],
}
nav = st.navigation(pages)

with st.sidebar:
    st.markdown("**Motore degli agenti**")
    options = ["live", "offline"]
    labels = {"live": "Live · Claude", "offline": "Copione offline (senza AI)"}
    current = state.mode()
    choice = st.radio("Motore", options, index=options.index(current), format_func=labels.get,
                      label_visibility="collapsed", key="mode_radio")
    if choice == "live" and not state.live_available():
        st.warning("Nessuna chiave API: imposta `ANTHROPIC_API_KEY` in `.env`. Uso il copione offline.")
        choice = "offline"
    state.set_mode(choice)
    st.caption("Offline: stesse regole e guardrail, ma agenti a regole su un copione. Utile se la rete cade.")
    if st.button("↺ Nuova sessione", width="stretch", key="reset"):
        state.reset()
        st.rerun()
    with st.expander("🎬 Per chi presenta"):
        st.caption("Riparte dal copione della demo, già portato a questa fase.")
        for target, label in [("prova", "Prova d'esame (l'errore)"), ("resoconto", "Resoconto dell'Insegnante"),
                              ("sfide", "Sfide")]:
            if st.button(label, key=f"jump_{target}", width="stretch"):
                state.jump(target)
                st.switch_page("views/loop.py")
    st.divider()
    st.caption("Studente: demo · Corso: Chimica Generale I")

state.flush_toasts()
nav.run()
