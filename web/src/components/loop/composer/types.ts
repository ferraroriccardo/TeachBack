import type { Busy, Run } from '../../../hooks/useLoopSession'
import type { Snapshot } from '../../../types'

/** What every step's controls receive from the loop page. */
export interface StepProps {
  snap: Snapshot
  busy: Busy
  run: Run
  text: string
  setText: (t: string) => void
}

export const SUB_LISTENING = { who: 'sub', label: 'The Sub-student is listening' } as const

/** Ctrl/Cmd + Enter submits a textarea. */
export const submitOnCtrlEnter = (submit: () => void) => (e: React.KeyboardEvent) => {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit() }
}
