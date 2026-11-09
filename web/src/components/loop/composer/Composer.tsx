import ChallengeForm from './ChallengeForm'
import ExplainForm from './ExplainForm'
import QuestionsForm from './QuestionsForm'
import { CorrectionActions, ExamActions } from './StepActions'
import type { StepProps } from './types'

/** The controls at the bottom of the conversation: they change with the loop step. */
export default function Composer(props: StepProps) {
  const { snap } = props
  return (
    <div className="composer">
      {snap.phase === 'spiego' && <ExplainForm {...props} />}
      {snap.phase === 'domande' && <QuestionsForm {...props} />}
      {snap.phase === 'prova' && <ExamActions {...props} />}
      {snap.phase === 'resoconto' && <CorrectionActions {...props} />}
      {snap.phase === 'sfide' && snap.challenge && <ChallengeForm {...props} />}
    </div>
  )
}
