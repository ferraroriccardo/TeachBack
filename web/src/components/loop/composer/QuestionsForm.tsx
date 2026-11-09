import { useState } from 'react'
import { api } from '../../../api'
import { SUB_LISTENING, type StepProps } from './types'

/** Step 2: answer the Sub-student's questions, then let it try an exam question. */
export default function QuestionsForm({ snap, busy, run, text, setText }: StepProps) {
  const [examQ, setExamQ] = useState(0)
  const questions = snap.course.exam_questions

  return (
    <>
      <form className="inline-form" onSubmit={e => {
        e.preventDefault()
        if (text.trim()) run(SUB_LISTENING, () => api.reply(snap.id, text), true)
      }}>
        <input value={text} onChange={e => setText(e.target.value)} placeholder="Answer its question or add an example…"
          aria-label="Reply to the Sub-student" />
        <button className="btn secondary" disabled={!text.trim() || !!busy}>Reply</button>
      </form>
      <div className="exam-pick">
        <label htmlFor="examq">When you think you've taught it enough, let it try an exam question</label>
        <select id="examq" value={examQ} onChange={e => setExamQ(+e.target.value)}>
          {questions.map((q, i) => <option key={i} value={i}>{q}</option>)}
        </select>
        <div className="actions">
          <button className="btn ghost" onClick={() => run(null, () => api.explainAgain(snap.id))}>Explain more</button>
          <button className="btn primary" disabled={!!busy}
            onClick={() => run({ who: 'sub', label: 'The Sub-student answers using only your claims' }, () => api.exam(snap.id, questions[examQ]))}>
            Let it try the question
          </button>
        </div>
      </div>
    </>
  )
}
