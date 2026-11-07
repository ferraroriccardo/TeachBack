"""Grafo di conoscenza (livello 3B) su NetworkX.

Ontologia (vedi docs/ONTOLOGY.md):
  Classi: Concept, Slide (fonte), Student (lo stato è una proprietà della coppia Student-Concept)
  Relazioni: Concept --requires--> Concept, Concept --taughtIn--> Slide, Student --hasStatus--> Concept

L'agente sul grafo risponde SOLO da nodi e archi: mostra il percorso, cita le fonti e
dice chiaramente quando il grafo non contiene l'informazione.
"""
from __future__ import annotations

import re

import networkx as nx

from teachback.contracts import Course, GraphAnswer, GraphEdge, GraphNode, GraphView
from teachback.guardrails import _norm

RED = "non_ancora"


def build(course: Course) -> nx.DiGraph:
    """Arco prerequisito → concetto (cioè: concetto RICHIEDE prerequisito)."""
    g = nx.DiGraph()
    for c in course.concepts:
        g.add_node(c.id, name=c.name, slide=c.slide_ref, provenance=c.provenance)
    for c in course.concepts:
        for p in c.prerequisites:
            g.add_edge(p, c.id, relation="requires")
    return g


def _red_ancestor(g: nx.DiGraph, node: str, status: dict) -> list[str] | None:
    """Percorso più corto da un prerequisito rosso al nodo (lista di id), se esiste."""
    best = None
    for anc in nx.ancestors(g, node):
        if status.get(anc) == RED:
            path = nx.shortest_path(g, anc, node)
            if best is None or len(path) < len(best):
                best = path
    return best


def view(course: Course, status: dict) -> GraphView:
    g = build(course)
    nodes = []
    for c in course.concepts:
        st = status.get(c.id, "non_visto")
        reason = None
        path = _red_ancestor(g, c.id, status) if st != "pronto" else None
        if path:
            reason = (f"{c.name} può non tornarti perché {g.nodes[path[0]]['name']} "
                      f"è ancora rosso (prerequisito).")
        nodes.append(GraphNode(c.id, c.name, st, reason, c.layout))
    edges = [GraphEdge(u, v) for u, v in g.edges]
    return GraphView(nodes, edges)


def _source(g: nx.DiGraph, node: str) -> str:
    d = g.nodes[node]
    p = d.get("provenance") or {}
    who = ", ".join(x for x in (p.get("extracted_by") and f"estratto da {p['extracted_by']}",
                                p.get("validated_by") and f"convalidato da {p['validated_by']}",
                                p.get("date")) if x)
    return f"{d['name']}: {d['slide']}" + (f" ({who})" if who else "")


def _arrow(g: nx.DiGraph, path: list[str]) -> list[str]:
    """[a, b, c] lungo gli archi prerequisito→concetto, letto come 'c richiede b richiede a'."""
    return [f"{g.nodes[v]['name']} —richiede→ {g.nodes[u]['name']}" for u, v in zip(path, path[1:])]


def _match_concepts(course: Course, question: str) -> list[str]:
    q = _norm(question)
    hits = []
    for c in course.concepts:
        for alias in sorted(c.aliases + [c.name], key=len, reverse=True):
            m = re.search(r"\b" + re.escape(_norm(alias)) + r"\b", q)
            if m:
                hits.append((m.start(), -len(alias), c.id))
                break
    return [cid for _, _, cid in sorted(hits)]


_NOT_FOUND = ("Il grafo non contiene questa informazione. So solo quali concetti richiedono quali altri, "
              "da quale slide vengono e il tuo stato su ciascuno. Chiedilo all'Insegnante o al docente.")


def ask(course: Course, status: dict, question: str) -> GraphAnswer:
    g = build(course)
    q = _norm(question)
    found = _match_concepts(course, question)
    if not found:
        return GraphAnswer(False, "Nel grafo non c'è nessun concetto che corrisponda alla domanda. " + _NOT_FOUND)
    cid = found[0]
    name = g.nodes[cid]["name"]

    # 1) "Perché X non mi torna / è rosso?"
    if re.search(r"perche.*(non|ross|giall|torna|sbagli|blocc)|non mi torna|come sono messo|stato", q):
        st = status.get(cid, "non_visto")
        path = _red_ancestor(g, cid, status)
        if path and st == "pronto":
            ans = (f"{name} per ora è «pronto», ma richiede {g.nodes[path[0]]['name']}, che per te è "
                   "ancora rosso: potresti saperlo applicare senza sapere perché funziona. Ripassa prima quello.")
            return GraphAnswer(True, ans, _arrow(g, path), [_source(g, n) for n in path])
        if path:
            ans = (f"{name} è «{st.replace('_', ' ')}». Il motivo più probabile: richiede "
                   f"{g.nodes[path[0]]['name']}, che per te è ancora rosso. Riparti da lì.")
            return GraphAnswer(True, ans, _arrow(g, path), [_source(g, n) for n in path])
        if st == RED:
            ans = (f"{name} è rosso, ma i suoi prerequisiti non sono rossi: la lacuna è proprio su "
                   f"{name}. Rileggi {g.nodes[cid]['slide']} e rispiegalo al Sotto-studente.")
            return GraphAnswer(True, ans, [f"{name} (stato: non ancora)"], [_source(g, cid)])
        ans = f"{name} è «{st.replace('_', ' ')}» e nessun suo prerequisito è rosso."
        return GraphAnswer(True, ans, [f"{name} (stato: {st.replace('_', ' ')})"], [_source(g, cid)])

    # 2) "Cosa devo sapere prima di X?"
    if re.search(r"prima|prerequisit|serve sapere|devo sapere|richied|basi|propedeut", q):
        anc = [n for n in nx.topological_sort(g) if n in nx.ancestors(g, cid)]
        if not anc:
            return GraphAnswer(True, f"{name} non ha prerequisiti nel grafo: è un punto di partenza.",
                               [], [_source(g, cid)])
        order = ", ".join(f"{g.nodes[n]['name']} ({status.get(n, 'non_visto').replace('_', ' ')})" for n in anc)
        path = []
        for n in anc:
            path += _arrow(g, nx.shortest_path(g, n, cid))
        return GraphAnswer(True, f"Prima di {name} servono, in quest'ordine: {order}.",
                           list(dict.fromkeys(path)), [_source(g, n) for n in anc + [cid]])

    # 3) "Cosa sblocca X?"
    if re.search(r"sblocca|dopo|a cosa serve|serve per|dipende da lui|chi lo usa", q):
        desc = [n for n in nx.topological_sort(g) if n in nx.descendants(g, cid)]
        if not desc:
            return GraphAnswer(True, f"Nel grafo nessun concetto richiede {name}.", [], [_source(g, cid)])
        path = [a for n in desc for a in _arrow(g, nx.shortest_path(g, cid, n))]
        return GraphAnswer(True, f"{name} serve per: " + ", ".join(g.nodes[n]["name"] for n in desc) + ".",
                           list(dict.fromkeys(path)), [_source(g, n) for n in [cid] + desc])

    return GraphAnswer(False, f"Ho trovato {name} nel grafo, ma la domanda non riguarda prerequisiti, "
                              f"dipendenze o il tuo stato. " + _NOT_FOUND, [], [_source(g, cid)])
