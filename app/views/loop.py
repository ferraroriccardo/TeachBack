"""Il loop (mockup: static/Gemini_..._vazz (2).jpg per chat + grafo, (1).jpg per il resoconto)."""
import streamlit as st

from app import state, ui

eng, s = state.engine(), state.session()
course = eng.load_course(s.course_id)
ss = st.session_state
rep = s.hidden.get("report")
reply = ss.get("last_reply")

head_l, head_r = st.columns([3, 2])
with head_l:
    ui.brand()
with head_r:
    st.markdown(f'<div style="text-align:right;margin-top:.5rem">{ui.mode_badge(eng.mode)}</div>', unsafe_allow_html=True)
st.caption(f"{course.title} · Argomento: principio di Le Châtelier")
ui.stepper(s.phase)

# --------------------------------------------------------------------- guida della fase
focus = s.hidden.get("focus")
if s.phase == "spiego" and focus:
    c = course.concept(focus)
    ui.guide("✏️", f"Rispiega <b>{ui.esc(c.name)}</b> con parole tue. Se serve rileggi la "
                   f"<b>{ui.esc(c.slide_ref)}</b>, ma non copiarla: il Sotto-studente se ne accorge.")
elif s.phase == "spiego":
    ui.guide("📝", "Spiega l'argomento che temi <b>con parole tue</b>. Il Sotto-studente impara solo da te: "
                   "dagli un <b>perché</b> o un <b>esempio</b>, non le parole chiave.")
elif s.phase == "domande":
    ui.guide("🐣", "Il Sotto-studente ha una domanda. <b>Rispondi</b> per insegnargli di più, oppure "
                   "<b>fagli provare una domanda d'esame</b>: userà solo le tue affermazioni.")
elif s.phase == "prova" and reply is not None and reply.kind == "blocco":
    ui.guide("🧱", "Si è bloccato: <b>c'è un passaggio che non gli hai spiegato</b>. Completa la spiegazione "
                   "oppure chiedi il resoconto all'Insegnante.")
elif s.phase == "prova":
    ui.guide("👀", "Guarda <b>quali affermazioni ha usato</b> (in blu, a destra). Se la risposta è sbagliata, "
                   "l'errore viene dalla tua spiegazione. Chiedi il <b>resoconto</b> all'Insegnante.")
elif s.phase == "resoconto":
    ui.guide("🦉", "L'Insegnante ha confrontato la tua spiegazione con le slide. Ti dice prima <b>dove</b>; "
                   "il <b>perché</b> lo apri tu. Puoi <b>rispiegare</b> un concetto o passare alle <b>sfide</b>.")
elif s.phase == "sfide":
    ui.guide("🎯", "Rispondi con un perché. <b>Non so</b> ti dà un indizio (al massimo due, poi la soluzione). "
                   "<b>Avanti</b> è sempre disponibile: il concetto resta rosso e torna nel ripasso.")

left, right = st.columns([11, 9], gap="large")


# --------------------------------------------------------------------- colonna destra
with right:
    view = eng.get_graph(s)
    with st.container(border=True):
        st.markdown("#### Grafo di conoscenza")
        ui.legend(view)
        ui.graph(view)
        reasons = [n.reason for n in view.nodes if n.reason and n.status in ("non_ancora", "quasi")]
        if reasons:
            with st.expander(f"Perché alcuni concetti non tornano ({len(reasons)})"):
                for r in reasons:
                    st.markdown(f"- {r}")
    with st.container(border=True):
        st.markdown(f"#### 🧠 Cosa sa il Sotto-studente · {len(s.claims)}")
        st.caption("Solo queste affermazioni, estratte dalla tua spiegazione. "
                   "In blu quelle citate nell'ultima risposta, in rosso quelle in contrasto con le slide.")
        wrong = {}
        if rep is not None:
            for f in rep.feedback:
                if s.concept_status.get(f.concept_id) == "non_ancora":
                    for n in f.claim_ids:
                        wrong[n] = f.slide_ref.split(" - ")[0]
        ui.claims_panel(s.claims, reply, wrong)
        if reply is not None and reply.discarded:
            st.caption(f"🛡️ Controllo citazioni: {reply.discarded} frase/i scartate perché senza un'affermazione che le sostenga.")


# --------------------------------------------------------------------- colonna sinistra
def report_view() -> None:
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
    wrong_fb = [f for f in rep.feedback if s.concept_status.get(f.concept_id) == "non_ancora"]
    unclear = [f for f in rep.feedback if f not in wrong_fb]
    if wrong_fb:
        st.markdown('<div class="tb-sec">Punti critici ed errori (lacuna)</div>', unsafe_allow_html=True)
        for f in wrong_fb:
            st.markdown(f'<div class="tb-box tb-red"><h4>⚠️ {ui.esc(course.concept(f.concept_id).name)}</h4>'
                        f'{ui.esc(f.where)}<br><b>Cosa rivedere:</b> {ui.esc(f.slide_ref)}</div>', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 1])
            if c1.button("✏️ Rispiega questo concetto", key=f"revise_{f.concept_id}", type="primary", width="stretch"):
                state.act("Il Sotto-studente dimentica l'affermazione sbagliata…", eng.revise_concept, s, f.concept_id)
                ss.explanation = ""
                ss.last_reply = None
                st.rerun()
            if f.why:
                with c2.popover("💡 Perché? (2° livello)", width="stretch"):
                    st.write(f.why)
    if unclear:
        st.markdown('<div class="tb-sec">Da chiarire (da rivedere)</div>', unsafe_allow_html=True)
        for f in unclear:
            st.markdown(f'<div class="tb-box tb-yellow"><h4>❕ {ui.esc(course.concept(f.concept_id).name)}</h4>'
                        f'{ui.esc(f.where)}<br><b>Cosa rivedere:</b> {ui.esc(f.slide_ref)}</div>', unsafe_allow_html=True)
    if not wrong_fb and not unclear:
        st.markdown('<div class="tb-box tb-green" style="margin-top:.8rem"><h4>🎉 Nessun errore nella tua spiegazione</h4>'
                    'Il Sotto-studente ha imparato bene quello che gli hai detto. Ora l\'Insegnante ti sfida '
                    'sui concetti che non hai toccato.</div>', unsafe_allow_html=True)
    if rep.explained:
        st.markdown('<div class="tb-sec">Spiegati bene</div>', unsafe_allow_html=True)
        st.markdown('<div class="tb-box tb-green">✓ ' + " · ".join(ui.esc(course.concept(c).name) for c in rep.explained)
                    + '</div>', unsafe_allow_html=True)
    if rep.discrepancies:
        st.markdown('<div class="tb-sec">⚠️ Segnalazione nei materiali</div>', unsafe_allow_html=True)
        for i, d in enumerate(rep.discrepancies):
            st.markdown(f'<div class="tb-box tb-yellow">{ui.esc(d.note)}</div>', unsafe_allow_html=True)
            if st.button("Segnala al docente (anonimo)", key=f"disc_{i}"):
                st.toast("Segnalazione inviata in forma anonima al messaggio settimanale del docente.")


def verdict_card() -> None:
    if reply is None or s.phase != "prova":
        return
    used = sorted({i for x in reply.sentences for i in x.claim_ids})
    if reply.kind == "blocco":
        st.markdown('<div class="tb-verdict tb-yellow"><div class="ico">🧱</div><div><b>Si è bloccato invece di inventare.</b><br>'
                    'Nessuna delle tue affermazioni gli permette di arrivare alla risposta.</div></div>',
                    unsafe_allow_html=True)
    else:
        cites = ", ".join(str(n) for n in used) or "—"
        st.markdown(f'<div class="tb-verdict" style="background:#e3eefc;border:2px solid #8db3ec"><div class="ico">🔎</div>'
                    f'<div><b>Ha risposto usando solo le affermazioni {cites}.</b><br>'
                    f'Se la risposta non ti convince, il problema è in quello che gli hai insegnato.</div></div>',
                    unsafe_allow_html=True)


def welcome() -> None:
    st.markdown(
        '<div class="tb-msg sub"><div class="ava">🐣</div><div class="tb-bubble">'
        'Ciao! Di chimica non so <b>niente</b>: imparo solo da quello che mi spieghi tu. '
        'Poi proverò una domanda d\'esame, e se mi hai insegnato qualcosa di sbagliato lo sbaglierò anch\'io.'
        '</div></div>'
        '<ul class="tb-tip"><li>Scegli i 3-4 argomenti che temi, non tutto il corso.</li>'
        '<li>Usa un <b>perché</b> o un <b>esempio tuo</b>: elencare parole chiave non basta.</li>'
        '<li>Niente voti: i colori del grafo servono solo a te.</li></ul>', unsafe_allow_html=True)


with left:
    with st.container(border=True):
        is_sub = s.phase in ("spiego", "domande", "prova")
        ui.card_head("🐣" if is_sub else "🦉", "Sotto-studente AI" if is_sub else "Insegnante AI")
        if s.phase == "resoconto":
            report_view()
        elif s.phase == "sfide" and ss.get("challenge") is not None:
            ch = ss.challenge
            data = s.hidden["challenges"][ch.id]
            label = "🔁 Rispiega al Sotto-studente" if ch.kind == "rispiega" else "🎯 Sfida"
            name = course.concept(ch.concept_id).name
            dots = "●" * min(data["hints_used"], 2) + "○" * (2 - min(data["hints_used"], 2))
            st.markdown(f'<div class="tb-owl"><div class="ava">🦉</div><div style="flex:1"><b>{label} · {ui.esc(name)}</b>'
                        f'<span class="tb-dots" style="float:right" title="indizi usati">{dots}</span><br>'
                        f'{ui.esc(ch.question)}</div></div>', unsafe_allow_html=True)
            step = ss.get("last_step")
            if step is not None:
                box = {"corretta": "tb-green", "soluzione": "tb-red"}.get(step.level, "tb-yellow")
                title = {"corretta": "✅ Corretta", "indizio_1": "💡 Primo indizio", "indizio_2": "💡 Secondo indizio",
                         "soluzione": "📖 Soluzione (dopo due indizi)"}.get(step.level, "")
                body = step.text.replace("Indizio: ", "")
                st.markdown(f'<div class="tb-box {box}" style="margin-top:.7rem"><h4>{title}</h4>{ui.esc(body)}</div>',
                            unsafe_allow_html=True)
                if step.level == "soluzione":
                    st.caption("🔁 Più avanti, dopo un'altra domanda, ti chiederò di rispiegarlo su un caso diverso.")
            with st.expander("Conversazione completa"):
                ui.chat(s.chat)
        elif s.phase == "spiego" and not s.chat:
            welcome()
        else:
            ui.chat(s.chat, recent=3 if focus else 6)
            verdict_card()

    # ---- comandi della fase corrente
    if s.phase == "spiego":
        if "explanation" not in ss:
            ss.explanation = ""
        label = (f"La tua spiegazione di «{course.concept(focus).name}»" if focus
                 else "Spiega l'argomento al Sotto-studente, con parole tue")
        st.text_area(label, key="explanation", height=150,
                     placeholder="Es. «Se aggiungo un reagente, il sistema… perché…»")
        n_words = len(ss.explanation.split())
        st.caption(f"{n_words} parole" + (" · prova ad aggiungere un esempio tuo" if 0 < n_words < 25 else ""))
        c1, c2, c3 = st.columns([2, 2, 1])
        if c1.button("Insegna al Sotto-studente ➤", type="primary", width="stretch", key="teach"):
            if not ss.explanation.strip():
                st.warning("Scrivi prima una spiegazione.")
            else:
                if state.act("Il Sotto-studente ascolta…", eng.submit_explanation, s, ss.explanation) is not None:
                    ss.last_reply = state.act("Il Sotto-studente pensa a cosa non ha capito…", eng.substudent_reply, s)
                st.rerun()
        if not focus:
            c2.button("📋 Spiegazione della demo", width="stretch", key="demo_text",
                      help="Riempie il campo con la spiegazione del copione (contiene l'errore sul catalizzatore).",
                      on_click=lambda: ss.update(explanation=state.DEMO_EXPLANATION))
        elif focus == "catalizzatore":
            c2.button("📋 Correzione della demo", width="stretch", key="demo_fix",
                      on_click=lambda: ss.update(explanation=state.DEMO_FIX))
        c3.button("🎙️", disabled=True, width="stretch", key="mic", help="Voce: in roadmap (default testo).")

    elif s.phase == "domande":
        with st.form("reply_form", clear_on_submit=True, border=False):
            fc1, fc2 = st.columns([5, 1], vertical_alignment="bottom")
            msg = fc1.text_input("Rispondi al Sotto-studente", placeholder="Rispondi o aggiungi un esempio tuo…")
            sent = fc2.form_submit_button("Invia ➤", width="stretch")
        if sent and msg.strip():
            ss.last_reply = state.act("Il Sotto-studente ascolta…", eng.substudent_reply, s, msg)
            st.rerun()
        q = st.selectbox("📝 Domanda d'esame da fargli provare", course.exam_questions, key="exam_q")
        c1, c2 = st.columns([3, 2])
        if c1.button("Fagli provare la domanda d'esame →", type="primary", width="stretch", key="try_exam"):
            ss.last_reply = state.act("Il Sotto-studente prova a rispondere con le tue affermazioni…",
                                      eng.substudent_try_exam, s, q)
            st.rerun()
        if c2.button("Spiega ancora", width="stretch", key="back_explain"):
            s.phase = "spiego"
            st.rerun()

    elif s.phase == "prova":
        c1, c2 = st.columns([3, 2])
        if c1.button("Chiedi il resoconto all'Insegnante →", type="primary", width="stretch", key="ask_report"):
            state.act("L'Insegnante confronta la tua spiegazione con le slide…", eng.teacher_report, s)
            st.rerun()
        if c2.button("Completa la spiegazione", width="stretch", key="other_q"):
            s.phase = "domande"
            st.rerun()

    elif s.phase == "resoconto":
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
        elif c3.button("Procedi: sfide dell'Insegnante →", width="stretch", key="to_challenges",
                       type="secondary" if any(s.concept_status.get(f.concept_id) == "non_ancora"
                                               for f in (rep.feedback if rep else [])) else "primary"):
            ss.challenge = state.act("L'Insegnante prepara una sfida…", eng.next_challenge, s)
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
                    ss.last_step = state.act("L'Insegnante corregge…", eng.answer_challenge, s, ch.id, ans)
                    st.rerun()
            c1, c2, c3 = st.columns(3)
            if not closed and c1.button("🤔 Non so", width="stretch", key="dunno"):
                ss.last_step = state.act("L'Insegnante prepara un indizio…", eng.answer_challenge, s, ch.id, None)
                st.rerun()
            if c2.button("Prossima sfida →" if closed else "Avanti → nuova sfida", width="stretch", key="next_ch",
                         type="primary" if closed else "secondary"):
                ss.challenge = state.act("L'Insegnante prepara una sfida…", eng.next_challenge, s)
                ss.last_step = None
                st.rerun()
            if c3.button("Esame interno", width="stretch", key="to_exam"):
                st.switch_page("views/esame.py")
