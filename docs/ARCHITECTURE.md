# Architettura

Segue l'architettura di riferimento della challenge (`static/structure.png`): interfaccia → orchestratore → LLM + system prompt → tool → memoria, con guardrail in codice e log di ogni passo.

```
 Streamlit (app/)  ──►  Engine (teachback/engine.py)  ──►  Backend agenti ──► Claude (llm.py)
   chat, grafo,          macchina a stati del loop,          LLMBackend       Opus 5.5: Insegnante
   resoconto,            guardrail, soglie, stati,           OfflineBackend   Haiku 5.5: Sotto-studente
   docente, ripasso      indizi, "spiegalo tu", budget        (stessa interfaccia)
        ▲                  │            │            │
        │                  ▼            ▼            ▼
        └──────────  guardrails.py   graph.py     memory.py (SQLite)   logger.py → logs/*.jsonl
                     (in codice)     (NetworkX)   stati + ripassi
```

| Blocco di riferimento | In TeachBack |
| --- | --- |
| User interface | `app/` (Streamlit, ricalcata sui mockup in `static/`) |
| Agent orchestrator | `teachback/engine.py`: il loop *spiego → domande → prova → resoconto → sfide*, budget di 60 passi per sessione, poi passaggio a un umano |
| LLM | `teachback/llm.py`: client unico, structured outputs (JSON con schema), fallback in caso di rifiuto |
| System prompt (versionati in git) | `prompts/*.md`: ruolo, obiettivo, conoscenza, regole, procedura, formato |
| Tools | funzioni degli agenti e del motore (tabella sotto) |
| Memory | `teachback/memory.py`: stato per concetto e per studente, date dei ripassi |
| Guardrails | `teachback/guardrails.py`, applicati dall'orchestratore a entrambi i backend |
| Logs & evaluation | `teachback/logger.py` → `logs/`; `eval/` (accordo con il giudice, fughe, esempi) |

## Cosa riceve in input

- La **spiegazione dello studente**, scritta. La voce è in roadmap.
- Le sue **risposte** alle domande del Sotto-studente e alle sfide dell'Insegnante.
- Le sue **scelte**: quale domanda d'esame far provare, "non so", "avanti", "contesta il giudizio".

## Quale conoscenza usa

| Agente | Conoscenza | Cosa non vede mai |
| --- | --- | --- |
| Sotto-studente | **Solo** le affermazioni numerate estratte dalla spiegazione, più il testo della domanda d'esame | Slide, materiale, risposte giuste (verificato in `tests/test_substudent.py`) |
| Insegnante | Slide del corso (`slides.md`, già ripulite e chiuse in un blocco `<materiale_del_corso>` trattato come dato), concetti e prerequisiti convalidati (`concepts.json`), conoscenza del modello pre-addestrato solo per accorgersi di discrepanze | — |
| Agente sul grafo | Solo nodi, archi, stati e provenienza | Il modello: è deterministico |

Nella demo il materiale di un argomento sta tutto nel prompt dell'Insegnante: è la semplificazione prevista, senza database vettoriale. Con più corsi si passa a una ricerca per spezzoni (RAG) dietro la stessa funzione.

## Quali tool può chiamare

| Tool / azione | Chi lo usa | Implementazione |
| --- | --- | --- |
| `extract_claims` | Sotto-studente | LLM → elenco di affermazioni (schema JSON) |
| `ask` (domanda ingenua citata) | Sotto-studente | LLM + controllo citazioni |
| `try_exam` (prova una domanda d'esame) | Sotto-studente | LLM + controllo citazioni + blocco |
| `report` (resoconto a livelli) | Insegnante | LLM con schema; soglia e stati calcolati in codice |
| `make_challenge` / `grade` | Insegnante | LLM; la soluzione resta lato server |
| `update_status` + `schedule_review` | Motore | `memory.save_status` (intervalli 1-2-4-8…, tetto di 3 al giorno) |
| `flag_discrepancy` | Motore | "Discrepanza con [fonte], chiedi al docente", nel messaggio settimanale |
| `flag_judgement` | Studente | Registrata nel log per misurare l'accordo con il giudice |
| `ask_graph` | Studente | Percorsi nel grafo NetworkX, con fonti |
| `weekly_message` | Docente | Aggregazione con soglia dei 10 studenti |

## Quali decisioni prende

| Decisione | Chi decide |
| --- | --- |
| Domanda, risposta o blocco del Sotto-studente | Il modello propone; il **codice** scarta le frasi senza citazione valida e trasforma in blocco una risposta senza appoggi |
| Rifiuto del "dimmi tu", richiesta di un esempio a chi legge le slide | **Codice**, deterministico |
| Giudizio per concetto (spiegato / nominato / errato / assente) | L'**Insegnante** (modello) |
| Soglia di un terzo, stato del concetto, slide citata | **Codice** |
| Indizio 1 → indizio 2 → soluzione; quando chiedere la rispiegazione; coprire e scoprire la soluzione | **Codice** |
| Correttezza di una risposta a una sfida | L'**Insegnante** (modello) |
| Fermarsi e passare a un umano | **Codice**: budget di passi esaurito, o modello non disponibile (messaggio in pagina e copione offline) |

Il flusso è deliberatamente **guidato dal codice**, non lasciato al modello. È ciò che rende verificabili i limiti: "non sa", "non rivela la soluzione", "nessun voto".

## Cosa restituisce

| Oggetto (`teachback/contracts.py`) | Contenuto |
| --- | --- |
| `SubStudentReply` | Testo, frasi con citazioni, numero di frasi scartate, segnale "copiato dalle slide" |
| `TeacherReport` | Concetti spiegati, nominati e mancanti; flag "riprova"; per ogni errore: dove, slide e perché; discrepanze |
| `Challenge` (senza soluzione) | Domanda della sfida |
| `ChallengeStep` | Indizio, soluzione o esito |
| `GraphView` | Nodi colorati per stato, con il motivo ("rosso perché il prerequisito X è rosso") |
| `GraphAnswer` | Risposta dal grafo, percorso, fonti, `found` |
| `WeeklyMessage` | I 3 concetti più sbagliati con la slide, discrepanze, avvertenza sulla rappresentatività |
| `ReviewItem` | Ripassi di oggi |

## Perché due backend

`LLMBackend` e `OfflineBackend` hanno la stessa interfaccia (un test lo verifica). L'orchestratore applica le stesse regole a entrambi. Il backend offline serve a tre cose:
1. far girare i test senza rete;
2. avere una demo di riserva se la rete cade davanti ai giudici;
3. dare una base di confronto per la valutazione.
