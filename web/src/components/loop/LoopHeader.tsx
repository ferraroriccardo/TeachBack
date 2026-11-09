import { useNavigate } from 'react-router-dom'
import Brand, { ModePill } from '../Brand'
import type { Phase, Snapshot } from '../../types'

const STEPS: { phase: Phase; label: string }[] = [
  { phase: 'spiego', label: 'Explain' },
  { phase: 'domande', label: 'Questions' },
  { phase: 'prova', label: 'Exam attempt' },
  { phase: 'resoconto', label: 'Correction' },
  { phase: 'sfide', label: 'Challenges' },
]

export default function LoopHeader({ snap, onNewSession }: { snap: Snapshot; onNewSession: (mode?: string) => void }) {
  const nav = useNavigate()
  const [title, topic] = snap.course.title.split(' - ')
  return (
    <>
      <header className="topbar">
        <div className="topbar-left">
          <Brand />
          <button className="link" onClick={() => nav('/')}>All courses</button>
        </div>
        <div className="topbar-right">
          {snap.live_available ? (
            <button className="mode-switch" onClick={() => onNewSession(snap.mode === 'live' ? 'offline' : 'live')}
              title="Switch engine (starts a new session)"><ModePill mode={snap.mode} /></button>
          ) : <ModePill mode={snap.mode} />}
          <button className="btn ghost small" onClick={() => onNewSession()}>New session</button>
        </div>
      </header>

      <div className="loop-head">
        <div>
          <p className="course-kicker">{title}</p>
          <h1>{topic ?? title}</h1>
        </div>
        <Stepper phase={snap.phase} />
      </div>
    </>
  )
}

function Stepper({ phase }: { phase: Phase }) {
  const current = STEPS.findIndex(s => s.phase === phase)
  return (
    <ol className="stepper" aria-label="Loop steps">
      {STEPS.map((s, i) => (
        <li key={s.phase} className={i < current ? 'done' : i === current ? 'current' : ''}
          aria-current={i === current ? 'step' : undefined}>
          <span className="step-n">{i < current ? '✓' : i + 1}</span>{s.label}
        </li>
      ))}
    </ol>
  )
}
