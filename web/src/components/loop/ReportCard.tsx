import { useState } from 'react'
import type { Snapshot } from '../../types'

type Props = { snap: Snapshot; name: (id: string) => string; onRevise: (conceptId: string) => void }

/** The Teacher's correction: where you went wrong (with the slide), and the why on request. */
export default function ReportCard({ snap, name, onRevise }: Props) {
  const rep = snap.report!
  const [open, setOpen] = useState<Record<string, boolean>>({})

  if (rep.retry) {
    return (
      <div className="report">
        <div className="fb amber">
          <h3>Try explaining again</h3>
          <p>You explained less than a third of the key concepts with a why or an example. Missing: {rep.missing.map(name).join(', ')}.</p>
        </div>
      </div>
    )
  }

  const wrong = rep.feedback.filter(f => snap.statuses[f.concept_id] === 'non_ancora')
  const unclear = rep.feedback.filter(f => !wrong.includes(f))
  return (
    <div className="report">
      {wrong.map(f => (
        <div key={f.concept_id} className="fb red">
          <h3>{name(f.concept_id)}</h3>
          <p>{f.where}</p>
          <p className="slide-ref">Reread: {f.slide_ref}</p>
          {open[f.concept_id] && f.why && <p className="why">{f.why}</p>}
          <div className="fb-actions">
            {f.why && (
              <button className="btn ghost small" aria-expanded={!!open[f.concept_id]}
                onClick={() => setOpen(o => ({ ...o, [f.concept_id]: !o[f.concept_id] }))}>
                {open[f.concept_id] ? 'Hide the why' : 'Why?'}
              </button>
            )}
            <button className="btn primary small" onClick={() => onRevise(f.concept_id)}>Re-explain this concept</button>
          </div>
        </div>
      ))}
      {unclear.map(f => (
        <div key={f.concept_id} className="fb amber">
          <h3>{name(f.concept_id)}</h3>
          <p>{f.where}</p>
          <p className="slide-ref">Reread: {f.slide_ref}</p>
        </div>
      ))}
      {wrong.length === 0 && unclear.length === 0 && (
        <div className="fb green">
          <h3>No mistakes in your explanation</h3>
          <p>The Sub-student learned well. Now the Teacher will challenge you on the concepts you didn't cover.</p>
        </div>
      )}
      {rep.explained.length > 0 && <p className="explained">Explained well: {rep.explained.map(name).join(', ')}</p>}
      {rep.discrepancies.map((d, i) => <div key={i} className="fb amber small"><p>{d.note}</p></div>)}
    </div>
  )
}
