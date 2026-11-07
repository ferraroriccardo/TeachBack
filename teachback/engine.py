"""Orchestratore di TeachBack: il loop spiego → domande → prova → resoconto → sfide.

Il flusso è guidato dal codice (una macchina a stati sulle fasi). Gli agenti decidono il
contenuto; il codice decide cosa è ammesso: guardrail, soglie, stati dei concetti,
scala degli indizi, regola "spiegalo tu", budget di passi e passaggio a un umano.

Le stesse regole valgono con il backend vero (Claude) e con quello offline.
"""
from __future__ import annotations

from datetime import date

from teachback import course as course_mod
from teachback import graph, guardrails, logger, memory
from teachback.agents import BACKEND_METHODS
from teachback.contracts import (
    Challenge, ChallengeStep, CitedSentence, Claim, Course, Discrepancy, Feedback,
    GraphAnswer, GraphView, ReviewItem, Session, SubStudentReply, TeacherReport,
    WeeklyMessage,
)

STATUS_FROM_VERDICT = {"spiegato": "pronto", "nominato": "quasi", "errato": "non_ancora"}
MIN_ACTIVE_STUDENTS = 10
COVERED_TEXT = "🔒 Spiegazione coperta: ora tocca a te rispiegarla al Sotto-studente."


class Engine:
    def __init__(self, backend, persist: bool = True):
        missing = [m for m in BACKEND_METHODS if not callable(getattr(backend, m, None))]
        if missing:
            raise TypeError(f"Backend incompleto, mancano: {missing}")
        self.backend = backend
        self.mode = backend.name
        self.persist = persist

    # --- corso e sessione ----------------------------------------------------------

    def load_course(self, course_id: str) -> Course:
        return course_mod.load_course(course_id)

    def start_session(self, course_id: str, topic_id: str, student_id: str = "demo",
                      resume: bool = False) -> Session:
        course = self.load_course(course_id)
        s = Session(course_id=course_id, topic_id=topic_id, student_id=student_id,
                    concept_status={c.id: "non_visto" for c in course.concepts})
        if self.persist:
            if resume:
                s.concept_status.update(memory.load_statuses(student_id, course_id))
            else:
                memory.reset(student_id, course_id)
        logger.log(s, "start_session", mode=self.mode, course=course_id, topic=topic_id)
        return s

    def _set_status(self, s: Session, concept_id: str, status: str, why: str) -> None:
        s.concept_status[concept_id] = status
        if self.persist:
            memory.save_status(s.student_id, s.course_id, concept_id, status)
        logger.log(s, "update_status", concept=concept_id, status=status, why=why)

    # --- 1 · Io spiego ------------------------------------------------------------------

    def submit_explanation(self, s: Session, text: str) -> list[Claim]:
        text = text.strip()
        s.hidden.pop("focus", None)
        s.chat.append(("studente", text))
        s.phase = "domande"
        if guardrails.asks_substudent_for_answer(text) and len(text.split()) < 25:
            s.hidden["pending_refusal"] = True
            logger.log(s, "guardrail_answer_request", text=text)
            return []
        overlap = guardrails.slide_overlap(text, course_mod.slide_chunks(s.course_id))
        if overlap >= guardrails.SLIDE_COPY_THRESHOLD:
            s.hidden["copied"] = True
            logger.log(s, "guardrail_slide_copy", overlap=round(overlap, 2))
        new = self.backend.extract_claims(text, len(s.claims) + 1, s)
        s.claims.extend(new)
        logger.log(s, "extract_claims", claims=[c.text for c in new])
        return new

    # --- 2 · Il Sotto-studente fa domande -------------------------------------------------

    def substudent_reply(self, s: Session, student_msg: str | None = None) -> SubStudentReply:
        if student_msg:
            student_msg = student_msg.strip()
            s.chat.append(("studente", student_msg))
            if guardrails.asks_substudent_for_answer(student_msg) and len(student_msg.split()) < 25:
                return self._say(s, SubStudentReply("rifiuto", guardrails.REFUSAL_TEXT), "answer_request")
            new = self.backend.extract_claims(student_msg, len(s.claims) + 1, s)
            s.claims.extend(new)
            logger.log(s, "extract_claims", claims=[c.text for c in new])
        if s.hidden.pop("pending_refusal", False) or not s.claims:
            return self._say(s, SubStudentReply("rifiuto", guardrails.REFUSAL_TEXT), "no_claims")
        if s.hidden.pop("copied", False):
            return self._say(s, SubStudentReply("domanda", guardrails.SLIDE_COPY_TEXT,
                                                copied_from_slides=True), "slide_copy")

        asked = [t for r, t in s.chat if r == "sotto_studente"]
        raw = self.backend.ask(s.claims, asked, s)
        kept, dropped = guardrails.validate_citations(_sentences(raw), s.claims)
        if not kept:  # nessuna domanda valida: domanda di riserva, sempre ancorata a un'affermazione
            c = s.claims[-1]
            kept = [CitedSentence(f"Mi fai un esempio tuo su «{_short(c.text)}»?", [c.n])]
        text = " ".join(x.text for x in kept)
        return self._say(s, SubStudentReply("domanda", text, kept, len(dropped)), "ask", dropped)

    # --- 3 · Il Sotto-studente prova una domanda d'esame ------------------------------------------

    def substudent_try_exam(self, s: Session, question: str | None = None) -> SubStudentReply:
        course = self.load_course(s.course_id)
        q = question or course.exam_questions[0]
        s.phase = "prova"
        s.chat.append(("esame", q))
        if not s.claims:
            reply = SubStudentReply("blocco", "Qui mi blocco: non mi hai ancora insegnato niente!")
        else:
            raw = self.backend.try_exam(s.claims, q, s)
            kept, dropped = guardrails.validate_citations(_sentences(raw), s.claims, context=q)
            missing = (raw.get("missing") or "").strip().rstrip(".?")
            if raw.get("kind") == "blocco" or not kept:
                tail = (f"non mi hai detto {missing}." if missing
                        else "con quello che mi hai insegnato non arrivo a una risposta.")
                partial = " ".join(f"{x.text} ({_cite(x)})" for x in kept)
                reply = SubStudentReply("blocco", (partial + " " if partial else "") + "Qui mi blocco: " + tail,
                                        kept, len(dropped))
            else:
                reply = SubStudentReply("risposta", " ".join(f"{x.text} ({_cite(x)})" for x in kept),
                                        kept, len(dropped))
            for x in kept:
                logger.log(s, "novelty", sentence=x.text,
                           ratio=round(guardrails.novelty_ratio(x.text, s.claims, q), 2))
            if dropped:
                logger.log(s, "guardrail_dropped", reasons=[r for _, r in dropped],
                           sentences=[d.text for d, _ in dropped])
        s.hidden["exam"] = {"question": q, "answer": reply.text, "kind": reply.kind}
        s.chat.append(("sotto_studente", reply.text))
        logger.log(s, "try_exam", question=q, kind=reply.kind,
                   cited=sorted({i for x in reply.sentences for i in x.claim_ids}))
        return reply

    # --- 4 · Resoconto dell'Insegnante ----------------------------------------------------------

    def teacher_report(self, s: Session) -> TeacherReport:
        course = self.load_course(s.course_id)
        raw = self.backend.report(course, course_mod.load_slides(s.course_id), s.claims,
                                  s.hidden.get("exam", {}), s)
        verdicts = {c["id"]: c for c in raw.get("concepts", []) if course.concept(c.get("id", ""))}
        explained = [cid for cid, v in verdicts.items() if v["verdict"] == "spiegato"]
        named = [cid for cid, v in verdicts.items() if v["verdict"] == "nominato"]
        wrong = [cid for cid, v in verdicts.items() if v["verdict"] == "errato"]
        missing = [c.id for c in course.concepts if c.id not in explained]
        retry = guardrails.below_threshold(len(explained), len(course.concepts))

        for cid, v in verdicts.items():
            if v["verdict"] in STATUS_FROM_VERDICT:
                self._set_status(s, cid, STATUS_FROM_VERDICT[v["verdict"]], f"resoconto: {v['verdict']}")

        feedback: list[Feedback] = []
        if not retry:  # sotto soglia si dice solo cosa manca, senza aiuti
            valid = {c.n for c in s.claims}
            for cid in wrong:
                v = verdicts[cid]
                feedback.append(Feedback(cid, v["where"] or "Qui qualcosa non torna con il materiale.",
                                         course.concept(cid).slide_ref, v.get("why") or None,
                                         [n for n in v.get("evidence_claims", []) if n in valid]))
            for cid in named:
                v = verdicts[cid]
                feedback.append(Feedback(cid, v["where"] or f"Hai nominato {course.concept(cid).name} senza un perché o un esempio.",
                                         course.concept(cid).slide_ref, None,
                                         [n for n in v.get("evidence_claims", []) if n in valid]))
        discrepancies = [Discrepancy(d["source"], guardrails.discrepancy_note(d["source"], d["detail"]))
                         for d in raw.get("discrepancies", [])]
        for d in discrepancies:
            logger.log(s, "flag_discrepancy", source=d.source, note=d.note)

        rep = TeacherReport(explained, missing, retry, feedback, discrepancies, named, raw.get("summary", ""))
        s.phase = "resoconto"
        s.hidden["report"] = rep
        s.chat.append(("insegnante", rep.summary if not retry else
                       "Riprova: mancano ancora " + ", ".join(course.concept(c).name for c in missing) + "."))
        logger.log(s, "teacher_report", explained=explained, named=named, wrong=wrong, retry=retry)
        return rep

    def revise_concept(self, s: Session, concept_id: str) -> list[Claim]:
        """Dal resoconto: lo studente rispiega un concetto. Le affermazioni giudicate sbagliate
        vengono ritirate (il Sotto-studente le "dimentica") e si torna a "Io spiego"."""
        course = self.load_course(s.course_id)
        rep = s.hidden.get("report")
        ids = set()
        if rep is not None:
            ids = {n for f in rep.feedback if f.concept_id == concept_id for n in f.claim_ids}
        removed = [c for c in s.claims if c.n in ids]
        s.claims = [c for c in s.claims if c.n not in ids]
        s.hidden["focus"] = concept_id
        s.phase = "spiego"
        name = course.concept(concept_id).name
        s.chat.append(("insegnante", f"Rispiega «{name}» al Sotto-studente con parole tue"
                                     + (f": ho tolto dalla sua memoria l'affermazione {', '.join(str(c.n) for c in removed)}."
                                        if removed else ".")))
        logger.log(s, "revise_concept", concept=concept_id, retracted=[c.n for c in removed])
        return removed

    # --- 5 · Sfide dell'Insegnante (con la regola "spiegalo tu") -------------------------------------

    def next_challenge(self, s: Session) -> Challenge:
        course = self.load_course(s.course_id)
        s.phase = "sfide"
        h = s.hidden
        h.setdefault("challenges", {})
        h.setdefault("retell", [])
        # "Avanti" sempre disponibile: chi salta lascia il concetto rosso e lo ritrova nel ripasso.
        for ch in h["challenges"].values():
            if not ch["closed"]:
                skipped = "pronto" if s.concept_status.get(ch["concept"]) == "pronto" else "non_ancora"
                self._close(s, ch, skipped, "sfida saltata con 'avanti'")
        done = h.get("challenges_done", 0)

        kind, concept = "sfida", None
        if h["retell"] and h["retell"][0]["after"] <= done:
            item = h["retell"].pop(0)
            kind, concept = "rispiega", course.concept(item["concept"])
            self._cover(s, item["concept"])
        if concept is None:
            concept = self._pick_concept(s, course)

        data = self.backend.make_challenge(course, course_mod.load_slides(s.course_id), concept, kind,
                                           h.get("cases", {}).get(concept.id, ""), s)
        cid = f"ch{len(h['challenges']) + 1}"
        h["challenges"][cid] = {"concept": concept.id, "kind": kind, "question": data["question"],
                                "hints": [data["hint_1"], data["hint_2"]], "solution": data["solution"],
                                "hints_used": 0, "closed": False}
        h.setdefault("cases", {})[concept.id] = data["question"]
        h["last_concept"] = concept.id
        s.chat.append(("insegnante", data["question"]))
        logger.log(s, "next_challenge", id=cid, concept=concept.id, kind=kind)
        return Challenge(cid, concept.id, data["question"], kind)

    def _pick_concept(self, s: Session, course: Course):
        order = {"non_visto": 0, "non_ancora": 1, "quasi": 2, "pronto": 3}
        last = s.hidden.get("last_concept")
        candidates = sorted(course.concepts, key=lambda c: (order[s.concept_status.get(c.id, "non_visto")],
                                                            c.id == last))
        return candidates[0]

    def answer_challenge(self, s: Session, challenge_id: str, answer: str | None) -> ChallengeStep:
        course = self.load_course(s.course_id)
        ch = s.hidden["challenges"][challenge_id]
        concept = course.concept(ch["concept"])
        prefix = ""
        if answer and answer.strip():
            s.chat.append(("studente", answer.strip()))
            g = self.backend.grade(course_mod.load_slides(s.course_id), concept, ch["question"],
                                   ch["solution"], answer, s)
            logger.log(s, "grade", id=challenge_id, correct=g["correct"])
            if g["correct"]:
                new = "pronto" if ch["hints_used"] == 0 else "quasi"
                self._close(s, ch, new, "sfida corretta")
                return self._teacher(s, ChallengeStep("corretta", g["feedback"], new))
            prefix = g["feedback"] + " "

        # "non so" o risposta sbagliata: primo indizio → secondo indizio → soluzione
        used = ch["hints_used"]
        ch["hints_used"] = used + 1
        if used < 2:
            level = "indizio_1" if used == 0 else "indizio_2"
            return self._teacher(s, ChallengeStep(level, prefix + "Indizio: " + ch["hints"][used]))
        self._close(s, ch, "non_ancora", "soluzione mostrata dopo due indizi")
        # Regola "spiegalo tu": più avanti, dopo un'altra domanda e su un caso diverso.
        s.hidden["retell"].append({"concept": concept.id, "after": s.hidden["challenges_done"] + 1})
        step = self._teacher(s, ChallengeStep("soluzione", prefix + ch["solution"], "non_ancora"))
        s.hidden.setdefault("solution_msgs", {}).setdefault(concept.id, []).append(len(s.chat) - 1)
        return step

    def _close(self, s: Session, ch: dict, status: str, why: str) -> None:
        if not ch["closed"]:
            ch["closed"] = True
            s.hidden["challenges_done"] = s.hidden.get("challenges_done", 0) + 1
            self._set_status(s, ch["concept"], status, why)
            if ch["kind"] == "rispiega":
                self._uncover(s, ch["concept"])

    def _cover(self, s: Session, concept_id: str) -> None:
        """Durante la rispiegazione la spiegazione completa non resta nella pagina."""
        covered = s.hidden.setdefault("covered", {})
        for idx in s.hidden.get("solution_msgs", {}).get(concept_id, []):
            if idx not in covered:
                covered[idx] = s.chat[idx]
                s.chat[idx] = ("insegnante", COVERED_TEXT)

    def _uncover(self, s: Session, concept_id: str) -> None:
        covered = s.hidden.get("covered", {})
        for idx in s.hidden.get("solution_msgs", {}).get(concept_id, []):
            if idx in covered:
                s.chat[idx] = covered.pop(idx)

    # --- grafo, segnalazioni, docente, ripasso ----------------------------------------------------

    def get_graph(self, s: Session) -> GraphView:
        return graph.view(self.load_course(s.course_id), s.concept_status)

    def ask_graph(self, s: Session, question: str) -> GraphAnswer:
        ans = graph.ask(self.load_course(s.course_id), s.concept_status, question)
        logger.log(s, "ask_graph", question=question, found=ans.found, path=ans.path)
        return ans

    def flag_judgement(self, s: Session, note: str) -> None:
        """Registrata e basta: serve a misurare l'accordo con il giudice. Nessuno la legge in tempo reale."""
        logger.log(s, "flag_judgement", note=note, statuses=dict(s.concept_status))

    def weekly_message(self, course_id: str, session: Session | None = None) -> WeeklyMessage:
        course = self.load_course(course_id)
        snap = course_mod.load_class_snapshot(course_id)
        errors = dict(snap.get("errors", {}))
        active = int(snap.get("active_students", 0))
        if session is not None and session.claims:
            active += 1
            for cid, st in session.concept_status.items():
                if st == "non_ancora":
                    errors[cid] = errors.get(cid, 0) + 1
        if not course.official:
            return WeeklyMessage(course_id, False, active, reason="Solo i corsi ufficiali inviano il messaggio al docente.")
        if active < MIN_ACTIVE_STUDENTS:
            return WeeklyMessage(course_id, False, active,
                                 reason=f"Servono almeno {MIN_ACTIVE_STUDENTS} studenti attivi perché i dati restino anonimi.")
        top = sorted(errors.items(), key=lambda kv: -kv[1])[:3]
        return WeeklyMessage(
            course_id, True, active,
            top_errors=[(course.concept(cid).name, course.concept(cid).slide_ref, n) for cid, n in top if course.concept(cid)],
            discrepancies=[Discrepancy(d["source"], d["note"]) for d in snap.get("discrepancies", [])],
            synthetic=bool(snap.get("synthetic")),
        )

    def due_reviews(self, s: Session, today: date | None = None) -> list[ReviewItem]:
        course = self.load_course(s.course_id)
        if self.persist:
            return memory.due_reviews(s.student_id, course, today)
        rows = [(cid, st, memory.next_interval(st, None), (today or date.today()).isoformat())
                for cid, st in s.concept_status.items() if st != "non_visto"]
        return memory.review_items(course, rows, today or date.today())

    # --- utilità ---------------------------------------------------------------------------

    def _say(self, s: Session, reply: SubStudentReply, why: str, dropped=()) -> SubStudentReply:
        s.chat.append(("sotto_studente", reply.text))
        logger.log(s, "substudent_reply", kind=reply.kind, why=why, text=reply.text,
                   cited=sorted({i for x in reply.sentences for i in x.claim_ids}),
                   dropped=[r for _, r in dropped])
        return reply

    def _teacher(self, s: Session, step: ChallengeStep) -> ChallengeStep:
        s.chat.append(("insegnante", step.text))
        logger.log(s, "challenge_step", level=step.level)
        return step


def _sentences(raw: dict) -> list[CitedSentence]:
    out = []
    for x in raw.get("sentences", []) or []:
        if isinstance(x, dict) and str(x.get("text", "")).strip():
            ids = [i for i in x.get("claim_ids", []) if isinstance(i, int)]
            out.append(CitedSentence(str(x["text"]).strip(), ids))
    return out


def _cite(x: CitedSentence) -> str:
    return ("aff. " if len(x.claim_ids) == 1 else "aff. ") + ", ".join(map(str, x.claim_ids))


def _short(text: str, words: int = 10) -> str:
    w = text.rstrip(".").split()
    return " ".join(w[:words]) + ("…" if len(w) > words else "")
