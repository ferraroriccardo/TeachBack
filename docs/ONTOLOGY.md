# Ontologia e grafo di conoscenza (livello 3B)

Il grafo è al centro dell'esperienza dello studente: mostra cosa sa, cosa no e **perché**. Per ogni coppia studente-concetto c'è un solo dato: lo stato (*pronto*, *quasi*, *non ancora*).

## Classi

| Classe | Perché serve | Proprietà chiave |
| --- | --- | --- |
| `Concept` | Unità di comprensione su cui si dà il giudizio (es. *Catalizzatore*) | `id`, `name`, `aliases`, `validated` |
| `Slide` | Fonte del concetto: serve a dire allo studente *cosa rivedere* e al docente *dove intervenire* | `ref` (es. "Slide 13 - Catalizzatori ed equilibrio") |
| `Student` | Il grafo è personale | `student_id` |
| `Course` | Raggruppa concetti e domande d'esame; ufficiale o non ufficiale | `official`, `title` |

## Relazioni

| Relazione | Dominio → codominio | Perché serve |
| --- | --- | --- |
| `requires` | Concept → Concept | Spiega i blocchi: *"Le Châtelier non ti torna perché la costante di equilibrio è ancora rossa"* |
| `taughtIn` | Concept → Slide | Riferimento nel resoconto e nel messaggio al docente |
| `hasStatus` | Student → Concept (pronto / quasi / non ancora) | Colore del nodo, ripasso, messaggio al docente |
| `partOf` | Concept → Course | Libreria dei corsi |

**Provenienza** di ogni fatto: `source` (slide), `extracted_by` (AI), `validated_by` (docente), `date`. Si trova in [data/courses/chimica-equilibrio/concepts.json](../data/courses/chimica-equilibrio/concepts.json) ed è citata nelle risposte dell'agente.

## Il grafo della demo

```
Equilibrio dinamico ──► Costante di equilibrio (Kc) ──► Quoziente di reazione (Q) ──► Principio di Le Châtelier ──► Effetto della temperatura
        │                                                                                      │
        └──────────────────────────────────────► Catalizzatore ◄──────────────────────────────┘
```

(A ──► B significa: B *richiede* A.)

## Come è stato popolato e validato

1. **Estrazione con l'AI.** Dalle slide della lezione (`slides.md`) l'AI propone i concetti chiave e i prerequisiti. È il passo che nel prodotto fa l'Insegnante quando il docente carica il materiale.
2. **Validazione umana**, come farebbe il docente (circa 10 minuti per argomento). Abbiamo controllato ogni concetto e ogni arco contro le slide e un manuale di chimica generale:
   - **tolti** i concetti troppo fini per una domanda di teoria (es. "solidi puri non compaiono in Kc");
   - **aggiunto** l'arco *Catalizzatore requires Le Châtelier*. Lo sbaglio tipico ("il catalizzatore sposta l'equilibrio") nasce dall'applicare Le Châtelier a ciò che non è una perturbazione;
   - **tenuto** il grafo piccolo: 6 nodi e 6 archi. *Un grafo piccolo e corretto vale più di uno grande e rumoroso.*
3. **Controlli automatici** ([tests/test_graph_memory_digest.py](../tests/test_graph_memory_digest.py)):
   - il grafo è aciclico;
   - ogni prerequisito esiste;
   - i percorsi restituiti seguono archi reali.
4. Nei **corsi non ufficiali** la proposta dell'AI resta automatica, con `validated: false` ed etichetta "non convalidato".

## L'agente sul grafo

[teachback/graph.py](../teachback/graph.py), funzione `ask`. Risponde **solo** da nodi e archi, quindi non usa il modello. Per ogni risposta mostra:
- il **percorso** di archi `requires` usato;
- le **fonti**, cioè slide e provenienza di ogni concetto toccato;
- `found: false` con un messaggio esplicito quando la domanda va oltre ciò che il grafo contiene, invece di inventare.

Domande supportate: perché un concetto è rosso o non torna, cosa serve sapere prima, cosa sblocca.

**Esempi** (output reali in [EXAMPLES.md](EXAMPLES.md), sezione 7):

| Domanda | Esito |
| --- | --- |
| *"Perché il catalizzatore non mi torna?"* | Percorso Catalizzatore → Le Châtelier → Q → Kc, perché Kc è rosso; fonti: Slide 6, 8, 10, 13 |
| *"Cosa devo sapere prima di Le Châtelier?"* | Prerequisiti in ordine topologico, con lo stato di ciascuno |
| *"Chi ha scoperto il principio di Le Châtelier?"* | **Non nel grafo**: lo dice e rimanda all'Insegnante o al docente |

## Controllabilità

Il grafo è un file JSON leggibile. Se un arco è sbagliato, il docente lo corregge lì: non serve riaddestrare un modello né riscrivere un prompt. Nella roadmap la correzione si fa dalla dashboard del docente.
