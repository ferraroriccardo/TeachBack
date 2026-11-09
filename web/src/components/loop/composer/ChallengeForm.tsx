import { api } from '../../../api'
import { PREPARING_CHALLENGE } from './StepActions'
import { submitOnCtrlEnter, type StepProps } from './types'

const GRADING = { who: 'owl', label: 'The Teacher is grading' } as const

/** Step 5: answer the Teacher's challenge, ask for a hint, or skip. */
export default function ChallengeForm({ snap, busy, run, text, setText }: StepProps) {
  const ch = snap.challenge!
  const next = () => run(PREPARING_CHALLENGE, () => api.challenge(snap.id))
  const send = () => { if (text.trim()) run(GRADING, () => api.answer(snap.id, text), true) }

  if (ch.closed) {
    return (
      <div className="actions">
        <button className="btn owl" disabled={!!busy} onClick={next}>Next challenge</button>
      </div>
    )
  }
  return (
    <>
      {ch.kind === 'rispiega' && (
        <p className="composer-note">"Explain it yourself" rule: re-explain it on a different case. The earlier solution stays hidden until you answer.</p>
      )}
      <textarea value={text} onChange={e => setText(e.target.value)} rows={3} aria-label="Your answer"
        placeholder="Answer with a why…" onKeyDown={submitOnCtrlEnter(send)} />
      <div className="actions">
        <Hints used={ch.hints_used} />
        <button className="btn ghost" disabled={!!busy} onClick={next}>Skip</button>
        <button className="btn ghost" disabled={!!busy}
          onClick={() => run({ who: 'owl', label: 'The Teacher is preparing a hint' }, () => api.answer(snap.id))}>
          I don't know, give me a hint
        </button>
        <button className="btn owl" disabled={!text.trim() || !!busy} onClick={send}>Send answer</button>
      </div>
    </>
  )
}

function Hints({ used }: { used: number }) {
  return (
    <span className="hints" title="Hints used: after two, the solution is shown">
      <span className={used > 0 ? 'on' : ''} /><span className={used > 1 ? 'on' : ''} />hints
    </span>
  )
}
