import './ConceptMap.css'
import { useState } from 'react'
import type { GraphEdge, GraphNode, Status } from '../types'

export const STATUS_LABEL: Record<Status, string> = {
  pronto: 'Ready', quasi: 'Almost', non_ancora: 'Not yet', non_visto: 'Not seen',
}

const NODE_W = 120
const NODE_H = 46
const SX = 70    // pixels per layout unit
const SY = 54

/** Concept map: prerequisite → concept, coloured with the student's status. */
export default function ConceptMap({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  const [hover, setHover] = useState<string | null>(null)
  const pos = Object.fromEntries(
    nodes.map((n, i) => {
      const [x, y] = n.layout ?? [i * 2, (i % 2) * 2]
      return [n.id, { x: x * SX + NODE_W / 2 + 8, y: (3 - y) * SY + 10 }]
    }),
  )
  const xs = Object.values(pos).map(p => p.x)
  const ys = Object.values(pos).map(p => p.y)
  const w = Math.max(...xs) + NODE_W / 2 + 8
  const h = Math.max(...ys) + NODE_H / 2 + 10
  const reason = nodes.find(n => n.id === hover)?.reason

  return (
    <div className="map">
      <div className="map-scroll"><svg viewBox={`0 ${Math.min(...ys) - NODE_H / 2 - 10} ${w} ${h - Math.min(...ys) + NODE_H / 2 + 10}`} role="img"
        aria-label="Map of the course concepts and their status">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0 0L10 5L0 10z" fill="var(--edge)" />
          </marker>
        </defs>
        {edges.map(e => {
          const a = pos[e.source], b = pos[e.target]
          if (!a || !b) return null
          const [x1, y1] = clip(a, b), [x2, y2] = clip(b, a)
          const mx = (x1 + x2) / 2, my = (y1 + y2) / 2 - (Math.abs(y1 - y2) < 4 ? 28 : 0)
          return <path key={e.source + e.target} d={`M${x1} ${y1} Q${mx} ${my} ${x2} ${y2}`}
            fill="none" stroke="var(--edge)" strokeWidth="1.6" markerEnd="url(#arrow)" />
        })}
        {nodes.map(n => {
          const p = pos[n.id]
          return (
            <g key={n.id} className={`node s-${n.status}`} transform={`translate(${p.x - NODE_W / 2} ${p.y - NODE_H / 2})`}
              onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)} tabIndex={0}
              onFocus={() => setHover(n.id)} onBlur={() => setHover(null)}>
              <title>{`${n.label}: ${STATUS_LABEL[n.status]}`}</title>
              <rect width={NODE_W} height={NODE_H} rx={NODE_H / 2} />
              <foreignObject x="6" y="0" width={NODE_W - 12} height={NODE_H}>
                <div className="node-label">{n.label}</div>
              </foreignObject>
            </g>
          )
        })}
      </svg></div>
      <p className="map-hint" aria-live="polite">{reason ?? 'Arrows point from a prerequisite to the concept that requires it.'}</p>
    </div>
  )
}

// Point on the edge (approximate ellipse) of node a in the direction of b.
function clip(a: { x: number; y: number }, b: { x: number; y: number }): [number, number] {
  const dx = b.x - a.x, dy = b.y - a.y
  const rx = NODE_W / 2 + 3, ry = NODE_H / 2 + 3
  const t = 1 / Math.sqrt((dx * dx) / (rx * rx) + (dy * dy) / (ry * ry))
  return [a.x + dx * t, a.y + dy * t]
}

export function Legend({ statuses }: { statuses: Record<string, Status> }) {
  const count = (s: Status) => Object.values(statuses).filter(v => v === s).length
  return (
    <ul className="legend">
      {(['pronto', 'quasi', 'non_ancora', 'non_visto'] as Status[]).map(s => (
        <li key={s}><span className={`dot s-${s}`} />{STATUS_LABEL[s]} <b>{count(s)}</b></li>
      ))}
    </ul>
  )
}
