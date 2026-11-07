# Struttura del progetto e lavoro in parallelo

Il prototipo è completo: vedi il [README](../README.md) per avvio, test e consegne. Questo file serve a chi continua a lavorarci in due, senza pestarsi i piedi.

## Due aree, un contratto

| Area | Proprietario | File |
| --- | --- | --- |
| **Backend e agenti** | P1 | `teachback/`, `prompts/`, `data/`, `eval/`, `tests/` tranne `test_app.py`, `docs/ARCHITECTURE.md`, `docs/ONTOLOGY.md`, `docs/EXAMPLES.md` (generato) |
| **Interfaccia e presentazione** | P2 | `app/`, `.streamlit/`, `tests/test_app.py`, `TeachBack.html`, `static/`, `docs/LEVEL1.md`, `docs/pitch.md`, `docs/LAUNCH.md` |
| **In comune** (si tocca solo dopo essersi parlati) | P1 + P2 | `teachback/contracts.py`, `requirements.txt`, `README.md` |

**Il contratto** tra le due aree è fatto di due cose:
- i tipi in [teachback/contracts.py](../teachback/contracts.py);
- i metodi pubblici di `Engine` in [teachback/engine.py](../teachback/engine.py).

La UI chiama solo quelli, tramite `get_engine()`. Regola: si **aggiungono** campi con un valore di default, non si rinomina e non si toglie nulla.

## I metodi che la UI usa

| Passo | Metodo `Engine` | Restituisce |
| --- | --- | --- |
| setup | `load_course`, `start_session` | `Course`, `Session` |
| 1 · Io spiego | `submit_explanation(s, text)` | `list[Claim]` |
| 2 · Domande | `substudent_reply(s, msg=None)` | `SubStudentReply` |
| 3 · Prova | `substudent_try_exam(s, question=None)` | `SubStudentReply` |
| 4 · Resoconto | `teacher_report(s)` | `TeacherReport` |
| 5 · Sfide | `next_challenge(s)`, `answer_challenge(s, id, answer)` | `Challenge`, `ChallengeStep` |
| Grafo | `get_graph(s)`, `ask_graph(s, q)` | `GraphView`, `GraphAnswer` |
| Docente | `weekly_message(course_id, s)` | `WeeklyMessage` |
| Ripasso | `due_reviews(s)` | `list[ReviewItem]` |
| Segnala | `flag_judgement(s, note)` | — |

## Come lavorare in parallelo

- **P2 lavora sempre sul motore offline** (`TEACHBACK_MODE=offline`). Non serve la chiave, e le risposte sono stabili per provare l'interfaccia.
- **P1 aggiunge un comportamento in due posti**:
  - in entrambi i backend (`agents/llm_backend.py` e `agents/offline_backend.py`), oppure direttamente nell'orchestratore se è una regola;
  - in un test. `test_both_backends_implement_the_same_interface` controlla che i due backend restino allineati.
- **Due branch** (`backend`, `ui`), con merge frequenti su `main`. Le cartelle sono disgiunte, quindi i merge non vanno in conflitto.
- **Prima di ogni merge**: `python -m pytest`.
