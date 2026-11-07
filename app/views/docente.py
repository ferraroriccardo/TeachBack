"""Messaggio settimanale al docente (mockup: static/Gemini_..._vazz.jpg)."""
import streamlit as st

from app import state, ui

eng, s = state.engine(), state.session()
course = eng.load_course(s.course_id)
msg = eng.weekly_message(s.course_id, s)

h1, h2 = st.columns([3, 2])
with h1:
    ui.brand()
with h2:
    st.markdown('<div style="text-align:right;margin-top:.4rem"><span class="tb-privacy">🔒 Dati anonimi e aggregati · '
                'visibili solo al docente</span></div>', unsafe_allow_html=True)

st.caption("Corso")
st.markdown(f"## {course.title}")
if msg.synthetic:
    ui.mock_banner("dati della classe SINTETICI per la demo, più la tua sessione. Il calcolo e le soglie sono reali.")

if not msg.available:
    st.warning(msg.reason)
    st.stop()

left, right = st.columns([3, 2], gap="large")
with left:
    with st.container(border=True):
        st.markdown(f"#### I 3 concetti più sbagliati questa settimana · {msg.active_students} studenti attivi")
        for name, slide, n in msg.top_errors:
            share = n / msg.active_students
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:.6rem">'
                f'<b>{ui.esc(name)}</b><span><span style="color:#6b7280;margin-right:.5rem">{n} studenti</span>'
                f'<span class="tb-pill" style="background:#fde2e2;color:#b42318">Lacuna</span></span></div>'
                f'<div class="tb-bar"><div style="width:{int(share * 100)}%;background:#e05252"></div></div>'
                f'<div style="color:#6b7280;font-size:.85rem;margin-top:.2rem">Slide collegata: {ui.esc(slide)}</div>',
                unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Attività di studio (sessioni per settimana)")
        st.line_chart({"sessioni": [12, 18, 15, 26, 31, 44, 38, 52]}, height=180)
        st.caption(msg.disclaimer)

with right:
    with st.container(border=True):
        st.markdown("#### Discrepanze trovate nel materiale")
        if not msg.discrepancies:
            st.caption("Nessuna discrepanza questa settimana.")
        for i, d in enumerate(msg.discrepancies):
            st.markdown(f'<div class="tb-box tb-red">{ui.esc(d.note)}</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("Correggi la slide", key=f"fix_{i}", type="primary", width="stretch"):
                st.toast("Segnata come da correggere. L'AI non modifica le slide: lo fa il docente.")
            if c2.button("Ignora", key=f"ign_{i}", width="stretch"):
                st.toast("Ignorata.")
    with st.container(border=True):
        st.markdown("#### Regole di questo messaggio")
        st.markdown("- Solo corsi ufficiali, con almeno **10 studenti attivi**.\n"
                    "- Lo vede **solo il docente**: non serve a valutarlo.\n"
                    "- Le discrepanze sono scritte come *“Discrepanza con [fonte], chiedi al docente”*.")
