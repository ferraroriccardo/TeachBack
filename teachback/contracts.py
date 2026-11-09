"""Contratto tra backend (teachback/) e interfaccia (server/ → web/).

L'interfaccia importa SOLO da qui e dal motore restituito da `teachback.get_engine()`.
Regola: si aggiungono campi con un default, non si rinomina e non si toglie nulla.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# --- Vocabolario -------------------------------------------------------------

ConceptStatus = Literal["pronto", "quasi", "non_ancora", "non_visto"]
Phase = Literal["spiego", "domande", "prova", "resoconto", "sfide", "esame"]
ReplyKind = Literal["domanda", "risposta", "blocco", "rifiuto"]

STATUS_LABEL: dict[str, str] = {
    "pronto": "ready", "quasi": "almost", "non_ancora": "not yet", "non_visto": "not seen",
}


# --- Corso e grafo -----------------------------------------------------------

@dataclass
class Concept:
    id: str
    name: str
    prerequisites: list[str]          # id dei prerequisiti (relazione: questo concetto RICHIEDE quelli)
    slide_ref: str                    # es. "Slide 13 - Catalizzatori ed equilibrio"
    validated: bool = True            # False nei corsi non ufficiali ("non convalidato")
    aliases: list[str] = field(default_factory=list)
    provenance: dict = field(default_factory=dict)   # chi l'ha estratto/convalidato e quando
    layout: list[float] | None = None                # posizione suggerita nel disegno del grafo (solo UI)


@dataclass
class Course:
    id: str
    title: str
    official: bool
    concepts: list[Concept]
    exam_questions: list[str] = field(default_factory=list)

    def concept(self, concept_id: str) -> Concept | None:
        return next((c for c in self.concepts if c.id == concept_id), None)


@dataclass
class GraphNode:
    id: str
    label: str
    status: ConceptStatus
    reason: str | None = None         # es. "Le Châtelier non ti torna perché Kc è ancora rossa"
    layout: list[float] | None = None


@dataclass
class GraphEdge:
    source: str                       # prerequisito
    target: str                       # concetto che lo richiede


@dataclass
class GraphView:
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@dataclass
class GraphAnswer:
    """Risposta dell'agente sul grafo (livello 3B): sempre con percorso e fonti."""
    found: bool
    answer: str
    path: list[str] = field(default_factory=list)      # es. "Catalizzatore —richiede→ Le Châtelier"
    sources: list[str] = field(default_factory=list)   # slide + provenienza dei fatti usati


# --- Sotto-studente -----------------------------------------------------------

@dataclass
class Claim:
    n: int                            # numero mostrato a schermo ("affermazione 4")
    text: str


@dataclass
class CitedSentence:
    text: str
    claim_ids: list[int]


@dataclass
class SubStudentReply:
    kind: ReplyKind
    text: str                         # testo da mostrare in chat
    sentences: list[CitedSentence] = field(default_factory=list)
    discarded: int = 0                # frasi scartate dal controllo citazioni
    copied_from_slides: bool = False  # la spiegazione era quasi identica alle slide


# --- Insegnante ---------------------------------------------------------------

@dataclass
class Feedback:
    concept_id: str
    where: str                        # livello 1: DOVE sbagli (con la slide)
    slide_ref: str
    why: str | None = None            # livello 2: PERCHÉ (la UI lo mostra solo su richiesta)
    claim_ids: list[int] = field(default_factory=list)   # affermazioni dello studente su cui si basa il giudizio


@dataclass
class Discrepancy:
    source: str                       # es. "Slide 12"
    note: str                         # sempre "Discrepanza con [fonte], chiedi al docente: ..."


@dataclass
class TeacherReport:
    explained: list[str]              # concetti spiegati con un perché o un esempio
    missing: list[str]                # concetti chiave non spiegati
    retry: bool                       # True se sotto 1/3 dei concetti chiave: si riprova
    feedback: list[Feedback] = field(default_factory=list)
    discrepancies: list[Discrepancy] = field(default_factory=list)
    named_only: list[str] = field(default_factory=list)   # nominati senza perché né esempio
    summary: str = ""


@dataclass
class Challenge:
    id: str
    concept_id: str
    question: str                     # la soluzione NON è qui: resta in Session.hidden
    kind: Literal["sfida", "rispiega"] = "sfida"


@dataclass
class ChallengeStep:
    level: Literal["corretta", "sbagliata", "indizio_1", "indizio_2", "soluzione"]
    text: str
    new_status: ConceptStatus | None = None


# --- Docente e ripasso ------------------------------------------------------------

@dataclass
class WeeklyMessage:
    course_id: str
    available: bool                   # False sotto i 10 studenti attivi o se il corso non è ufficiale
    active_students: int
    top_errors: list[tuple[str, str, int]] = field(default_factory=list)   # (concetto, slide, n. studenti)
    discrepancies: list[Discrepancy] = field(default_factory=list)
    reason: str = ""
    synthetic: bool = False           # True se i dati della classe sono sintetici (demo)
    disclaimer: str = ("The app is used mostly by the most motivated students: "
                       "the data does not represent the whole class.")


@dataclass
class ReviewItem:
    concept_id: str
    name: str
    status: ConceptStatus
    due: str                          # data ISO
    interval_days: int
    action: Literal["sfida", "riapri_loop"] = "sfida"


# --- Sessione (vive in memoria nel server API) ---------------------------

@dataclass
class Session:
    course_id: str
    topic_id: str
    student_id: str = "demo"
    phase: Phase = "spiego"
    claims: list[Claim] = field(default_factory=list)
    chat: list[tuple[str, str]] = field(default_factory=list)   # (ruolo, testo) per la UI
    concept_status: dict[str, ConceptStatus] = field(default_factory=dict)
    log: list[dict] = field(default_factory=list)               # ogni passo, per eval ed esempi
    hidden: dict = field(default_factory=dict)                  # soluzioni, indizi, spiegazioni coperte: MAI renderizzato
    llm_calls: int = 0
