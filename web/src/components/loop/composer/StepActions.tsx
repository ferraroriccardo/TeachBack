import { api } from '../../../api'
import type { StepProps } from './types'

const PREPARING_CHALLENGE = { who: 'owl', label: 'The Teacher is preparing a challenge' } as const

/** Step 3: after the exam attempt, ask the Teacher for a correction. */
export function ExamActions({ snap, busy, run }: StepProps) {
  return (
    <div className="actions">
      <button className="btn ghost" onClick={() => run(null, () => api.explainAgain(snap.id))}>Complete the explanation</button>
      <button className="btn owl" disabled={!!busy}
        onClick={() => run({ who: 'owl', label: 'The Teacher is comparing your explanation with the slides' }, () => api.report(snap.id))}>
        Ask the Teacher for a correction
      </button>
    </div>
  )
}

/** Step 4: after the correction, try again (below the threshold) or move on to the challenges. */
export function CorrectionActions({ snap, busy, run }: StepProps) {
  return (
    <div className="actions">
      {snap.report?.retry ? (
        <button className="btn primary" onClick={() => run(null, () => api.explainAgain(snap.id))}>Try explaining again</button>
      ) : (
        <button className="btn owl" disabled={!!busy} onClick={() => run(PREPARING_CHALLENGE, () => api.challenge(snap.id))}>
          Go to the Teacher's challenges
        </button>
      )}
    </div>
  )
}

export { PREPARING_CHALLENGE }
