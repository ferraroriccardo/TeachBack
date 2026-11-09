# TeachBack

> **Don't reread it. Explain it.**
> You study by explaining to an AI that knows nothing: it learns only from you, and if you taught it wrong, it gets the exercise wrong right in front of you.

Built at the **Reply Student Tech Clash 2026 — AI on Campus** hackathon (level 2, *Path B · code*; level 3B knowledge graph and 3C launch campaign).

It is based on *learning by teaching*: the best way to learn is to teach. Two agents:
- the 🐣 **Sub-student** knows only what the student explains to it, asks questions, and every sentence it says cites the claim it comes from;
- the 🦉 **Teacher** knows the course slides, corrects you by saying first *where* you went wrong and then *why*, sets challenges with hints, and colours the concept map.

Demo case: **General Chemistry I, chemical equilibrium and Le Châtelier's principle**, with the classic mistake *"the catalyst shifts the equilibrium"*.

---

## Quick start

You need Python 3.10 or later. The frontend is already built in `web/dist`, so **you don't need Node** to try the app.

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt     # Windows
.venv/bin/pip install -r requirements.txt         # macOS / Linux

cp .env.example .env      # optional: add ANTHROPIC_API_KEY for the Live engine
```

Run it (from the repository root):

```bash
.venv\Scripts\python -m server      # Windows
.venv/bin/python -m server          # macOS / Linux
```

Then open <http://localhost:8000>. The pitch deck is at <http://localhost:8000/presentation/>.

**Two engines, same app.**
- **Live · Claude**: both agents run on Claude via the API. Needs `ANTHROPIC_API_KEY` in `.env`. With a key, the badge in the top right switches between engines.
- **Offline**: rule-based agents, no network and no key. The orchestrator, guardrails, states, hints and graph are the **same code**. It is the backup demo if the network goes down, and the basis for the tests.

### Frontend development

The frontend is React + TypeScript (Vite). To change it you need Node 20 or later:

```bash
python -m server                         # API on :8000 (terminal 1)
cd web && npm install && npm run dev     # UI on :5173 with hot reload (terminal 2)
npm run build                            # rebuilds web/dist, served by python -m server
```

---

## The interface

Two screens.

**Course dashboard.** Each course shows its concepts with a coloured dot per status (*ready*, *almost*, *not yet*, *not seen*), progress, and today's reviews. The chemistry course is the real one; the other two are labelled examples and cannot be opened.

**The loop.** On the left, the conversation with the Sub-student and the Teacher. On the right, the **concept map**, which colours in as you study, and **what the Sub-student knows**: the numbered claims extracted from your explanations, highlighted in blue when it uses them and in red when they contradict the slides. The steps are at the top: *Explain → Questions → Exam attempt → Correction → Challenges*. The controls at the bottom change with the step.

### Demo script (2 minutes)

1. Open **General Chemistry I** and press **Use the demo explanation**: it contains the mistake *"the catalyst also shifts the equilibrium towards the products"*. Then **Teach the Sub-student**.
2. The Sub-student asks a question: you can answer it, or **Let it try the question** about the catalyst. It answers *"the amount of NH3 increases"*, citing claim 3.
3. **Ask the Teacher for a correction**. A red *Catalyst* card appears with Slide 13, *Why?* as the second level, and the node turns red on the map.
4. **Re-explain this concept**: the Sub-student forgets the wrong claim. **Use the demo correction**, teach it, let it retry the question and ask for a correction again: now it answers *"does not change"* and the catalyst turns green.
5. **Go to the Teacher's challenges**: answer, or ask for a hint (at most two, then the solution). **Skip** is always available.

Every status change shows up as a notification in the bottom right. **New session** resets everything.

---

## Models, libraries, frameworks

| What | Choice | Why |
| --- | --- | --- |
| Teacher | **Claude Opus 5.5** (`claude-opus-5-5`); effort `medium` for the correction, `low` for challenges and hints | Judgement against the course material |
| Sub-student and claim extraction | **Claude Haiku 5.5** (`claude-haiku-5-5`), effort `low` | Cheaper. A less capable model "fills in the gaps" less on its own |
| SDK | `anthropic` (official) | **Structured outputs**: every response is JSON validated against a schema |
| Model refusals | Server-side fallback (`fallbacks: "default"`) on Opus calls | If a safety filter refuses by mistake, the request is retried on a backup model |
| API | FastAPI + Uvicorn (`server/`) | Exposes the engine as JSON; challenge solutions never leave the server |
| Interface | React 19 + TypeScript + Vite (`web/`) | Dashboard and loop; fonts bundled, works offline too |
| Graph | NetworkX (backend) + SVG (frontend) | Prerequisites, concept status, paths |
| Memory | SQLite (`data/teachback.db`, created automatically) | Status of each concept per student, and review dates |
| Tests | pytest + FastAPI TestClient | 54 offline tests, plus 3 optional ones against the real model |

Models can be changed in `.env` (`TEACHBACK_TEACHER_MODEL`, `TEACHBACK_SUBSTUDENT_MODEL`). No training: pre-trained models only.

---

## Custom logic (the heart of the project)

Full description in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (in Italian). In short:

1. **The Sub-student really doesn't know.** The explanation is turned into a numbered list of claims ([teachback/agents/llm_backend.py](teachback/agents/llm_backend.py)). The Sub-student receives **only** those, never the slides; a test checks this. Every sentence must cite the numbers of the claims it uses.
2. **Citation check in code** ([teachback/guardrails.py](teachback/guardrails.py)). It discards sentences with no citation, with citations that don't exist, or with citations that are unrelated. If nothing is left, the Sub-student **gets stuck** ("I'm stuck here: you didn't tell me…") instead of making things up.
3. **More guardrails in code**:
   - *"you tell me"* gets a deterministic refusal, with no model call;
   - an explanation copied from the slides is detected (trigram similarity ≥ 60%) and the Sub-student asks for an example of your own;
   - uploaded material is data, never an instruction: lines that look like hidden instructions are removed;
   - discrepancies in the material are always phrased as *"Discrepancy with [source], ask your lecturer"*.
4. **Threshold-based correction** ([teachback/engine.py](teachback/engine.py)). Only concepts explained with a why or an example count, not those merely named.
   - Below a third of the key concepts you try again, and the app only says what is missing.
   - Above the threshold, the Teacher says first *where* (with the slide, which the code adds, not the model) and then *why*, on request.
5. **Challenges** with the ladder *first hint → second hint → solution*.
   - **"Explain it yourself" rule**: after another question, you re-explain on a different case. During the re-explanation the solution is **removed from the page** and comes back at the end.
   - **"Skip"** is always available: skipping leaves the concept red.
6. **Concept states**: *ready*, *almost*, *not yet*. No grades. Spaced review at 1-2-4-8… days, capped at 3 reviews a day ([teachback/memory.py](teachback/memory.py)).
7. **Graph agent** (level 3B, [teachback/graph.py](teachback/graph.py)). Answers only from nodes and edges, shows the path and the sources with their provenance, and says when the graph doesn't know.
8. **Step budget.** Beyond 60 model calls per session, the orchestrator stops and hands over to a human. Every step is logged (`logs/<student>.jsonl`).
9. **Message to the lecturer**: the 3 most-missed concepts, with the slide. Only for official courses with at least 10 active students.

---

## Tests and evaluation

```bash
.venv\Scripts\python -m pytest                 # 54 tests, no network calls
.venv\Scripts\python -m pytest -m live         # 3 tests on the real model (needs the key, costs cents)
.venv\Scripts\python eval\run_eval.py --mode offline|live      # agreement with human judgement + knowledge leaks
.venv\Scripts\python eval\export_examples.py --mode offline|live   # regenerates docs/EXAMPLES.md
```

What the tests cover:

| File | What it checks |
| --- | --- |
| [tests/test_guardrails.py](tests/test_guardrails.py) | Citations, similarity with the slides, threshold, poisoned material, "you tell me", wording of discrepancies |
| [tests/test_substudent.py](tests/test_substudent.py) | With a **fake model**: the Sub-student never sees the slides, uses the cheaper model, applies the wrong claim, gets stuck, leaks are discarded, step budget, invalid JSON |
| [tests/test_teacher.py](tests/test_teacher.py) | From judgement to status, one-third threshold, discrepancies, invented IDs ignored, hint ladder, "explain it yourself" rule with the hidden explanation, "skip" |
| [tests/test_engine_flow.py](tests/test_engine_flow.py) | The demo script end to end, parity between the two engines, logging of every step, resuming from memory |
| [tests/test_graph_memory_digest.py](tests/test_graph_memory_digest.py) | Acyclic graph, paths and sources, "I don't know", review intervals, daily cap, 10-student threshold |
| [tests/test_api.py](tests/test_api.py) | The frontend API on the full demo script; challenge solutions never reach the browser; the deck is served |

**Current results** (`eval/results_offline.json`), on the **offline engine** and 8 hand-labelled explanations:

| Metric | Result | Target |
| --- | --- | --- |
| Sub-student knowledge leaks | 0 of 8 | 0 |
| Agreement of the rule-based judge with human judgement | 65% | ≥ 80% |

The 80% target is for the Claude judge: it has to be measured with `--mode live`. We haven't done that yet, because it needs the API key. The dataset should grow to 20 explanations, as planned in the documentation.

---

## Structure

```
web/                  React frontend
  src/pages/          Dashboard, Loop (the two screens, kept thin)
  src/hooks/          useLoopSession: loads the session and runs each step against the API
  src/components/     ConceptMap, mascots, toasts, dashboard/CourseCard
    loop/             header + stepper, thread, messages, Teacher's correction, side panel
    loop/composer/    the controls of each step (explain, questions, exam, correction, challenges)
  src/styles/         base, dashboard and loop styles (component styles sit next to their component)
  dist/               ready-made build, served by python -m server
server/               FastAPI API: sessions, JSON snapshots for the UI; also serves presentation/
presentation/         pitch deck: one file per slide, assets, and the script that splits an export
teachback/            backend
  engine.py           orchestrator: loop steps, thresholds, states, hints, "explain it yourself", budget
  agents/             llm_backend.py (Claude) · offline_backend.py (rules) · same interface
  guardrails.py       checks in code
  graph.py            NetworkX graph + graph agent (3B)
  memory.py           SQLite: states and reviews
  llm.py              single model client (structured outputs, budget, logs)
  contracts.py        types shared between backend and UI
prompts/              versioned system prompts (role, goal, rules, procedure, format)
data/courses/chemistry-equilibrium/   concepts + prerequisites, slides, synthetic class data
eval/                 evaluation and example export
tests/                pytest
docs/                 documentation and deliverables (in Italian)
static/               mockups and challenge images
```

## Deliverables

| Required by the challenge | Where |
| --- | --- |
| Presentation (mandatory) | [presentation/](presentation/) (one file per slide, with speaker notes), pitch text in [docs/pitch.md](docs/pitch.md) |
| L1: problem, idea, scenario, user, metrics | [docs/LEVEL1.md](docs/LEVEL1.md) |
| L2: README (setup, models, libraries, custom logic) | this file |
| L2: working repository | `teachback/`, `server/`, `web/`, `tests/` |
| L2: architecture (input, knowledge, tools, decisions, output) | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| L2: interaction examples, including one where the agent holds the line | [docs/EXAMPLES.md](docs/EXAMPLES.md) (section 4) |
| L2: interface | `web/` (React) + `server/` (API) |
| L3B: ontology, validated graph, graph agent, ≥ 3 examples (one with no answer) | [docs/ONTOLOGY.md](docs/ONTOLOGY.md), [docs/EXAMPLES.md](docs/EXAMPLES.md) (section 7) |
| L3C: launch campaign | [docs/LAUNCH.md](docs/LAUNCH.md) |
| Full project and decisions | [docs/TeachBack - Reply Clash 2026.md](docs/TeachBack%20-%20Reply%20Clash%202026.md) |

**What is real and what is a mockup**

| Status | Parts |
| --- | --- |
| Working, in the interface | Dashboard, full loop (explanation, questions, exam attempt, correction, re-explanation, challenges with hints), concept map, memory |
| Working in the backend only (with tests) | Weekly message to the lecturer, graph agent (3B), review schedule |
| Synthetic data | The **class** data in the message to the lecturer (`class_snapshot.json`) |
| Example or not active, labelled on the page | The Physics and Calculus courses on the dashboard, course creation |
| Sample material | The slides in `data/courses/chemistry-equilibrium/slides.md`, written for the demo in the format of a lecture. They should be replaced with the lecturer's real slides |

## Team

Riccardo Ferraro · Rosario Marco Grifasi · Francesco Sicilia · Samuele Gentile

License: see [LICENSE](LICENSE).
