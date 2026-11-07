"""Componenti grafici ricalcati sui mockup in static/ (stepper, chat, grafo, card)."""
from __future__ import annotations

import html
import re

import streamlit as st

from teachback.contracts import Claim, GraphView, SubStudentReply

STATUS_STYLE = {   # fill, bordo, etichetta
    "pronto": ("#8fd694", "#3f9d4a", "Pronto"),
    "quasi": ("#ffe08a", "#d9a400", "Quasi"),
    "non_ancora": ("#f59a9a", "#d64545", "Non ancora"),
    "non_visto": ("#e8ecf2", "#a0a9b8", "Non visto"),
}

STEPS = [("spiego", "Io spiego"), ("domande", "Domande"), ("prova", "Prova d'esame"),
         ("resoconto", "Resoconto"), ("sfide", "Sfide"), ("esame", "Esame interno")]

AVATAR = {"sotto_studente": "🐣", "insegnante": "🦉", "studente": "🧑‍🎓"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.6rem; max-width: 1400px; }
h1, h2, h3 { color: #14213d; letter-spacing: -0.01em; }
.tb-brand { display:flex; align-items:center; gap:.55rem; font-weight:800; font-size:1.55rem; color:#14213d; margin-bottom:.4rem; }
.tb-brand .logo { background:#2f6fdf; color:white; border-radius:10px; width:38px; height:38px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; }
.tb-card { background:#fff; border:1px solid #dbe5f1; border-radius:16px; padding:1rem 1.2rem; box-shadow:0 1px 2px rgba(20,33,61,.04); }
.tb-card-blue { border:1.5px solid #8db3ec; }
.tb-card-head { display:flex; align-items:center; gap:.6rem; font-weight:700; font-size:1.15rem; background:#e3eefc; margin:0 0 .6rem 0; padding:.6rem 1rem; border-radius:12px; }.tb-card-head .ava { font-size:1.6rem; }
.tb-pill { display:inline-block; border-radius:999px; padding:.15rem .7rem; font-size:.82rem; font-weight:600; }
.tb-legend { display:flex; border-radius:10px; overflow:hidden; font-size:.85rem; font-weight:600; }
.tb-legend span { padding:.3rem .7rem; }
/* stepper a frecce come nel mockup */
.tb-steps { display:flex; gap:4px; margin:.3rem 0 1.1rem 0; }
.tb-step { flex:1; text-align:center; padding:.55rem .4rem .55rem 1.1rem; font-size:.88rem; font-weight:600; color:#4b5563; background:#e5e7eb;
  clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 50%, calc(100% - 14px) 100%, 0 100%, 14px 50%); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tb-step:first-child { clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 50%, calc(100% - 14px) 100%, 0 100%); padding-left:.6rem; }
.tb-step.done { background:#cfe0fa; color:#1e4fa8; }
.tb-step.active { background:#2f6fdf; color:#fff; }
/* chat */
.tb-msg { display:flex; gap:.6rem; margin:.55rem 0; align-items:flex-start; }
.tb-msg .ava { font-size:1.7rem; line-height:1; margin-top:.15rem; }
.tb-bubble { border-radius:16px; padding:.7rem .95rem; max-width:82%; line-height:1.45; font-size:.97rem; }
.tb-msg.me { justify-content:flex-end; }
.tb-msg.me .tb-bubble { background:#dbeafe; color:#14213d; }
.tb-msg.sub .tb-bubble { background:#eef0f3; }
.tb-msg.teach .tb-bubble { background:#fff7e0; border:1px solid #f3dc9b; }
.tb-exam { text-align:center; margin:.8rem 0; }
.tb-exam span { background:#14213d; color:#fff; border-radius:10px; padding:.45rem .8rem; font-size:.9rem; display:inline-block; max-width:92%; }
.tb-cite { background:#2f6fdf; color:#fff; border-radius:6px; padding:0 .35rem; font-size:.78rem; font-weight:700; margin-left:.15rem; }
/* affermazioni */
.tb-claim { padding:.35rem .55rem; border-radius:8px; margin:.2rem 0; font-size:.92rem; }
.tb-claim b { color:#2f6fdf; margin-right:.35rem; }
.tb-claim.cited { background:#e3eefc; border-left:4px solid #2f6fdf; }
.tb-claim.wrong { background:#fde2e2; border-left:4px solid #d64545; }
.tb-claim .tag { float:right; font-size:.74rem; font-weight:700; border-radius:6px; padding:0 .4rem; margin-left:.4rem; }
.tb-claim.cited .tag { background:#2f6fdf; color:#fff; }
.tb-claim.wrong .tag { background:#d64545; color:#fff; }
/* guida della fase */
.tb-guide { display:flex; gap:.75rem; align-items:flex-start; background:#f1f6ff; border:1px solid #cfe0fa; border-radius:12px; padding:.65rem .9rem; margin:-.4rem 0 1rem 0; font-size:.95rem; }
.tb-guide .ico { font-size:1.3rem; line-height:1.2; }
.tb-guide b { color:#1e4fa8; }
/* messaggi lunghi richiudibili */
.tb-bubble details summary { cursor:pointer; list-style:none; }
.tb-bubble details summary::-webkit-details-marker { display:none; }
.tb-bubble details summary .more { color:#2f6fdf; font-weight:600; white-space:nowrap; }
.tb-bubble details[open] summary { display:none; }
/* esito della prova */
.tb-verdict { border-radius:14px; padding:.8rem 1rem; margin:.6rem 0 .2rem 0; display:flex; gap:.7rem; align-items:flex-start; }
.tb-verdict .ico { font-size:1.6rem; line-height:1.1; }
.tb-dots { letter-spacing:.25rem; font-size:1.05rem; color:#d9a400; }
.tb-tip { color:#4b5563; font-size:.9rem; margin:.4rem 0 .3rem 2.6rem; padding-left:1.1rem; }
.tb-tip li { margin:.1rem 0; }
/* resoconto (mockup Insegnante AI) */
.tb-sec { font-weight:800; font-size:.86rem; letter-spacing:.03em; color:#1f2937; margin:1rem 0 .4rem 0; text-transform:uppercase; }
.tb-box { border-radius:14px; padding:.85rem 1.1rem; margin-bottom:.6rem; }
.tb-box h4 { margin:0 0 .35rem 0; font-size:1.08rem; }
.tb-red { background:#fde2e2; border:2px solid #e05252; }
.tb-yellow { background:#fff4cc; border:2px solid #e8b931; }
.tb-green { background:#e3f6e6; border:2px solid #57b366; }
.tb-owl { display:flex; gap:.8rem; align-items:center; background:#fff; border:1px solid #dbe5f1; border-radius:14px; padding:.7rem 1rem; }
.tb-owl .ava { font-size:2.6rem; background:#5fb3a8; border-radius:50%; width:64px; height:64px; display:flex; align-items:center; justify-content:center; }
/* dashboard */
.tb-banner { background:#ffe9d6; border:1.5px solid #f2a65a; border-radius:14px; padding:.9rem 1.1rem; display:flex; gap:.9rem; align-items:center; }
.tb-banner .ico { font-size:1.8rem; }
.tb-course { background:#fff; border:1px solid #dbe5f1; border-radius:16px; overflow:hidden; }
.tb-course .top { height:84px; display:flex; justify-content:space-between; align-items:flex-start; padding:.8rem 1rem; font-size:1.7rem; }
.tb-course .body { padding:.9rem 1rem 1rem 1rem; }
.tb-course .title { font-weight:700; font-size:1.15rem; margin-bottom:.4rem; }
.tb-bar { background:#e5e7eb; border-radius:999px; height:10px; overflow:hidden; margin-top:.35rem; }
.tb-bar > div { height:100%; border-radius:999px; }
.tb-mock { background:repeating-linear-gradient(45deg,#fff7e0,#fff7e0 10px,#fff1c7 10px,#fff1c7 20px); border:1.5px dashed #d9a400; border-radius:12px; padding:.6rem .9rem; font-weight:600; color:#7a5b00; }
.tb-privacy { background:#dbe8ff; color:#1e4fa8; border-radius:10px; padding:.4rem .8rem; font-weight:600; display:inline-block; }
.tb-path { font-family: ui-monospace, monospace; font-size:.88rem; background:#f1f5fb; border-radius:8px; padding:.3rem .6rem; margin:.2rem 0; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def esc(text: str) -> str:
    return html.escape(text or "")


def brand() -> None:
    st.markdown('<div class="tb-brand"><div class="logo">🎓</div>TeachBack</div>', unsafe_allow_html=True)


def stepper(phase: str) -> None:
    idx = [p for p, _ in STEPS].index(phase) if phase in [p for p, _ in STEPS] else 0
    parts = []
    for i, (_, label) in enumerate(STEPS):
        cls = "active" if i == idx else ("done" if i < idx else "")
        parts.append(f'<div class="tb-step {cls}">{i + 1} · {label}</div>')
    st.markdown('<div class="tb-steps">' + "".join(parts) + "</div>", unsafe_allow_html=True)


def guide(icon: str, html_text: str) -> None:
    """Una riga che dice cosa sta succedendo e cosa fare adesso."""
    st.markdown(f'<div class="tb-guide"><div class="ico">{icon}</div><div>{html_text}</div></div>',
                unsafe_allow_html=True)


def _foldable(t: str, limit: int = 260) -> str:
    """Testo già escapato: oltre `limit` caratteri si richiude, con "mostra tutto"."""
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0]
    return (f'<details><summary>{cut}… <span class="more">mostra tutto</span></summary>{t}</details>')


def _cites_to_badges(text: str) -> str:
    return re.sub(r"\(aff\. ([\d, ]+)\)", lambda m: "".join(f'<span class="tb-cite">{n.strip()}</span>'
                                                              for n in m.group(1).split(",")), text)


def chat(messages: list[tuple[str, str]], recent: int | None = None) -> None:
    """Bolle come nel mockup. Con `recent` mostra gli ultimi messaggi e mette i precedenti in un riquadro chiuso."""
    if recent and len(messages) > recent:
        with st.expander(f"Messaggi precedenti ({len(messages) - recent})"):
            chat(messages[:-recent])
        messages = messages[-recent:]
    out = []
    for role, text in messages:
        t = esc(text)
        if role == "esame":
            out.append(f'<div class="tb-exam"><span>📝 Domanda d\'esame: {t}</span></div>')
        elif role == "studente":
            out.append(f'<div class="tb-msg me"><div class="tb-bubble">{_foldable(t)}</div><div class="ava">{AVATAR["studente"]}</div></div>')
        elif role == "sotto_studente":
            out.append(f'<div class="tb-msg sub"><div class="ava">🐣</div><div class="tb-bubble">{_cites_to_badges(t)}</div></div>')
        else:
            out.append(f'<div class="tb-msg teach"><div class="ava">🦉</div><div class="tb-bubble">{t}</div></div>')
    if not out:
        out.append('<div style="color:#6b7280;padding:1rem 0">Il Sotto-studente non sa ancora niente. '
                   'Spiegagli l\'argomento: imparerà solo da te.</div>')
    st.markdown("".join(out), unsafe_allow_html=True)


def claims_panel(claims: list[Claim], reply: SubStudentReply | None, wrong: dict[int, str] | None = None) -> None:
    """Blu = citata nell'ultima risposta del Sotto-studente; rosso = l'Insegnante l'ha trovata in contrasto con una slide."""
    cited = {i for s in (reply.sentences if reply else []) for i in s.claim_ids}
    wrong = wrong or {}
    if not claims:
        st.caption("Ancora vuoto: il Sotto-studente non sa niente finché non glielo spieghi.")
        return
    rows = []
    for c in claims:
        if c.n in wrong:
            cls, tag = "wrong", f'<span class="tag">✗ {esc(wrong[c.n])}</span>'
        elif c.n in cited:
            cls, tag = "cited", '<span class="tag">citata</span>'
        else:
            cls, tag = "", ""
        rows.append(f'<div class="tb-claim {cls}">{tag}<b>{c.n}</b>{esc(c.text)}</div>')
    st.markdown("".join(rows), unsafe_allow_html=True)
    if reply and reply.discarded:
        st.caption(f"🛡️ Controllo citazioni: {reply.discarded} frase/i scartate perché senza un'affermazione che le sostenga.")


def legend(view: GraphView) -> None:
    counts = {k: sum(1 for n in view.nodes if n.status == k) for k in STATUS_STYLE}
    sym = {"pronto": "✓", "quasi": "~", "non_ancora": "✗", "non_visto": "?"}
    spans = "".join(f'<span style="background:{STATUS_STYLE[k][0]};white-space:nowrap">{sym[k]} {STATUS_STYLE[k][2]}: {counts[k]}</span>'
                    for k in ("pronto", "quasi", "non_ancora", "non_visto"))
    st.markdown(f'<div class="tb-legend" style="width:fit-content">{spans}</div>', unsafe_allow_html=True)


def _wrap(label: str, width: int = 14) -> str:
    words, lines, cur = label.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return "\\n".join(lines)


def graph(view: GraphView) -> None:
    """Cerchi colorati come nel mockup; posizioni fisse se il corso le suggerisce, altrimenti layout automatico."""
    pinned = all(n.layout for n in view.nodes)
    head = ('digraph G { layout=neato; splines=true; bgcolor="transparent"; overlap=false;' if pinned
            else 'digraph G { rankdir=LR; bgcolor="transparent"; nodesep=0.45; ranksep=0.55;')
    dot = [head,
           'node [shape=circle, style="filled", fixedsize=true, width=1.3, fontname="Helvetica", fontsize=15, penwidth=2.6];',
           'edge [color="#8a94a6", penwidth=2, arrowsize=0.9];']
    k = 0.62  # comprime le posizioni: nodi più grandi rispetto al disegno, testo leggibile
    symbol = {"pronto": "✓", "quasi": "~", "non_ancora": "✗", "non_visto": "?"}
    for n in view.nodes:
        fill, border, name = STATUS_STYLE[n.status]
        label = _wrap(n.label.replace('"', "'"), 11) + f"\\n{symbol[n.status]}"
        tip = f"{n.label}: {name}" + (f" · {n.reason}" if n.reason else "")
        pos = f', pos="{n.layout[0] * k:.2f},{n.layout[1] * k:.2f}!"' if pinned else ""
        dot.append(f'"{n.id}" [label="{label}", tooltip="{tip.replace(chr(34), chr(39))}", '
                   f'fillcolor="{fill}", color="{border}"{pos}];')
    for e in view.edges:
        dot.append(f'"{e.source}" -> "{e.target}";')
    dot.append("}")
    st.graphviz_chart("\n".join(dot), width="stretch")


def card_head(icon: str, title: str, right_html: str = "") -> None:
    st.markdown(f'<div class="tb-card-head" style="justify-content:space-between"><div style="display:flex;gap:.6rem;align-items:center">'
                f'<span class="ava">{icon}</span>{esc(title)}</div><div>{right_html}</div></div>', unsafe_allow_html=True)


def mock_banner(text: str) -> None:
    st.markdown(f'<div class="tb-mock">🧪 Mockup statico dichiarato · {esc(text)}</div>', unsafe_allow_html=True)


def mode_badge(mode: str) -> str:
    if mode == "live":
        return '<span class="tb-pill" style="background:#dcfce7;color:#166534">● Live · Claude</span>'
    return '<span class="tb-pill" style="background:#fef3c7;color:#92400e">● Copione offline (senza AI)</span>'
