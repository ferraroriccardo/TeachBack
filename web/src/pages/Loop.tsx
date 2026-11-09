import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import Brand, { ModePill } from '../components/Brand'
import ConceptMap, { Legend, STATUS_LABEL } from '../components/ConceptMap'
import { Chick, Owl } from '../components/Mascots'
import type { ChatMsg, Phase, Snapshot, Status } from '../types'

const STEPS: { phase: Phase; label: string }[] = [
  { phase: 'spiego', label: 'Explain' },
  { phase: 'domande', label: 'Questions' },
  { phase: 'prova', label: 'Exam attempt' },
  { phase: 'resoconto', label: 'Correction' },
  { phase: 'sfide', label: 'Challenges' },
]

type Busy = { who: 'sub' | 'owl'; label: string } | null
type Toast = { key: number; text: string; status: Status }

export default function Loop() {
  const { courseId = '' } = useParams()
  const nav = useNavigate()
  const [snap, setSnap] = useState<Snapshot | null>(null)
  const [busy, setBusy] = useState<Busy>(null)
  const [error, setError] = useState<string | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [text, setText] = useState('')
  const [examQ, setExamQ] = useState(0)
  const [demo, setDemo] = useState<{ explanation: string; fix: string } | null>(null)
  const threadEnd = useRef<HTMLDivElement>(null)
  const storeKey = `teachback:${courseId}`

  const apply = useCallback((s: Snapshot) => {
    setSnap(s)
    try { sessionStorage.setItem(storeKey, s.id) } catch { /* storage unavailable */ }
    if (s.changes.length) {
      const now = Date.now()
      const fresh = s.changes.map((c, i) => ({ key: now + i, text: `${c.name}: ${STATUS_LABEL[c.status].toLowerCase()}`, status: c.status }))
      setToasts(t => [...t, ...fresh])
      fresh.forEach(f => setTimeout(() => setToasts(t => t.filter(x => x.key !== f.key)), 4200))
    }
  }, [storeKey])

  useEffect(() => {
    let saved: string | null = null
    try { saved = sessionStorage.getItem(storeKey) } catch { /* ignore */ }
    const start = () => api.start(courseId).then(apply).catch(e => setError(e.message))
    if (saved) api.get(saved).then(apply).catch(start)
    else start()
    api.demo().then(setDemo).catch(() => {})
  }, [courseId, storeKey, apply])

  useEffect(() => { threadEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [snap?.chat.length, snap?.phase, busy, snap?.step])

  async function run(b: Busy, fn: () => Promise<Snapshot>, clear = false) {
    setBusy(b); setError(null)
    try {
      apply(await fn())
      if (clear) setText('')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(null)
    }
  }

  if (!snap) {
    return (
      <div className="page"><header className="topbar"><Brand /></header>
        <main className="loading">{error ? <p className="alert" role="alert">{error}</p> : <p>Preparing the session…</p>}</main>
      </div>
    )
  }

  const sid = snap.id
  const course = snap.course
  const name = (id: string) => course.concepts.find(c => c.id === id)?.name ?? id
  const [title, topic] = course.title.split(' - ')
  const phaseIdx = STEPS.findIndex(s => s.phase === snap.phase)
  const lastSub = [...snap.chat].reverse().find(m => m.role === 'sotto_studente')
  const wrongClaims = new Set(
    (snap.report?.feedback ?? []).filter(f => snap.statuses[f.concept_id] === 'non_ancora').flatMap(f => f.claim_ids),
  )
  const cited = new Set(snap.reply?.cited ?? [])
  const submitShortcut = (fn: () => void) => (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); fn() }
  }

  const newSession = (mode?: string) => run(null, () => api.start(courseId, mode ?? snap.mode, false))

  return (
    <div className="page loop-page">
      <header className="topbar">
        <div className="topbar-left">
          <Brand />
          <button className="link" onClick={() => nav('/')}>All courses</button>
        </div>
        <div className="topbar-right">
          {snap.live_available ? (
            <button className="mode-switch" onClick={() => newSession(snap.mode === 'live' ? 'offline' : 'live')}
              title="Switch engine (starts a new session)"><ModePill mode={snap.mode} /></button>
          ) : <ModePill mode={snap.mode} />}
          <button className="btn ghost small" onClick={() => newSession()}>New session</button>
        </div>
      </header>

      <div className="loop-head">
        <div>
          <p className="course-kicker">{title}</p>
          <h1>{topic ?? title}</h1>
        </div>
        <ol className="stepper" aria-label="Loop steps">
          {STEPS.map((s, i) => (
            <li key={s.phase} className={i < phaseIdx ? 'done' : i === phaseIdx ? 'current' : ''}
              aria-current={i === phaseIdx ? 'step' : undefined}>
              <span className="step-n">{i < phaseIdx ? '✓' : i + 1}</span>{s.label}
            </li>
          ))}
        </ol>
      </div>

      <main className="loop">
        <section className="thread-col" aria-label="Conversation">
          <div className="thread">
            {snap.chat.length === 0 && <Welcome />}
            {snap.chat.map((m, i) => (
              <Message key={i} m={m} isLastSub={m === lastSub} snap={snap} />
            ))}
            {snap.phase === 'prova' && snap.reply && !busy && <Verdict snap={snap} />}
            {snap.phase === 'resoconto' && snap.report && !busy && (
              <ReportCard snap={snap} name={name}
                onRevise={id => run({ who: 'sub', label: 'The Sub-student forgets the wrong claim' }, () => api.revise(sid, id), true)} />
            )}
            {snap.phase === 'sfide' && snap.step && !busy && <StepCard snap={snap} />}
            {busy && <Typing busy={busy} />}
            <div ref={threadEnd} />
          </div>

          {error && <p className="alert" role="alert">{error}</p>}

          <Composer>
            {snap.phase === 'spiego' && (
              <>
                {snap.focus && <p className="composer-note">Re-explain <b>{name(snap.focus)}</b> in your own words. You can reread {course.concepts.find(c => c.id === snap.focus)?.slide_ref}, but don't copy it.</p>}
                <textarea value={text} onChange={e => setText(e.target.value)} rows={4} aria-label="Your explanation"
                  placeholder={snap.focus ? 'E.g. “The catalyst does not shift the equilibrium because…”' : 'Explain the topic in your own words: give it a why or an example, not just keywords.'}
                  onKeyDown={submitShortcut(() => text.trim() && run({ who: 'sub', label: 'The Sub-student is listening' }, () => api.explain(sid, text), true))} />
                <div className="actions">
                  <span className="words">{wordCount(text)} words{wordCount(text) > 0 && wordCount(text) < 25 ? ' · add an example of your own' : ''}</span>
                  {demo && !snap.focus && <button className="btn ghost" onClick={() => setText(demo.explanation)}>Use the demo explanation</button>}
                  {demo && snap.focus === 'catalizzatore' && <button className="btn ghost" onClick={() => setText(demo.fix)}>Use the demo correction</button>}
                  <button className="btn primary" disabled={!text.trim() || !!busy}
                    onClick={() => run({ who: 'sub', label: 'The Sub-student is listening' }, () => api.explain(sid, text), true)}>
                    Teach the Sub-student
                  </button>
                </div>
              </>
            )}

            {snap.phase === 'domande' && (
              <>
                <form className="inline-form" onSubmit={e => { e.preventDefault(); if (text.trim()) run({ who: 'sub', label: 'The Sub-student is listening' }, () => api.reply(sid, text), true) }}>
                  <input value={text} onChange={e => setText(e.target.value)} placeholder="Answer its question or add an example…" aria-label="Reply to the Sub-student" />
                  <button className="btn secondary" disabled={!text.trim() || !!busy}>Reply</button>
                </form>
                <div className="exam-pick">
                  <label htmlFor="examq">When you think you've taught it enough, let it try an exam question</label>
                  <select id="examq" value={examQ} onChange={e => setExamQ(+e.target.value)}>
                    {course.exam_questions.map((q, i) => <option key={i} value={i}>{q}</option>)}
                  </select>
                  <div className="actions">
                    <button className="btn ghost" onClick={() => run(null, () => api.explainAgain(sid))}>Explain more</button>
                    <button className="btn primary" disabled={!!busy}
                      onClick={() => run({ who: 'sub', label: 'The Sub-student answers using only your claims' }, () => api.exam(sid, course.exam_questions[examQ]))}>
                      Let it try the question
                    </button>
                  </div>
                </div>
              </>
            )}

            {snap.phase === 'prova' && (
              <div className="actions">
                <button className="btn ghost" onClick={() => run(null, () => api.explainAgain(sid))}>Complete the explanation</button>
                <button className="btn owl" disabled={!!busy}
                  onClick={() => run({ who: 'owl', label: 'The Teacher is comparing your explanation with the slides' }, () => api.report(sid))}>
                  Ask the Teacher for a correction
                </button>
              </div>
            )}

            {snap.phase === 'resoconto' && (
              <div className="actions">
                {snap.report?.retry ? (
                  <button className="btn primary" onClick={() => run(null, () => api.explainAgain(sid))}>Try explaining again</button>
                ) : (
                  <button className="btn owl" disabled={!!busy}
                    onClick={() => run({ who: 'owl', label: 'The Teacher is preparing a challenge' }, () => api.challenge(sid))}>
                    Go to the Teacher's challenges
                  </button>
                )}
              </div>
            )}

            {snap.phase === 'sfide' && snap.challenge && (
              snap.challenge.closed ? (
                <div className="actions">
                  <button className="btn owl" disabled={!!busy}
                    onClick={() => run({ who: 'owl', label: 'The Teacher is preparing a challenge' }, () => api.challenge(sid))}>Next challenge</button>
                </div>
              ) : (
                <>
                  {snap.challenge.kind === 'rispiega' && <p className="composer-note">"Explain it yourself" rule: re-explain it on a different case. The earlier solution stays hidden until you answer.</p>}
                  <textarea value={text} onChange={e => setText(e.target.value)} rows={3} aria-label="Your answer"
                    placeholder="Answer with a why…"
                    onKeyDown={submitShortcut(() => text.trim() && run({ who: 'owl', label: 'The Teacher is grading' }, () => api.answer(sid, text), true))} />
                  <div className="actions">
                    <Hints used={snap.challenge.hints_used} />
                    <button className="btn ghost" disabled={!!busy}
                      onClick={() => run({ who: 'owl', label: 'The Teacher is preparing the next challenge' }, () => api.challenge(sid))}>Skip</button>
                    <button className="btn ghost" disabled={!!busy}
                      onClick={() => run({ who: 'owl', label: 'The Teacher is preparing a hint' }, () => api.answer(sid))}>I don't know, give me a hint</button>
                    <button className="btn owl" disabled={!text.trim() || !!busy}
                      onClick={() => run({ who: 'owl', label: 'The Teacher is grading' }, () => api.answer(sid, text), true)}>Send answer</button>
                  </div>
                </>
              )
            )}
          </Composer>
        </section>

        <aside className="side" aria-label="What you know and what the Sub-student knows">
          <section className="panel">
            <div className="panel-head">
              <h2>Concept map</h2>
              <Legend statuses={snap.statuses} />
            </div>
            <ConceptMap nodes={snap.graph.nodes} edges={snap.graph.edges} />
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>What the Sub-student knows</h2>
              <span className="count-pill">{snap.claims.length}</span>
            </div>
            {snap.claims.length === 0 ? (
              <p className="empty">Nothing yet. Every sentence you teach it becomes a numbered claim: that's all it will be able to use.</p>
            ) : (
              <ol className="claims">
                {snap.claims.map(c => (
                  <li key={c.n} className={wrongClaims.has(c.n) ? 'wrong' : cited.has(c.n) ? 'cited' : ''}>
                    <span className="claim-n">{c.n}</span>
                    <span>{c.text}</span>
                    {wrongClaims.has(c.n) && <em>contradicts the slides</em>}
                  </li>
                ))}
              </ol>
            )}
            {snap.reply && snap.reply.discarded > 0 && (
              <p className="fineprint">Citation check: {snap.reply.discarded} sentences discarded because none of your claims supported them.</p>
            )}
          </section>
        </aside>
      </main>

      <div className="toasts" aria-live="polite">
        {toasts.map(t => <div key={t.key} className="toast"><span className={`dot s-${t.status}`} />{t.text}</div>)}
      </div>
    </div>
  )
}

function wordCount(t: string) { return t.trim() ? t.trim().split(/\s+/).length : 0 }

function Composer({ children }: { children: React.ReactNode }) {
  return <div className="composer">{children}</div>
}

function Welcome() {
  return (
    <div className="msg sub">
      <Chick />
      <div className="bubble">
        <p>Hi! I know nothing about chemistry: I only learn from what you explain to me.</p>
        <p>Then I'll try an exam question. If you taught me something wrong, I'll get it wrong too, and you'll see exactly which of your sentences the mistake comes from.</p>
      </div>
    </div>
  )
}

function Message({ m, isLastSub, snap }: { m: ChatMsg; isLastSub: boolean; snap: Snapshot }) {
  if (m.role === 'studente') {
    return <div className="msg me"><div className="bubble">{m.text}</div></div>
  }
  if (m.role === 'esame') {
    return (
      <div className="exam-q">
        <span>Exam question</span>
        <p>{m.text}</p>
      </div>
    )
  }
  if (m.role === 'sotto_studente') {
    const kind = isLastSub ? snap.reply?.kind : undefined
    return (
      <div className={`msg sub ${kind === 'blocco' ? 'blocked' : ''}`}>
        <Chick />
        <div className="bubble">
          <span className="who">Sub-student</span>
          {m.text}
        </div>
      </div>
    )
  }
  const covered = m.text.startsWith('🔒')
  const hint = m.text.startsWith('Hint:') || m.text.includes(' Hint: ')
  const isChallenge = snap.challenge && m.text === snap.challenge.question
  return (
    <div className={`msg owl ${covered ? 'covered' : ''} ${hint ? 'hint' : ''}`}>
      <Owl />
      <div className="bubble">
        <span className="who">{isChallenge
          ? (snap.challenge!.kind === 'rispiega' ? 'Teacher · your turn to re-explain' : `Teacher · challenge on ${snap.course.concepts.find(c => c.id === snap.challenge!.concept_id)?.name}`)
          : 'Teacher'}</span>
        {covered ? 'Explanation hidden: now it’s your turn to re-explain it.' : m.text}
      </div>
    </div>
  )
}

function Verdict({ snap }: { snap: Snapshot }) {
  const r = snap.reply!
  if (r.kind === 'blocco') {
    return <div className="verdict amber"><b>It got stuck instead of making things up.</b> None of your claims is enough to reach the answer: there's a step you haven't explained.</div>
  }
  return (
    <div className="verdict blue">
      <b>It answered using only claims {r.cited.join(', ') || '—'}.</b> They're highlighted on the right.
      If the answer doesn't convince you, the mistake is in what you taught it.
    </div>
  )
}

function ReportCard({ snap, name, onRevise }: { snap: Snapshot; name: (id: string) => string; onRevise: (id: string) => void }) {
  const rep = snap.report!
  const [open, setOpen] = useState<Record<string, boolean>>({})
  if (rep.retry) {
    return (
      <div className="report">
        <div className="fb amber">
          <h3>Try explaining again</h3>
          <p>You explained less than a third of the key concepts with a why or an example. Missing: {rep.missing.map(name).join(', ')}.</p>
        </div>
      </div>
    )
  }
  const wrong = rep.feedback.filter(f => snap.statuses[f.concept_id] === 'non_ancora')
  const unclear = rep.feedback.filter(f => !wrong.includes(f))
  return (
    <div className="report">
      {wrong.map(f => (
        <div key={f.concept_id} className="fb red">
          <h3>{name(f.concept_id)}</h3>
          <p>{f.where}</p>
          <p className="slide-ref">Reread: {f.slide_ref}</p>
          {open[f.concept_id] && f.why && <p className="why">{f.why}</p>}
          <div className="fb-actions">
            {f.why && <button className="btn ghost small" aria-expanded={!!open[f.concept_id]}
              onClick={() => setOpen(o => ({ ...o, [f.concept_id]: !o[f.concept_id] }))}>{open[f.concept_id] ? 'Hide the why' : 'Why?'}</button>}
            <button className="btn primary small" onClick={() => onRevise(f.concept_id)}>Re-explain this concept</button>
          </div>
        </div>
      ))}
      {unclear.map(f => (
        <div key={f.concept_id} className="fb amber">
          <h3>{name(f.concept_id)}</h3>
          <p>{f.where}</p>
          <p className="slide-ref">Reread: {f.slide_ref}</p>
        </div>
      ))}
      {wrong.length === 0 && unclear.length === 0 && (
        <div className="fb green"><h3>No mistakes in your explanation</h3><p>The Sub-student learned well. Now the Teacher will challenge you on the concepts you didn't cover.</p></div>
      )}
      {rep.explained.length > 0 && (
        <p className="explained">Explained well: {rep.explained.map(name).join(', ')}</p>
      )}
      {rep.discrepancies.map((d, i) => <div key={i} className="fb amber small"><p>{d.note}</p></div>)}
    </div>
  )
}

function StepCard({ snap }: { snap: Snapshot }) {
  const s = snap.step!
  if (s.level === 'corretta') return <div className="verdict green"><b>Correct.</b> The concept turns {s.new_status === 'pronto' ? 'green' : 'yellow (with hints)'} on the map.</div>
  if (s.level === 'soluzione') return <div className="verdict red"><b>Solution shown after two hints.</b> Later, after another challenge, I'll ask you to re-explain it on a different case.</div>
  return null
}

function Hints({ used }: { used: number }) {
  return (
    <span className="hints" title="Hints used: after two, the solution is shown">
      <span className={used > 0 ? 'on' : ''} /><span className={used > 1 ? 'on' : ''} />hints
    </span>
  )
}

function Typing({ busy }: { busy: NonNullable<Busy> }) {
  return (
    <div className={`msg ${busy.who} typing`} role="status">
      {busy.who === 'sub' ? <Chick /> : <Owl />}
      <div className="bubble"><span className="dots"><i /><i /><i /></span>{busy.label}</div>
    </div>
  )
}
