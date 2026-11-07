"""Dashboard dello studente (mockup: static/Gemini_..._vazz (3).jpg)."""
import streamlit as st

from app import state, ui

eng, s = state.engine(), state.session()
course = eng.load_course(s.course_id)
ui.brand()

reviews = eng.due_reviews(s)
if reviews:
    names = ", ".join(r.name for r in reviews)
    st.markdown(f'<div class="tb-banner"><div class="ico">⚠️</div><div><b>Tempo di ripasso!</b><br>'
                f'Ripasso a intervalli attivo su: {ui.esc(course.title)} — {ui.esc(names)}</div></div>',
                unsafe_allow_html=True)
    st.write("")

h1, h2 = st.columns([4, 1])
h1.markdown("## La tua dashboard")
with h2.popover("Nuovo corso", width="stretch"):
    st.markdown("**Crea un corso non ufficiale** con il tuo materiale. I concetti proposti dall'AI "
                "restano etichettati *non convalidato* finché un docente non li controlla.")
    ui.mock_banner("caricamento materiale non attivo nel prototipo")

ready = sum(1 for v in s.concept_status.values() if v == "pronto")
total = len(course.concepts)
cards = [
    ("🏅", "#dbe8ff", "Ufficiale", "#2f6fdf", course.title, f"{ready}/{total} concetti pronti", ready / total, "#2f6fdf", True),
    ("👥", "#d7f2df", "Creato da uno studente", "#2e9d57", "Fisica Generale", "non convalidato · esempio", 0.45, "#2e9d57", False),
    ("🏅", "#ffe9d6", "Ufficiale", "#2f6fdf", "Analisi Matematica I", "esempio", 0.12, "#f08a24", False),
]
cols = st.columns(3)
for col, (icon, bg, badge, badge_bg, title, sub, pct, bar, active) in zip(cols, cards):
    with col:
        st.markdown(
            f'<div class="tb-course"><div class="top" style="background:{bg}">{icon}'
            f'<span class="tb-pill" style="background:{badge_bg};color:white">{badge}</span></div>'
            f'<div class="body"><div class="title">{ui.esc(title)}</div>'
            f'<div style="display:flex;justify-content:space-between;color:#4b5563">{ui.esc(sub)}</div>'
            f'<div class="tb-bar"><div style="width:{int(pct * 100)}%;background:{bar}"></div></div></div></div>',
            unsafe_allow_html=True)
        if active:
            phase_name = {"spiego": "Inizia il loop →", "domande": "Riprendi: domande →", "prova": "Riprendi: prova d'esame →",
                          "resoconto": "Riprendi: resoconto →", "sfide": "Riprendi: sfide →"}
            label = phase_name.get(s.phase, "Apri il loop →") if s.chat else "Inizia il loop →"
            if st.button(label, key="open_loop", type="primary", width="stretch"):
                st.switch_page("views/loop.py")
        else:
            st.button("Solo esempio", key=f"ex_{title}", disabled=True, width="stretch")

st.write("")
left, right = st.columns([3, 2])
with left:
    with st.container(border=True):
        st.markdown("**Come funziona**")
        st.markdown(
            "1. **Io spiego** l'argomento che temi al 🐣 Sotto-studente, che non sa niente.\n"
            "2. Lui fa domande e **prova una domanda d'esame** usando solo quello che gli hai detto.\n"
            "3. Il 🦉 Insegnante, che conosce le slide, ti dice **dove** hai sbagliato e poi **perché**.\n"
            "4. Le sfide e il ripasso colorano il tuo **grafo di conoscenza**. Nessun voto.")
with right:
    with st.container(border=True):
        st.markdown("**Prossimi ripassi**")
        if reviews:
            for r in reviews:
                st.markdown(f"- {r.name} — {'riapri il loop' if r.action == 'riapri_loop' else 'sfida breve'} (oggi)")
        else:
            st.caption("Nessun ripasso in programma: fai una sessione del loop.")
