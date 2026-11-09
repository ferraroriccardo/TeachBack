import { Link } from 'react-router-dom'

export default function Brand() {
  return (
    <Link to="/" className="brand" aria-label="TeachBack, back to courses">
      <img src="/favicon.svg" alt="" width={28} height={28} />
      <span>TeachBack</span>
    </Link>
  )
}

export function ModePill({ mode }: { mode: string }) {
  return (
    <span className={`mode mode-${mode}`} title={mode === 'live'
      ? 'The agents run on Claude via the API'
      : 'Rule-based agents, no network: same orchestrator and same guardrails'}>
      <span className="mode-dot" />{mode === 'live' ? 'Live · Claude' : 'Offline'}
    </span>
  )
}
