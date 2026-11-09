import { Chick, Owl } from '../Mascots'
import type { Busy } from '../../hooks/useLoopSession'
import type { ChatMsg, Snapshot } from '../../types'

export function Welcome() {
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

/** One chat message, styled by who said it: you, the Sub-student, the Teacher or the exam question. */
export function Message({ m, isLastSub, snap }: { m: ChatMsg; isLastSub: boolean; snap: Snapshot }) {
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
    const stuck = isLastSub && snap.reply?.kind === 'blocco'
    return (
      <div className={`msg sub ${stuck ? 'blocked' : ''}`}>
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
  const ch = snap.challenge
  const isChallenge = ch && m.text === ch.question
  const who = !isChallenge ? 'Teacher'
    : ch.kind === 'rispiega' ? 'Teacher · your turn to re-explain'
    : `Teacher · challenge on ${snap.course.concepts.find(c => c.id === ch.concept_id)?.name}`
  return (
    <div className={`msg owl ${covered ? 'covered' : ''} ${hint ? 'hint' : ''}`}>
      <Owl />
      <div className="bubble">
        <span className="who">{who}</span>
        {covered ? 'Explanation hidden: now it’s your turn to re-explain it.' : m.text}
      </div>
    </div>
  )
}

export function Typing({ busy }: { busy: NonNullable<Busy> }) {
  return (
    <div className={`msg ${busy.who} typing`} role="status">
      {busy.who === 'sub' ? <Chick /> : <Owl />}
      <div className="bubble"><span className="dots"><i /><i /><i /></span>{busy.label}</div>
    </div>
  )
}
