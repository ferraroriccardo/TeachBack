# TeachBack

> **Non rileggerlo. Spiegalo.**
> Studi spiegando a un'AI che non sa niente: impara solo da te, e se le hai insegnato male sbaglia l'esercizio davanti ai tuoi occhi.

Prototipo per **Student Tech Clash 2026 — AI on Campus** (livello 2, *Path B · codice*; livello 3B grafo di conoscenza e 3C campagna di lancio).
Due agenti:
- il 🐣 **Sotto-studente** sa solo ciò che lo studente gli spiega, e ogni sua frase cita l'affermazione da cui viene;
- il 🦉 **Insegnante** conosce le slide del corso, dice *dove* hai sbagliato e poi *perché*, propone sfide con indizi e colora il grafo dei concetti.

Gli errori di tutta la classe tornano al docente con un messaggio settimanale, collegati alla slide giusta.

Caso della demo: **Chimica Generale I, equilibrio chimico e principio di Le Châtelier**, con l'errore classico *"il catalizzatore sposta l'equilibrio"*.

---

## Avvio rapido

Serve Python 3.11 o superiore. Tutto si installa in un ambiente virtuale dentro la cartella del progetto.

```bash
python -m venv .venv
# Windows
.venv\Scripts\pip install -r requirements.txt
# macOS / Linux
.venv/bin/pip install -r requirements.txt

cp .env.example .env          # poi inserisci ANTHROPIC_API_KEY (facoltativo)
```

Interfaccia (dalla radice del repository):

```bash
.venv\Scripts\streamlit run app/streamlit_app.py      # Windows
.venv/bin/streamlit run app/streamlit_app.py          # macOS / Linux
```

Si apre su <http://localhost:8501>.

**Due motori, stessa app.** Nella barra laterale si sceglie:
- **Live · Claude**: i due agenti girano su Claude via API. Serve `ANTHROPIC_API_KEY` nel file `.env`.
- **Copione offline**: agenti a regole, senza rete né chiave. Orchestratore, guardrail, stati, indizi e grafo sono lo **stesso codice**. È la demo di riserva se la rete cade e la base dei test.

Senza chiave l'app parte da sola in modalità offline.

### Copione della demo (2 minuti)

1. **Il loop** → **📋 Spiegazione della demo**. Il testo contiene l'errore *"anche il catalizzatore sposta l'equilibrio verso i prodotti"*.
2. **Insegna al Sotto-studente**. A destra compaiono le affermazioni numerate: è tutto ciò che il Sotto-studente sa.
3. **Fagli provare la domanda d'esame**, quella sul catalizzatore. Risponde *"l'NH3 aumenta"* citando l'affermazione sbagliata, che si colora di rosso.
4. **Chiedi il resoconto all'Insegnante**. Compare il riquadro rosso *Catalizzatore* con la Slide 13, e *Perché?* come secondo livello. Il nodo **Catalizzatore** nel grafo diventa rosso.
5. **Messaggio settimanale** (sezione Docente): *Catalizzatore* è in cima, con la slide collegata.

Per ripartire da un punto preciso basta aprire l'app con un parametro nell'indirizzo:

| Indirizzo | Dove riparte |
| --- | --- |
| `/loop?demo=prova` | il Sotto-studente ha appena provato la domanda d'esame |
| `/loop?demo=resoconto` | il resoconto dell'Insegnante |
| `/loop?demo=sfide` | la prima sfida |

Nella barra laterale, **↺ Nuova sessione** azzera tutto.

---

## Modelli, librerie, framework

| Cosa | Scelta | Perché |
| --- | --- | --- |
| Insegnante | **Claude Opus 5.5** (`claude-opus-5-5`); effort `medium` per il resoconto, `low` per sfide e correzioni | Giudizio sul materiale del corso |
| Sotto-studente ed estrazione delle affermazioni | **Claude Haiku 5.5** (`claude-haiku-5-5`), effort `low` | Più economico (vedi i costi nella documentazione). Un modello meno capace "completa" meno da solo |
| SDK | `anthropic` (ufficiale) | **Structured outputs**: ogni risposta è JSON validato contro uno schema |
| Rifiuti del modello | Fallback lato server (`fallbacks: "default"`) sulle chiamate a Opus | Se un filtro di sicurezza rifiuta per errore, la richiesta viene ripetuta su un modello di riserva |
| Interfaccia | Streamlit 1.67 | Multipagina, ricalcata sui mockup in `static/` |
| Grafo | NetworkX + Graphviz (nel browser, via `st.graphviz_chart`) | Prerequisiti, stato dei concetti, percorsi |
| Memoria | SQLite (`data/teachback.db`, creato da solo) | Stato di ogni concetto per studente e date dei ripassi |
| Test | pytest + `streamlit.testing` (AppTest) | 54 test offline, più 3 opzionali sul modello vero |

I modelli si cambiano da `.env` (`TEACHBACK_TEACHER_MODEL`, `TEACHBACK_SUBSTUDENT_MODEL`). Niente training: solo modelli pre-addestrati.

---

## Logica custom (il cuore del progetto)

Descrizione completa in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). In breve:

1. **Il Sotto-studente non sa davvero.** Dalla spiegazione si estrae un elenco numerato di affermazioni ([teachback/agents/llm_backend.py](teachback/agents/llm_backend.py)). Il Sotto-studente riceve **solo** quelle, mai le slide; c'è un test che lo verifica. Ogni frase deve citare i numeri delle affermazioni che usa.
2. **Controllo citazioni in codice** ([teachback/guardrails.py](teachback/guardrails.py)). Scarta le frasi senza citazione, con citazioni inesistenti o con citazioni che non c'entrano. Se non resta nulla, il Sotto-studente **si blocca** ("Qui mi blocco, non mi hai detto…") invece di inventare.
3. **Altri guardrail in codice**:
   - *"dimmi tu"* riceve un rifiuto deterministico, senza chiamare il modello;
   - una spiegazione copiata dalle slide viene riconosciuta (somiglianza di trigrammi ≥ 60%) e il Sotto-studente chiede un esempio tuo;
   - il materiale caricato è un dato, mai un'istruzione: le righe che sembrano istruzioni nascoste vengono rimosse;
   - le discrepanze nel materiale sono sempre formulate come *"Discrepanza con [fonte], chiedi al docente"*.
4. **Resoconto a soglia** ([teachback/engine.py](teachback/engine.py)). Contano solo i concetti spiegati con un perché o un esempio, non quelli nominati.
   - Sotto un terzo dei concetti chiave si riprova, e l'app dice solo cosa manca.
   - Sopra la soglia, l'Insegnante dice prima *dove* (con la slide, che mette il codice e non il modello) e poi *perché*, su richiesta.
5. **Sfide** con la scala *primo indizio → secondo indizio → soluzione*.
   - **Regola "spiegalo tu"**: dopo un'altra domanda, la rispiegazione su un caso diverso. Durante la rispiegazione la soluzione **viene tolta dalla pagina** e torna visibile alla fine.
   - **"Avanti"** è sempre disponibile: chi salta lascia il concetto rosso.
6. **Stati dei concetti**: *pronto*, *quasi*, *non ancora*. Nessun voto. Ripasso a intervalli 1-2-4-8… giorni, con tetto di 3 ripassi al giorno ([teachback/memory.py](teachback/memory.py)).
7. **Agente sul grafo** (livello 3B, [teachback/graph.py](teachback/graph.py)). Risponde solo da nodi e archi, mostra il percorso e le fonti con la provenienza, e dice quando il grafo non lo sa.
8. **Budget di passi.** Oltre 60 chiamate al modello per sessione, l'orchestratore si ferma e passa a un umano. Ogni passo finisce nel log (`logs/<studente>.jsonl`).
9. **Messaggio al docente**: i 3 concetti più sbagliati, con la slide. Solo per corsi ufficiali e con almeno 10 studenti attivi.

---

## Test e valutazione

```bash
.venv\Scripts\python -m pytest                 # 54 test, nessuna chiamata di rete
.venv\Scripts\python -m pytest -m live         # 3 test sul modello vero (serve la chiave, costa centesimi)
.venv\Scripts\python eval\run_eval.py --mode offline|live      # accordo con il giudizio umano + fughe di conoscenza
.venv\Scripts\python eval\export_examples.py --mode offline|live   # rigenera docs/EXAMPLES.md
```

Cosa coprono i test:

| File | Cosa verifica |
| --- | --- |
| [tests/test_guardrails.py](tests/test_guardrails.py) | Citazioni, somiglianza con le slide, soglia, materiale avvelenato, "dimmi tu", formulazione delle discrepanze |
| [tests/test_substudent.py](tests/test_substudent.py) | Con un **finto modello**: il Sotto-studente non vede mai le slide, usa il modello economico, applica l'affermazione sbagliata, si blocca, le fughe vengono scartate, budget di passi, JSON non valido |
| [tests/test_teacher.py](tests/test_teacher.py) | Da giudizio a stato, soglia di un terzo, discrepanze, ID inventati ignorati, scala degli indizi, regola "spiegalo tu" con la spiegazione coperta, "avanti" |
| [tests/test_engine_flow.py](tests/test_engine_flow.py) | Il copione della demo dall'inizio alla fine, parità tra i due motori, log di ogni passo, ripresa dalla memoria |
| [tests/test_graph_memory_digest.py](tests/test_graph_memory_digest.py) | Grafo aciclico, percorsi e fonti, "non lo so", intervalli di ripasso, tetto giornaliero, soglia dei 10 studenti |
| [tests/test_app.py](tests/test_app.py) | Tutte le pagine si aprono; demo completa cliccando nell'interfaccia |

**Risultati attuali** (`eval/results_offline.json`), sul **motore offline** e su 8 spiegazioni etichettate a mano:

| Metrica | Risultato | Obiettivo |
| --- | --- | --- |
| Fughe di conoscenza del Sotto-studente | 0 su 8 | 0 |
| Accordo del giudice a regole con il giudizio umano | 65% | ≥ 80% |

L'obiettivo dell'80% riguarda il giudice Claude: va misurato con `--mode live`. Non l'abbiamo ancora fatto, perché serve la chiave API. Il dataset va portato a 20 spiegazioni, come previsto nella documentazione.

---

## Struttura

```
app/                  interfaccia Streamlit (views/: dashboard, loop, grafo, ripasso, esame, docente)
teachback/            backend
  engine.py           orchestratore: fasi del loop, soglie, stati, indizi, "spiegalo tu", budget
  agents/             llm_backend.py (Claude) · offline_backend.py (regole) · stessa interfaccia
  guardrails.py       controlli in codice
  graph.py            grafo NetworkX + agente sul grafo (3B)
  memory.py           SQLite: stati e ripassi
  llm.py              client unico del modello (structured outputs, budget, log)
  contracts.py        tipi scambiati tra backend e interfaccia
prompts/              system prompt versionati (ruolo, obiettivo, regole, procedura, formato)
data/courses/chimica-equilibrio/   concetti + prerequisiti, slide, dati sintetici della classe
eval/                 valutazione ed esportazione degli esempi
tests/                pytest
docs/                 documentazione e consegne
static/               mockup dell'interfaccia e immagini della challenge
TeachBack.html        slide della presentazione
```

## Consegne

| Richiesto dalla challenge | Dove |
| --- | --- |
| Presentazione (obbligatoria) | [TeachBack.html](TeachBack.html), testo del pitch in [docs/pitch.md](docs/pitch.md) |
| L1: problema, idea, scenario, utente, metriche | [docs/LEVEL1.md](docs/LEVEL1.md) |
| L2: README (avvio, modelli, librerie, logica custom) | questo file |
| L2: repository funzionante | `teachback/`, `app/`, `tests/` |
| L2: architettura (input, conoscenza, tool, decisioni, output) | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| L2: esempi di interazione, anche uno in cui l'agente tiene il limite | [docs/EXAMPLES.md](docs/EXAMPLES.md) (sezione 4) |
| L2: interfaccia | `app/` |
| L3B: ontologia, grafo validato, agente sul grafo, ≥ 3 esempi (uno senza risposta) | [docs/ONTOLOGY.md](docs/ONTOLOGY.md), [docs/EXAMPLES.md](docs/EXAMPLES.md) (sezione 7) |
| L3C: campagna di lancio | [docs/LAUNCH.md](docs/LAUNCH.md) |
| Progetto completo e decisioni | [docs/TeachBack - Reply Clash 2026.md](docs/TeachBack%20-%20Reply%20Clash%202026.md) |

**Cosa è vero e cosa è mockup**

| Stato | Parti |
| --- | --- |
| Funzionante | Loop completo, grafo, sfide, memoria e ripasso, messaggio al docente (con calcolo e soglie veri) |
| Dati sintetici, dichiarati nella pagina | I dati della **classe** nel messaggio al docente |
| Mockup, dichiarato nella pagina | Esame interno, voce, creazione di un corso non ufficiale |
| Materiale di esempio | Le slide in `data/courses/chimica-equilibrio/slides.md`, scritte per la demo nel formato di una lezione. Vanno sostituite con le slide reali del docente |

Licenza: vedi [LICENSE](LICENSE).
