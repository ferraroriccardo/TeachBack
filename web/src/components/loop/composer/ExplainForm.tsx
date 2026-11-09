import { useEffect, useState } from 'react'
import { api } from '../../../api'
import { SUB_LISTENING, submitOnCtrlEnter, type StepProps } from './types'

const wordCount = (t: string) => (t.trim() ? t.trim().split(/\s+/).length : 0)

/** Step 1: explain the topic (or re-explain one concept after the correction). */
export default function ExplainForm({ snap, busy, run, text, setText }: StepProps) {
  const [demo, setDemo] = useState<{ explanation: string; fix: string } | null>(null)
  useEffect(() => { api.demo().then(setDemo).catch(() => {}) }, [])

  const focus = snap.course.concepts.find(c => c.id === snap.focus)
  const words = wordCount(text)
  const teach = () => { if (text.trim()) run(SUB_LISTENING, () => api.explain(snap.id, text), true) }

  return (
    <>
      {focus && (
        <p className="composer-note">
          Re-explain <b>{focus.name}</b> in your own words. You can reread {focus.slide_ref}, but don't copy it.
        </p>
      )}
      <textarea value={text} onChange={e => setText(e.target.value)} rows={4} aria-label="Your explanation"
        placeholder={focus ? 'E.g. “The catalyst does not shift the equilibrium because…”'
          : 'Explain the topic in your own words: give it a why or an example, not just keywords.'}
        onKeyDown={submitOnCtrlEnter(teach)} />
      <div className="actions">
        <span className="words">{words} words{words > 0 && words < 25 ? ' · add an example of your own' : ''}</span>
        {demo && !focus && <button className="btn ghost" onClick={() => setText(demo.explanation)}>Use the demo explanation</button>}
        {demo && focus?.id === 'catalizzatore' && <button className="btn ghost" onClick={() => setText(demo.fix)}>Use the demo correction</button>}
        <button className="btn primary" disabled={!text.trim() || !!busy} onClick={teach}>Teach the Sub-student</button>
      </div>
    </>
  )
}
