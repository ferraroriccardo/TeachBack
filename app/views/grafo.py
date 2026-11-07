"""Grafo di conoscenza e agente che risponde dal grafo (livello 3B)."""
import streamlit as st

from app import state, ui

eng, s = state.engine(), state.session()
course = eng.load_course(s.course_id)
ss = st.session_state

ui.brand()
st.markdown("## Grafo di conoscenza")
st.caption("Concetti collegati dai prerequisiti (A → B: B richiede A), colorati dal tuo stato. "
           "Lo stato non entra mai nel voto.")

left, right = st.columns([3, 2], gap="large")
with left:
    view = eng.get_graph(s)
    with st.container(border=True):
        ui.legend(view)
        ui.graph(view)
    for n in view.nodes:
        if n.reason and n.status != "pronto":
            st.caption(f"↳ {n.reason}")

with right:
    with st.container(border=True):
        st.markdown("#### Chiedi al grafo")
        st.caption("Risponde solo da nodi e archi, mostra il percorso e le fonti, e dice quando non lo sa.")
        examples = ["Perché il catalizzatore non mi torna?",
                    "Cosa devo sapere prima di Le Châtelier?",
                    "Chi ha scoperto il principio di Le Châtelier?"]
        for i, ex in enumerate(examples):
            if st.button(ex, key=f"ex_{i}", width="stretch"):
                ss.graph_answer = (ex, eng.ask_graph(s, ex))
        with st.form("graph_q", clear_on_submit=True, border=False):
            q = st.text_input("Oppure scrivi la tua domanda")
            if st.form_submit_button("Chiedi") and q.strip():
                ss.graph_answer = (q, eng.ask_graph(s, q))

    if ss.get("graph_answer"):
        q, ans = ss.graph_answer
        with st.container(border=True):
            st.markdown(f"**Domanda:** {ui.esc(q)}")
            box = "tb-green" if ans.found else "tb-yellow"
            icon = "✅" if ans.found else "🤷"
            st.markdown(f'<div class="tb-box {box}">{icon} {ui.esc(ans.answer)}</div>', unsafe_allow_html=True)
            if ans.path:
                st.markdown("**Percorso nel grafo**")
                for p in ans.path:
                    st.markdown(f'<div class="tb-path">{ui.esc(p)}</div>', unsafe_allow_html=True)
            if ans.sources:
                st.markdown("**Fonti (con provenienza)**")
                for src in ans.sources:
                    st.caption("• " + src)

with st.expander("Ontologia usata"):
    st.markdown(
        "- **Classi:** `Concept` (6 concetti dell'equilibrio chimico), `Slide` (fonte), `Student`.\n"
        "- **Relazioni:** `Concept requires Concept`, `Concept taughtIn Slide`, `Student hasStatus Concept` "
        "(pronto / quasi / non ancora).\n"
        "- **Provenienza:** ogni concetto registra chi l'ha estratto (AI), chi l'ha convalidato (docente) e quando.\n"
        "- Dettagli e validazione: `docs/ONTOLOGY.md`.")
