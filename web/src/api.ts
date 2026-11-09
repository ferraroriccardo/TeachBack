import type { CourseCard, Snapshot } from './types'

async function call<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) {
    let msg = `Error ${res.status}`
    try { msg = (await res.json()).detail ?? msg } catch { /* non-JSON response */ }
    throw new Error(msg)
  }
  return res.json()
}

export const api = {
  courses: () => call<{ mode: string; live_available: boolean; courses: CourseCard[] }>('/courses'),
  start: (course_id: string, mode?: string, resume = true) => call<Snapshot>('/sessions', { course_id, mode, resume }),
  get: (sid: string) => call<Snapshot>(`/sessions/${sid}`),
  explain: (sid: string, text: string) => call<Snapshot>(`/sessions/${sid}/explain`, { text }),
  reply: (sid: string, text: string) => call<Snapshot>(`/sessions/${sid}/reply`, { text }),
  exam: (sid: string, text?: string) => call<Snapshot>(`/sessions/${sid}/exam`, { text }),
  report: (sid: string) => call<Snapshot>(`/sessions/${sid}/report`, {}),
  revise: (sid: string, concept_id: string) => call<Snapshot>(`/sessions/${sid}/revise`, { concept_id }),
  explainAgain: (sid: string) => call<Snapshot>(`/sessions/${sid}/explain-again`, {}),
  challenge: (sid: string) => call<Snapshot>(`/sessions/${sid}/challenge`, {}),
  answer: (sid: string, text?: string) => call<Snapshot>(`/sessions/${sid}/answer`, { text }),
  demo: () => call<{ explanation: string; fix: string }>('/demo'),
}
