import './Toasts.css'
import type { Toast } from '../hooks/useLoopSession'

/** Status-change notifications (e.g. "Catalyst: not yet"), bottom right. */
export default function Toasts({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="toasts" aria-live="polite">
      {toasts.map(t => <div key={t.key} className="toast"><span className={`dot s-${t.status}`} />{t.text}</div>)}
    </div>
  )
}
