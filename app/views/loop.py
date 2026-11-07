"""Il loop (mockup: static/Gemini_..._vazz (2).jpg per chat + grafo, (1).jpg per il resoconto)."""
import streamlit as st

from app import state, ui

eng, s = state.engine(), state.session()
course = eng.load_course(s.course_id)
ss = st.session_state

head_l, head_r = st.columns([3, 2])
with head_l:
    ui.brand()
with head_r:
    st.markdown(f'<div style="text-align:right;margin-top:.5rem">{ui.mode_badge(eng.mode)}</div>', unsafe_allow_html=True)
st.caption(f"{course.title} · Argomento: principio di Le Châtelier")
ui.stepper(s.phase)

left, right = st.columns([11, 9], gap="large")


# --------------------------------------------------------------------- colonna destra
with right:
    view = eng.get_graph(s)
    with st.container(border=True):
        st.markdown("#### Grafo di conoscenza")
        ui.legend(view)
        ui.graph(view)
        for n in view.nodes:
            if n.reason and n.status != "pronto":
                st.caption(f"↳ {n.reason}")
    with st.container(border=True):
        st.markdown("#### 🧠 Cosa sa il Sotto-studente")
        st.caption("Solo queste affermazioni, estratte dalla tua spiegazione. In rosso quelle citate nell'ultima risposta.")
        ui.claims_panel(s.claims, ss.get("last_reply"))


# --------------------------------------------------------------------- colonna sinistra
def report_view() -> None:
    rep = s.hidden.get("report")
    if rep is None:
        return
    st.markdown(f'<div class="tb-owl"><div class="ava">🦉</div><div><b>Insegnante AI · Resoconto</b><br>'
                f'{ui.esc(rep.summary or "Ecco cosa hai spiegato bene e cosa rivedere.")}</div></div>',
                unsafe_allow_html=True)
    if rep.retry:
        names = ", ".join(course.concept(c).name for c in rep.missing)
        st.markdown(f'<div class="tb-box tb-yellow" style="margin-top:.8rem"><h4>Riprova</h4>'
                    f'Hai spiegato con un perché o un esempio meno di un terzo dei concetti chiave. '
                    f'Mancano: {ui.esc(names)}.</div>', unsafe_allow_html=True)
        return
    wrong = [f for f in rep.feedback if s.concept_status.get(f.concept_id) == "non_ancora"]
    unclear = [f for f in rep.feedback if f not in wrong]
    if wrong:
        st.markdown('<div class="tb-sec">Punti critici ed errori (lacuna)</div>', unsafe_allow_html=True)
        for f in wrong:
            st.markdown(f'<div class="tb-box tb-red"><h4>⚠️ {ui.esc(course.concept(f.concept_id).name)}</h4>'
                        f'{ui.esc(f.where)}<br><b>Cosa rivedere:</b> {ui.esc(f.slide_ref)}</div>', unsafe_allow_html=True)
            if f.why:
                with st.expander("Perché? (secondo livello di aiuto)"):
                    st.write(f.why)
    if unclear:
        st.markdown('<div class="tb-sec">Da chiarire (da rivedere)</div>', unsafe_allow_html=True)
        for f in unclear:
            st.markdown(f'<div class="tb-box tb-yellow"><h4>❕ {ui.esc(course.concept(f.concept_id).name)}</h4>'
                        f'{ui.esc(f.where)}<br><b>Cosa rivedere:</b> {ui.esc(f.slide_ref)}</div>', unsafe_allow_html=True)
    if rep.explained:
        st.markdown('<div class="tb-sec">Spiegati bene</div>', unsafe_allow_html=True)
        st.markdown('<div class="tb-box tb-green">' + ", ".join(ui.esc(course.concept(c).name) for c in rep.explained)
                    + '</div>', unsafe_allow_html=True)
    if rep.discrepancies:
        st.markdown('<div class="tb-sec">⚠️ Segnalazione nei materiali</div>', unsafe_allow_html=True)
        for i, d in enumerate(rep.discrepancies):
            st.markdown(f'<div class="tb-box tb-yellow">{ui.esc(d.note)}</div>', unsafe_allow_html=True)
            if st.button("Segnala al docente (anonimo)", key=f"disc_{i}"):
                st.toast("Segnalazione inviata in forma anonima al messaggio settimanale del docente.")


with left:
    with st.container(border=True):
        ui.card_head("🐣" if s.phase in ("spiego", "domande", "prova") else "🦉",
                     "Sotto-studente AI" if s.phase in ("spiego", "domande", "prova") else "Insegnante AI")
        if s.phase == "resoconto":
            report_view()
        elif s.phase == "sfide" and ss.get("challenge") is not None:
            ch = ss.challenge
            label = "🔁 Rispiega al Sotto-studente" if ch.kind == "rispiega" else "🎯 Sfida"
            name = course.concept(ch.concept_id).name
            st.markdown(f'<div class="tb-owl"><div class="ava">🦉</div><div><b>{label} · {ui.esc(name)}</b><br>'
                        f'{ui.esc(ch.question)}</div></div>', unsafe_allow_html=True)
            step = ss.get("last_step")
            if step is not None:
                box = {"corretta": "tb-green", "soluzione": "tb-red"}.get(step.level, "tb-yellow")
                title = {"corretta": "✅ Corretta", "indizio_1": "💡 Primo indizio", "indizio_2": "💡 Secondo indizio",
                         "soluzione": "📖 Soluzione (dopo due indizi)"}.get(step.level, "")
                st.markdown(f'<div class="tb-box {box}" style="margin-top:.7rem"><h4>{title}</h4>{ui.esc(step.text)}</div>',
                            unsafe_allow_html=True)
                if step.level == "soluzione":
                    st.caption("Più avanti, dopo un'altra domanda, ti chiederò di rispiegarlo su un caso diverso.")
            with st.expander("Conversazione completa"):
                ui.chat(s.chat)
        else:
            ui.chat(s.chat, recent=6)

    # ---- comandi della fase corrente
    if s.phase == "spiego":
        if "explanation" not in ss:
            ss.explanation = ""
        st.text_area("Spiega l'argomento al Sotto-studente, con parole tue", key="explanation", height=150,
                     placeholder="Scrivi qui la tua spiegazione…")
        c1, c2, c3 = st.columns([2, 2, 1])
        if c1.button("Insegna al Sotto-studente ➤", type="primary", width="stretch", key="teach"):
            if ss.explanation.strip():
                if state.run("Il Sotto-studente ascolta…", eng.submit_explanation, s, ss.explanation) is not None:
                    ss.last_reply = state.run("Il Sotto-studente pensa a cosa non ha capito…", eng.substudent_reply, s)
                st.rerun()
            else:
                st.warning("Scrivi prima una spiegazione.")
        c2.button("📋 Spiegazione della demo", width="stretch", key="demo_text",
                  help="Riempie il campo con la spiegazione del copione (contiene l'errore sul catalizzatore).",
                  on_click=lambda: ss.update(explanation=state.DEMO_EXPLANATION))
        c3.button("🎙️", disabled=True, width="stretch", key="mic", help="Voce: in roadmap (default testo).")

    elif s.phase == "domande":
        with st.form("reply_form", clear_on_submit=True, border=False):
            msg = st.text_input("Rispondi al Sotto-studente", placeholder="Rispondi o aggiungi un esempio tuo…")
            sent = st.form_submit_button("Invia ➤")
        if sent and msg.strip():
            ss.last_reply = state.run("Il Sotto-studente ascolta…", eng.substudent_reply, s, msg)
            st.rerun()
        q = st.selectbox("Domanda d'esame da far provare", course.exam_questions, key="exam_q")
        c1, c2 = st.columns([3, 2])
        if c1.button("Fagli provare la domanda d'esame →", type="primary", width="stretch", key="try_exam"):
            ss.last_reply = state.run("Il Sotto-studente prova a rispondere…", eng.substudent_try_exam, s, q)
            st.rerun()
        if c2.button("Spiega ancora", width="stretch", key="back_explain"):
            s.phase = "spiego"
            st.rerun()

    elif s.phase == "prova":
        c1, c2 = st.columns([3, 2])
        if c1.button("Chiedi il resoconto all'Insegnante →", type="primary", width="stretch", key="ask_report"):
            state.run("L'Insegnante confronta la tua spiegazione con le slide…", eng.teacher_report, s)
            st.rerun()
        if c2.button("Prova un'altra domanda", width="stretch", key="other_q"):
            s.phase = "domande"
            st.rerun()

    elif s.phase == "resoconto":
        rep = s.hidden.get("report")
        c1, c2, c3 = st.columns([2, 2, 3])
        if c1.button("← Dashboard", width="stretch", key="to_home"):
            st.switch_page("views/home.py")
        with c2.popover("⚑ Contesta", width="stretch", help="Il giudizio ti sembra sbagliato? Segnalalo."):
            note = st.text_area("Cosa non ti torna del giudizio?", key="flag_note")
            if st.button("Registra la segnalazione", key="flag_send"):
                eng.flag_judgement(s, note)
                st.success("Registrata: serve a misurare l'accordo con il giudice. Nessuno la legge in tempo reale.")
        if rep is not None and rep.retry:
            if c3.button("Riprova a spiegare →", type="primary", width="stretch", key="retry"):
                s.phase = "spiego"
                st.rerun()
        elif c3.button("Procedi: sfide dell'Insegnante →", type="primary", width="stretch", key="to_challenges"):
            ss.challenge = state.run("L'Insegnante prepara una sfida…", eng.next_challenge, s)
            ss.last_step = None
            st.rerun()

    elif s.phase == "sfide":
        ch = ss.get("challenge")
        if ch is not None:
            if ch.kind == "rispiega":
                st.info("🔁 **Regola “spiegalo tu”**: rispiega su un caso diverso. "
                        "La spiegazione di prima è coperta e non è più nella pagina.")
            closed = s.hidden["challenges"][ch.id]["closed"]
            if not closed:
                with st.form("answer_form", clear_on_submit=True, border=False):
                    ans = st.text_area("La tua risposta", height=90, placeholder="Rispondi con un perché…")
                    sent = st.form_submit_button("Invia risposta ➤", type="primary")
                if sent and ans.strip():
                    ss.last_step = state.run("L'Insegnante corregge…", eng.answer_challenge, s, ch.id, ans)
                    st.rerun()
            c1, c2, c3 = st.columns(3)
            if not closed and c1.button("Non so", width="stretch", key="dunno"):
                ss.last_step = state.run("L'Insegnante prepara un indizio…", eng.answer_challenge, s, ch.id, None)
                st.rerun()
            if c2.button("Avanti → nuova sfida", width="stretch", key="next_ch"):
                ss.challenge = state.run("L'Insegnante prepara una sfida…", eng.next_challenge, s)
                ss.last_step = None
                st.rerun()
            if c3.button("Esame interno", width="stretch", key="to_exam"):
                st.switch_page("views/esame.py")
