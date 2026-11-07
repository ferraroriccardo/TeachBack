"""Esame interno: MOCKUP statico dichiarato (nel prototipo non è implementato)."""
import streamlit as st

from app import state, ui

eng, s = state.engine(), state.session()
course = eng.load_course(s.course_id)

ui.brand()
st.markdown("## Esame interno")
ui.mock_banner("schermata dimostrativa, non collegata agli agenti. In roadmap.")
st.write("")
st.markdown("Domande sempre nuove, nello stile delle domande di teoria, **concentrate sui tuoi concetti deboli**. "
            "Le soluzioni si vedono solo dopo il tentativo. Esito per concetto: *pronto*, *quasi*, *non ancora*. "
            "**Nessun voto.**")

weak = [c for c in course.concepts if s.concept_status.get(c.id) in ("non_ancora", "quasi")] or course.concepts[:3]
questions = {
    "catalizzatore": "Un compagno dice: «con il catalizzatore giusto si ottiene più NH3». Ha ragione? Spiega perché.",
    "costante_equilibrio": "Raddoppio il volume del recipiente di N2 + 3H2 ⇌ 2NH3. Kc cambia? Perché?",
    "quoziente_reazione": "Tolgo NH3 man mano che si forma. Come cambia Q rispetto a K e cosa fa la reazione?",
    "effetto_temperatura": "Perché nel processo Haber-Bosch non si lavora alla temperatura più alta possibile?",
    "le_chatelier": "Aggiungo argon a volume costante all'equilibrio di N2 + 3H2 ⇌ 2NH3. Si sposta? Perché?",
    "equilibrio_dinamico": "Come dimostreresti che all'equilibrio la reazione non si è fermata?",
}
for i, c in enumerate(weak[:3], 1):
    with st.container(border=True):
        st.markdown(f"**Domanda {i}** · {c.name}")
        st.write(questions.get(c.id, ""))
        st.text_area("Risposta", key=f"exam_{c.id}", disabled=True, height=70, label_visibility="collapsed",
                     placeholder="(mockup) la risposta verrebbe corretta dall'Insegnante")
        st.button("Mostra soluzione", key=f"sol_{c.id}", disabled=True, help="Visibile solo dopo il tentativo.")

st.markdown("#### Esito (esempio)")
cols = st.columns(3)
for col, (label, color) in zip(cols, [("Pronto", "#8fd694"), ("Quasi", "#ffe08a"), ("Non ancora", "#f59a9a")]):
    col.markdown(f'<div class="tb-box" style="background:{color};text-align:center;font-weight:700">{label}</div>',
                 unsafe_allow_html=True)
