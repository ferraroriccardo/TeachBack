import type { Snapshot } from '../../types'

/** After the exam attempt: which claims the Sub-student used, or where it got stuck. */
export function ExamVerdict({ reply }: { reply: NonNullable<Snapshot['reply']> }) {
  if (reply.kind === 'blocco') {
    return <div className="verdict amber"><b>It got stuck instead of making things up.</b> None of your claims is enough to reach the answer: there's a step you haven't explained.</div>
  }
  return (
    <div className="verdict blue">
      <b>It answered using only claims {reply.cited.join(', ') || '—'}.</b> They're highlighted on the right.
      If the answer doesn't convince you, the mistake is in what you taught it.
    </div>
  )
}

/** Outcome of a challenge once it is closed (correct, or solution shown). */
export function ChallengeVerdict({ step }: { step: NonNullable<Snapshot['step']> }) {
  if (step.level === 'corretta') {
    return <div className="verdict green"><b>Correct.</b> The concept turns {step.new_status === 'pronto' ? 'green' : 'yellow (with hints)'} on the map.</div>
  }
  if (step.level === 'soluzione') {
    return <div className="verdict red"><b>Solution shown after two hints.</b> Later, after another challenge, I'll ask you to re-explain it on a different case.</div>
  }
  return null
}
