import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import { STATUS_LABEL } from '../components/ConceptMap'
import type { Snapshot, Status } from '../types'

export type Busy = { who: 'sub' | 'owl'; label: string } | null
export type Toast = { key: number; text: string; status: Status }
export type Run = (busy: Busy, call: () => Promise<Snapshot>, clearText?: boolean) => Promise<void>

/** One learning-loop session for a course: loads or resumes it and runs each step against the API. */
export function useLoopSession(courseId: string) {
  const [snap, setSnap] = useState<Snapshot | null>(null)
  const [busy, setBusy] = useState<Busy>(null)
  const [error, setError] = useState<string | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [text, setText] = useState('')
  const storeKey = `teachback:${courseId}`

  const apply = useCallback((s: Snapshot) => {
    setSnap(s)
    try { sessionStorage.setItem(storeKey, s.id) } catch { /* storage unavailable */ }
    if (s.changes.length) {
      const now = Date.now()
      const fresh = s.changes.map((c, i) => ({ key: now + i, text: `${c.name}: ${STATUS_LABEL[c.status].toLowerCase()}`, status: c.status }))
      setToasts(t => [...t, ...fresh])
      fresh.forEach(f => setTimeout(() => setToasts(t => t.filter(x => x.key !== f.key)), 4200))
    }
  }, [storeKey])

  useEffect(() => {
    let saved: string | null = null
    try { saved = sessionStorage.getItem(storeKey) } catch { /* ignore */ }
    const start = () => api.start(courseId).then(apply).catch(e => setError(e.message))
    if (saved) api.get(saved).then(apply).catch(start)
    else start()
  }, [courseId, storeKey, apply])

  const run: Run = async (b, call, clearText = false) => {
    setBusy(b); setError(null)
    try {
      apply(await call())
      if (clearText) setText('')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(null)
    }
  }

  const newSession = (mode?: string) => run(null, () => api.start(courseId, mode ?? snap?.mode, false))

  return { snap, busy, error, toasts, text, setText, run, newSession }
}
