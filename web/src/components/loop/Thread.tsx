import { useEffect, useRef } from 'react'
import { api } from '../../api'
import type { Busy, Run } from '../../hooks/useLoopSession'
import type { Snapshot } from '../../types'
import { Message, Typing, Welcome } from './Message'
import ReportCard from './ReportCard'
import { ChallengeVerdict, ExamVerdict } from './Verdicts'

type Props = { snap: Snapshot; busy: Busy; run: Run; name: (id: string) => string }

/** The conversation, plus the card that belongs to the current step. */
export default function Thread({ snap, busy, run, name }: Props) {
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [snap.chat.length, snap.phase, busy, snap.step])

  const lastSub = [...snap.chat].reverse().find(m => m.role === 'sotto_studente')
  const revise = (id: string) => run({ who: 'sub', label: 'The Sub-student forgets the wrong claim' }, () => api.revise(snap.id, id), true)

  return (
    <div className="thread">
      {snap.chat.length === 0 && <Welcome />}
      {snap.chat.map((m, i) => <Message key={i} m={m} isLastSub={m === lastSub} snap={snap} />)}
      {!busy && snap.phase === 'prova' && snap.reply && <ExamVerdict reply={snap.reply} />}
      {!busy && snap.phase === 'resoconto' && snap.report && <ReportCard snap={snap} name={name} onRevise={revise} />}
      {!busy && snap.phase === 'sfide' && snap.step && <ChallengeVerdict step={snap.step} />}
      {busy && <Typing busy={busy} />}
      <div ref={end} />
    </div>
  )
}
