"""Ripasso a intervalli: date calcolate davvero dalla memoria SQLite (teachback/memory.py)."""
import math

import streamlit as st

from app import state, ui
from teachback import memory

eng, s = state.engine(), state.session()
course = eng.load_course(s.course_id)

ui.brand()
st.markdown("## Ripasso")
st.caption(f"Sfide brevi sui concetti *quasi*; i concetti *non ancora* riaprono il loop. "
           f"Tetto di {memory.DAILY_CAP} ripassi al giorno per non sommergere chi segue più corsi.")

left, right = st.columns([2, 3], gap="large")
with left:
    with st.container(border=True):
        st.markdown("#### Oggi")
        due = eng.due_reviews(s)
        if not due:
            st.caption("Niente da ripassare oggi. Fai una sessione del loop per riempire il grafo.")
        for r in due:
            fill = ui.STATUS_STYLE[r.status][0]
            st.markdown(f'<div class="tb-box" style="background:{fill}"><b>{ui.esc(r.name)}</b> · '
                        f'{"riapri il loop" if r.action == "riapri_loop" else "sfida breve"}</div>',
                        unsafe_allow_html=True)
        if due and st.button("Inizia il ripasso →", type="primary", key="start_review"):
            st.switch_page("views/loop.py")
    with st.container(border=True):
        st.markdown("#### In programma")
        rows = memory.upcoming(s.student_id, course) if eng.persist else []
        if not rows:
            st.caption("Nessun ripasso programmato.")
        for name, status, d in rows:
            st.markdown(f"- **{name}** · {status.replace('_', ' ')} · {d}")

with right:
    with st.container(border=True):
        st.markdown("#### Perché a intervalli")
        st.caption("Ogni picco è un ripasso: riporta su il ricordo, e la discesa successiva è più lenta.")
        reviews_at, stability, curve = [0, 1, 3, 7, 15], 1.0, []
        for day in [d / 4 for d in range(0, 30 * 4)]:
            last = max(r for r in reviews_at if r <= day)
            k = reviews_at.index(last)
            curve.append(100 * math.exp(-(day - last) / (stability * (2.2 ** k))))
        st.area_chart({"ricordo (%)": curve}, height=230)
        st.caption("Ripassi al giorno 1, 3, 7, 15: con TeachBack l'intervallo si allunga se rispondi bene e si accorcia se sbagli.")
