import './SidePanel.css'
import ConceptMap, { Legend } from '../ConceptMap'
import type { Snapshot } from '../../types'

/** Right column: the concept map and everything the Sub-student knows. */
export default function SidePanel({ snap }: { snap: Snapshot }) {
  return (
    <aside className="side" aria-label="What you know and what the Sub-student knows">
      <section className="panel">
        <div className="panel-head">
          <h2>Concept map</h2>
          <Legend statuses={snap.statuses} />
        </div>
        <ConceptMap nodes={snap.graph.nodes} edges={snap.graph.edges} />
      </section>
      <ClaimsPanel snap={snap} />
    </aside>
  )
}

function ClaimsPanel({ snap }: { snap: Snapshot }) {
  const wrong = new Set(
    (snap.report?.feedback ?? []).filter(f => snap.statuses[f.concept_id] === 'non_ancora').flatMap(f => f.claim_ids),
  )
  const cited = new Set(snap.reply?.cited ?? [])
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>What the Sub-student knows</h2>
        <span className="count-pill">{snap.claims.length}</span>
      </div>
      {snap.claims.length === 0 ? (
        <p className="empty">Nothing yet. Every sentence you teach it becomes a numbered claim: that's all it will be able to use.</p>
      ) : (
        <ol className="claims">
          {snap.claims.map(c => (
            <li key={c.n} className={wrong.has(c.n) ? 'wrong' : cited.has(c.n) ? 'cited' : ''}>
              <span className="claim-n">{c.n}</span>
              <span>{c.text}</span>
              {wrong.has(c.n) && <em>contradicts the slides</em>}
            </li>
          ))}
        </ol>
      )}
      {snap.reply && snap.reply.discarded > 0 && (
        <p className="fineprint">Citation check: {snap.reply.discarded} sentences discarded because none of your claims supported them.</p>
      )}
    </section>
  )
}
