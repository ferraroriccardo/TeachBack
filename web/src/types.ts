export type Status = 'pronto' | 'quasi' | 'non_ancora' | 'non_visto'
export type Phase = 'spiego' | 'domande' | 'prova' | 'resoconto' | 'sfide' | 'esame'

export interface Claim { n: number; text: string }
export interface ChatMsg { role: 'studente' | 'sotto_studente' | 'insegnante' | 'esame'; text: string }
export interface GraphNode { id: string; label: string; status: Status; reason: string | null; layout: number[] | null }
export interface GraphEdge { source: string; target: string }
export interface Feedback { concept_id: string; where: string; slide_ref: string; why: string | null; claim_ids: number[] }
export interface Report {
  explained: string[]; missing: string[]; retry: boolean; feedback: Feedback[]
  discrepancies: { source: string; note: string }[]; named_only: string[]; summary: string
}
export interface Snapshot {
  id: string
  mode: 'live' | 'offline'
  live_available: boolean
  phase: Phase
  focus: string | null
  course: { id: string; title: string; official: boolean; exam_questions: string[]; concepts: { id: string; name: string; slide_ref: string }[] }
  claims: Claim[]
  chat: ChatMsg[]
  statuses: Record<string, Status>
  graph: { nodes: GraphNode[]; edges: GraphEdge[] }
  reply: { kind: 'domanda' | 'risposta' | 'blocco' | 'rifiuto'; text: string; discarded: number; copied: boolean; cited: number[] } | null
  report: Report | null
  challenge: { id: string; concept_id: string; question: string; kind: 'sfida' | 'rispiega'; hints_used: number; closed: boolean } | null
  step: { level: 'corretta' | 'sbagliata' | 'indizio_1' | 'indizio_2' | 'soluzione'; text: string; new_status: Status | null } | null
  changes: { id: string; name: string; status: Status }[]
}
export interface CourseCard {
  id: string; title: string; subtitle: string; official: boolean; example: boolean
  concepts: number; ready: number
  statuses?: Record<string, Status>; names?: Record<string, string>
  reviews?: { concept_id: string; name: string; status: Status; due: string; action: string }[]
}
