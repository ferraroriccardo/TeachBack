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

from teachback.contracts import STATUS_LABEL, Course, GraphAnswer, GraphEdge, GraphNode, GraphView
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
            reason = (f"{c.name} may not click yet because {g.nodes[path[0]]['name']} "
                      f"is still red (prerequisite).")
        nodes.append(GraphNode(c.id, c.name, st, reason, c.layout))
    edges = [GraphEdge(u, v) for u, v in g.edges]
    return GraphView(nodes, edges)


def _source(g: nx.DiGraph, node: str) -> str:
    d = g.nodes[node]
    p = d.get("provenance") or {}
    who = ", ".join(x for x in (p.get("extracted_by") and f"extracted by {p['extracted_by']}",
                                p.get("validated_by") and f"validated by {p['validated_by']}",
                                p.get("date")) if x)
    return f"{d['name']}: {d['slide']}" + (f" ({who})" if who else "")


def _arrow(g: nx.DiGraph, path: list[str]) -> list[str]:
    """[a, b, c] along prerequisite→concept edges, read as 'c requires b requires a'."""
    return [f"{g.nodes[v]['name']} —requires→ {g.nodes[u]['name']}" for u, v in zip(path, path[1:])]


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


_NOT_FOUND = ("The graph does not contain this information. I only know which concepts require which, "
              "which slide they come from and your status on each. Ask the Teacher or your lecturer.")


def ask(course: Course, status: dict, question: str) -> GraphAnswer:
    g = build(course)
    q = _norm(question)
    found = _match_concepts(course, question)
    if not found:
        return GraphAnswer(False, "No concept in the graph matches the question. " + _NOT_FOUND)
    cid = found[0]
    name = g.nodes[cid]["name"]

    # 1) "Why don't I get X / why is it red?"
    if re.search(r"why.*(not|n't|red|yellow|wrong|stuck|click)|how am i doing|status|perche.*(non|ross|giall|torna|sbagli|blocc)|non mi torna", q):
        st = status.get(cid, "non_visto")
        path = _red_ancestor(g, cid, status)
        if path and st == "pronto":
            ans = (f"{name} is “ready” for now, but it requires {g.nodes[path[0]]['name']}, which is "
                   "still red for you: you may be able to apply it without knowing why it works. Review that first.")
            return GraphAnswer(True, ans, _arrow(g, path), [_source(g, n) for n in path])
        if path:
            ans = (f"{name} is “{STATUS_LABEL[st]}”. The most likely reason: it requires "
                   f"{g.nodes[path[0]]['name']}, which is still red for you. Start again from there.")
            return GraphAnswer(True, ans, _arrow(g, path), [_source(g, n) for n in path])
        if st == RED:
            ans = (f"{name} is red, but its prerequisites are not: the gap is in "
                   f"{name} itself. Reread {g.nodes[cid]['slide']} and re-explain it to the Sub-student.")
            return GraphAnswer(True, ans, [f"{name} (status: not yet)"], [_source(g, cid)])
        ans = f"{name} is “{STATUS_LABEL[st]}” and none of its prerequisites is red."
        return GraphAnswer(True, ans, [f"{name} (status: {STATUS_LABEL[st]})"], [_source(g, cid)])

    # 2) "What do I need to know before X?"
    if re.search(r"before|prerequisit|need to know|require|basics|prima|serve sapere|devo sapere|richied", q):
        anc = [n for n in nx.topological_sort(g) if n in nx.ancestors(g, cid)]
        if not anc:
            return GraphAnswer(True, f"{name} has no prerequisites in the graph: it is a starting point.",
                               [], [_source(g, cid)])
        order = ", ".join(f"{g.nodes[n]['name']} ({STATUS_LABEL[status.get(n, 'non_visto')]})" for n in anc)
        path = []
        for n in anc:
            path += _arrow(g, nx.shortest_path(g, n, cid))
        return GraphAnswer(True, f"Before {name} you need, in this order: {order}.",
                           list(dict.fromkeys(path)), [_source(g, n) for n in anc + [cid]])

    # 3) "What does X unlock?"
    if re.search(r"unlock|after|what is .* for|used for|depend on|needs it|sblocca|a cosa serve|serve per", q):
        desc = [n for n in nx.topological_sort(g) if n in nx.descendants(g, cid)]
        if not desc:
            return GraphAnswer(True, f"No concept in the graph requires {name}.", [], [_source(g, cid)])
        path = [a for n in desc for a in _arrow(g, nx.shortest_path(g, cid, n))]
        return GraphAnswer(True, f"{name} is needed for: " + ", ".join(g.nodes[n]["name"] for n in desc) + ".",
                           list(dict.fromkeys(path)), [_source(g, n) for n in [cid] + desc])

    return GraphAnswer(False, f"I found {name} in the graph, but the question is not about prerequisites, "
                              f"dependencies or your status. " + _NOT_FOUND, [], [_source(g, cid)])
