import { STATUS_LABEL } from '../ConceptMap'
import type { CourseCard as Course, Status } from '../../types'

/** A course on the dashboard: concepts coloured by status, progress, and the button to open the loop. */
export default function CourseCard({ c, onOpen }: { c: Course; onOpen: () => void }) {
  const [title, topic] = c.title.includes(' - ') ? c.title.split(' - ') : [c.title, c.subtitle]
  const pct = c.concepts ? Math.round((c.ready / c.concepts) * 100) : 0
  const started = c.statuses && Object.values(c.statuses).some(s => s !== 'non_visto')
  const Tag = c.example ? 'div' : 'button'
  return (
    <Tag className={`course ${c.example ? 'is-example' : ''}`} {...(c.example ? { 'aria-disabled': true } : { onClick: onOpen })}>
      <div className="course-top">
        <span className={`badge ${c.official ? 'official' : 'community'}`}>{c.official ? 'Official' : 'Created by students'}</span>
        {c.example && <span className="badge example">Example</span>}
      </div>
      <h3>{title}</h3>
      <p className="course-topic">{topic}</p>
      {c.statuses && c.names ? (
        <ul className="concept-dots" aria-label="Concept status">
          {Object.entries(c.statuses).map(([id, s]) => (
            <li key={id} title={`${c.names![id]}: ${STATUS_LABEL[s as Status]}`}><span className={`dot s-${s}`} />{c.names![id]}</li>
          ))}
        </ul>
      ) : (
        <div className="concept-dots ghost" aria-hidden="true">
          {Array.from({ length: c.concepts }, (_, i) => <span key={i} className={`dot ${i < c.ready ? 's-pronto' : 's-non_visto'}`} />)}
        </div>
      )}
      <div className="course-foot">
        <div className="progress" aria-label={`${c.ready} of ${c.concepts} concepts ready`}>
          <div style={{ width: `${pct}%` }} />
        </div>
        <span className="count">{c.ready}/{c.concepts} ready</span>
      </div>
      {!c.example && <span className="cta">{started ? 'Continue explaining' : 'Start explaining'}</span>}
    </Tag>
  )
}
