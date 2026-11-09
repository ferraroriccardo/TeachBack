import { useParams } from 'react-router-dom'
import Brand from '../components/Brand'
import Composer from '../components/loop/composer/Composer'
import LoopHeader from '../components/loop/LoopHeader'
import SidePanel from '../components/loop/SidePanel'
import Thread from '../components/loop/Thread'
import Toasts from '../components/Toasts'
import { useLoopSession } from '../hooks/useLoopSession'

/** The learning loop: explain → questions → exam attempt → correction → challenges. */
export default function Loop() {
  const { courseId = '' } = useParams()
  const { snap, busy, error, toasts, text, setText, run, newSession } = useLoopSession(courseId)

  if (!snap) {
    return (
      <div className="page">
        <header className="topbar"><Brand /></header>
        <main className="loading">{error ? <p className="alert" role="alert">{error}</p> : <p>Preparing the session…</p>}</main>
      </div>
    )
  }

  const name = (id: string) => snap.course.concepts.find(c => c.id === id)?.name ?? id

  return (
    <div className="page loop-page">
      <LoopHeader snap={snap} onNewSession={newSession} />
      <main className="loop">
        <section className="thread-col" aria-label="Conversation">
          <Thread snap={snap} busy={busy} run={run} name={name} />
          {error && <p className="alert" role="alert">{error}</p>}
          <Composer snap={snap} busy={busy} run={run} text={text} setText={setText} />
        </section>
        <SidePanel snap={snap} />
      </main>
      <Toasts toasts={toasts} />
    </div>
  )
}
