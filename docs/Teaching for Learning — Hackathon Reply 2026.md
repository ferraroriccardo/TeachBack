# Teaching for Learning — Hackathon Reply 2026

Nov 7, 2026 · @Rosario

## La challenge

**Student Tech Clash 2026 — AI on Campus.** Scegliere un problema reale di apprendimento, insegnamento o valutazione all'università e progettare una soluzione basata su AI. "Parti dal problema, non dallo strumento." Fuori tema: amministrazione e logistica (iscrizioni, tasse, orari, aule, trasporti).

### I tre livelli

| Livello | Obbligatorio | Cosa chiede |
| --- | --- | --- |
| 1 · Design | Sì | Problema + idea di soluzione AI + pitch di 60 secondi |
| 2 · Build | Sì | Un agente AI funzionante che mostri il cuore dell'idea (no-code o codice) |
| 3 · Extra | No | Multi-agente, knowledge graph e/o campagna di lancio: uno, due, tutti o parziali |

Si può vincere anche solo con i livelli 1 e 2; il livello 3 è un bonus.

### Livello 1 — Design

Tre direzioni suggerite (si possono proporre altre idee):

- **Teaching** — capire cosa gli studenti non hanno colto, adattare le spiegazioni, creare materiali. Rischio: sostituire il giudizio umano. Esempi: Q&A sulla lezione, aggiornare le slide dell'anno prima, "gemello digitale" del docente disponibile 24/7.
- **Learning** — capire gli errori, costruire modelli mentali solidi, sapere cosa si sa davvero. Esempi: esercizi che si adattano a ciò che sbagli, simulazione d'orale con un tutor che ti contraddice.
- **Assessment** — misurare cosa sai davvero. Esempi: feedback su saggi che spiega perché l'argomento non regge, readiness check prima dell'esame.

Consigli: partire dall'esperienza personale; essere specifici (un corso, un esame, un momento); chiedersi se funzionerebbe anche senza AI; nominare i rischi (dati degli studenti, servizio giù la notte prima dell'esame, chi non ha accesso).

### Livello 2 — Build

Rispetto a un semplice chatbot l'agente deve:

1. **Lavorare su materiale reale** — appunti, slide, programma, esercizi passati.
2. **Fare qualcosa, non solo rispondere** — almeno un'azione: generare e correggere un quiz, tracciare gli errori ricorrenti, creare un piano di studio, segnalare una domanda al docente.
3. **Conoscere i propri limiti** — guidare il ragionamento, non pensare al posto dello studente.

Due percorsi, se ne sceglie uno:

|  | Path A · No/Low code | Path B · Codice |
| --- | --- | --- |
| Come | Strumenti AI pronti, istruzioni scritte come specifica: Role, Goal, Knowledge, Rules, Procedure, Memory | Qualsiasi linguaggio e modello (consigliato Open Code) |
| Consegne | Istruzioni + note sulle scelte; materiale e azioni; esempi di interazione (uno in cui tiene il limite); screenshot/export del setup; video demo (opzionale) | README; script/notebook/repo funzionante; descrizione architettura (input, conoscenza, tool, decisioni, output); esempi di interazione (uno in cui tiene il limite); interfaccia o video demo (opzionale) |

Architettura di riferimento (Path B): interfaccia (chat, Telegram, Streamlit) → orchestratore (loop plan → act → observe, con limite di passi e passaggio a un umano) → LLM + system prompt → tool (es. `search_notes` con RAG, `generate_exercise`, `grade_answer`, `schedule_review`, `notify`) → memoria strutturata (profilo dello studente in JSON/SQLite) → guardrail in codice → log di ogni passo. Il minimo per un agente vero: orchestratore + LLM + un tool + memoria.

Consigli: fare bene un solo flusso; usare modelli pre-addestrati, niente training.

### Livello 3 — Extra (opzionale)

- **A · Multi-agente** — un Problem Identifier Agent produce un Problem Brief; almeno due Solver Agent con ruoli diversi propongono soluzioni; un orchestratore o valutatore le confronta; loop di chiarimento; punti di controllo umano.
- **B · Knowledge graph** — ontologia (classi e relazioni, es. Student, Concept, Exam; *requires*, *assesses*), grafo popolato con estrazione AI validata, agente che risponde dal grafo mostrando il percorso di ragionamento e dicendo quando il grafo non sa. Almeno 3 esempi, di cui uno senza risposta. Strumenti: Protégé, Neo4j, RDFLib, NetworkX, Streamlit.
- **C · Campagna di lancio** — nome, tagline, canali, tempistiche sull'anno accademico. Obiettivo: dopo un mese gli utenti target conoscono lo strumento e l'hanno provato almeno una volta.

### Valutazione

| Criterio | Peso |
| --- | --- |
| Creatività e innovazione | 40% |
| Impatto | 20% |
| Tecnica | 20% |
| Presentazione | 20% |

Tre domande che i giudici usano a ogni livello:

1. È davvero nuovo o solo più veloce?
2. Aiuta a pensare o pensa al posto tuo?
3. Chi ne beneficia e chi resta escluso?

**Presentazione.** Fase 1: pitch di 60 secondi, senza slide (problema, idea, impatto), pronti a difendere le scelte. Fase 2, solo per i primi 3: presentazione con slide di massimo 5 minuti.

**Da consegnare.** La presentazione è obbligatoria; se possibile anche i materiali (agente, documenti, file del prototipo). Checklist livello 1: problema e chi lo vive, idea in parole semplici, scenario d'uso in un momento reale, utente target e contesto, metriche di successo, pitch provato.

## La nostra proposta

**TeachBack — "Studi spiegando a un'AI che non sa niente: impara solo da te, e se le hai insegnato male sbaglia l'esercizio davanti ai tuoi occhi."** È la frase del pitch. Due agenti: un Sotto-studente che sa solo quello che gli spieghi e un Insegnante che conosce il materiale del corso. Gli errori di tutta la classe tornano al docente, sulla slide giusta.

### Il problema

Rileggere slide e appunti dà una sensazione di fluidità che lo studente scambia per comprensione: è l'*illusione di competenza*, e se ne accorge solo all'esame. La ricerca indica la strada:

- **Recupero attivo:** richiamare a memoria funziona meglio che rileggere (Roediger e Karpicke, 2006).
- **Spiegare migliora la comprensione:** auto-spiegazione (Chi) e apprendimento insegnando, anche a un pubblico assente (Fiorella e Mayer, 2013).
- **Effetto protégé:** gli studenti si impegnano di più per un agente a cui insegnano che per sé stessi (Chase et al., 2009, la linea di ricerca di Betty's Brain).

TeachBack fa scoprire allo studente *prima dell'esame* cosa non sa, e dice al docente cosa la classe non ha capito. Questa seconda metà è la novità vera.

**Per cosa funziona:** domande di teoria ed esami orali. Non promettiamo "qualunque esame": esercizi numerici, dimostrazioni, programmazione e lingue richiedono altro. Estensione futura: la variante "spiegami il procedimento", in cui lo studente insegna al Sotto-studente come si imposta un esercizio.

**Scenario per pitch e demo:** Chimica, primo anno, teoria dell'equilibrio chimico e del principio di Le Châtelier. Gran parte dell'esame è calcolo (Kc, tabelle ICE, pH), ma le domande di teoria chiedono di spiegare *perché* l'equilibrio si sposta. TeachBack serve per i 3-4 argomenti che temi, non per ripassare l'intero corso.

### Come funziona

1. Il docente carica slide e appunti. L'AI propone i concetti chiave e i prerequisiti di ogni argomento, il docente li convalida: circa 10 minuti per argomento, una volta sola. Nei corsi non ufficiali la proposta resta automatica, con l'etichetta "non convalidato".
2. Lo studente sceglie l'argomento che teme e parte il loop.

**Il loop:**

1. **Io spiego** l'argomento al Sotto-studente, per iscritto o a voce. Si sceglie al primo avvio; il default è il testo.
2. **Sotto-studente AI · domande.** Non sa niente: il suo sapere è solo la mia spiegazione. Fa domande ingenue su quello che ha sentito e non può far trapelare la risposta, perché non la conosce. Se leggo le slide parola per parola risponde: "Così c'è scritto sulle slide, ma io non l'ho capito. Me lo fai con un esempio tuo?"
3. **Sotto-studente AI · prova.** Prova a rispondere a una domanda d'esame usando solo quello che gli ho insegnato. Se gli ho insegnato una cosa sbagliata, la applica e sbaglia davanti a me. Se gli ho spiegato una cosa incompleta, non inventa: si blocca e dice "Qui mi blocco, non mi hai detto cosa succede quando…".
4. **Insegnante AI · resoconto.** Conta solo i concetti spiegati con un perché o un esempio, non le parole chiave nominate. Sotto un terzo dei concetti chiave chiede di riprovare, dicendo solo quali mancano. Sopra, aiuta a livelli: prima *dove* sbaglio, con il riferimento alla slide, poi *perché*.
5. **Insegnante AI · sfide**, in un momento distinto: domande su argomenti non toccati, sempre nel contesto del corso. A "non so" segue una scala: primo indizio, secondo indizio, soluzione.
6. **Esame interno.** Domande sempre nuove nello stile delle domande di teoria, concentrate sui concetti deboli. Le soluzioni si vedono solo dopo il tentativo. Esito per concetto: *pronto*, *quasi*, *non ancora*. Nessun voto.

**Regola "spiegalo tu", morbida.** Quando l'Insegnante dà una spiegazione completa, nel resoconto o nelle sfide, più avanti chiede di rispiegarla al Sotto-studente: non subito ma dopo un'altra domanda, e applicata a un caso diverso. Durante la rispiegazione la spiegazione è coperta: non viene proprio inviata alla pagina, quindi non si recupera nemmeno dal codice. Il pulsante "avanti" è sempre disponibile: chi salta lascia il concetto rosso nel grafo e se lo ritrova nel ripasso.

&#91;embedded content: il loop di apprendimento · 2 agenti AI, 6 passi\]

Lo studente è sempre quello che parla. Il Sotto-studente impara solo da lui; l'Insegnante è l'unico che conosce il materiale.

**Materiale:** l'Insegnante usa slide, appunti e l'LLM pre-addestrato. Se trova una discrepanza non scrive "la slide è sbagliata", ma "discrepanza con \[fonte\], chiedi al docente". Il materiale caricato dagli studenti è trattato come dato, mai come istruzione: un file con istruzioni nascoste non cambia il comportamento degli agenti.

**Come si fa un Sotto-studente che non sa.** Un LLM la chimica la conosce già, quindi "non sapere" va imposto e verificato:

1. Dalla spiegazione dello studente si estrae un elenco numerato di affermazioni.
2. Il Sotto-studente risponde citando, per ogni passaggio, il numero dell'affermazione che usa.
3. Un controllo in codice scarta ogni frase senza citazione, o con una citazione che non c'entra.
4. Se un passaggio non ha un'affermazione che lo sostiene, il Sotto-studente si blocca invece di inventare. Se l'affermazione è sbagliata, la applica fedelmente e sbaglia.

Nella demo le affermazioni citate compaiono a schermo accanto alla risposta: i giudici vedono che il Sotto-studente usa solo ciò che gli è stato detto. Va testato con il modello che useremo: i modelli più potenti tendono a "completare" da soli più facilmente.

### Grafo di conoscenza e ripasso

Tutto si basa su un unico dato: lo **stato di ogni concetto** per ogni studente (*pronto*, *quasi*, *non ancora*). Lo aggiorna l'Insegnante usando la prova del Sotto-studente, il resoconto, le sfide e l'esame interno.

- **Il grafo è al centro.** I concetti sono collegati dai prerequisiti (es. *costante di equilibrio* → *principio di Le Châtelier*) e si colorano mentre studi. Lo studente vede cosa sa, cosa no e perché ("Le Châtelier non ti torna perché la costante di equilibrio è *ancora rossa*"). Senza voto, è questa la ragione per tornare. È anche il livello 3B della challenge.
- **Lo stato non entra mai nel voto.** Niente da vincere barando, e lo studente è libero di sbagliare.
- **Ripasso.** Sfide brevi dell'Insegnante sui concetti *quasi*, a intervalli che si allungano se rispondi bene e si accorciano se sbagli. Un concetto "non ancora" riapre il loop su quell'argomento. Tetto giornaliero di avvisi, ad esempio 3 ripassi al giorno, per non sommergere chi segue più corsi.
- **Verifica del giudice.** Tutto il grafo è l'opinione di un solo LLM. Per questo misuriamo l'accordo tra noi e il modello su 20 spiegazioni giudicate da entrambi. Lo studente può segnalare un giudizio che ritiene sbagliato: la segnalazione viene registrata e serve a misurare l'accordo con il giudice. Nessuno la legge in tempo reale.

&#91;embedded content: spaced repetition · curva del ricordo con ripassi ripetuti\]

Ogni picco è un ripasso: riporta su il ricordo, e la discesa successiva è più lenta.

**Cosa resta allo studente:** la capacità di esporre, la comprensione dei propri errori e il proprio grafo di conoscenza.

### Obiettivi

- Far scoprire allo studente cosa non sa, prima dell'esame.
- Dire al docente cosa la classe non ha capito, argomento per argomento.
- Uno studio meno passivo e meno ansioso per gli studenti.

### Feature

- **Libreria di corsi.** Il docente crea un corso ufficiale, con concetti e prerequisiti convalidati, e lo condivide lui stesso. Lo studente può creare un corso non ufficiale con il proprio materiale, così usa l'app anche se il professore non la propone. I corsi non ufficiali sono privati o condivisi solo con colleghi dello stesso ateneo, ed etichettati "non convalidato".
- **Messaggio settimanale al docente** (solo corsi ufficiali, con almeno 10 studenti attivi, così i dati restano davvero anonimi). I 3 concetti più sbagliati dalla classe, le slide collegate e le discrepanze trovate nel materiale. Per chi vuole c'è una dashboard, che vede **solo il docente**: non è uno strumento per valutarlo. Avvertenza dichiarata: l'app la usano soprattutto i più motivati, quindi i dati non rappresentano tutta la classe.
- **Il loop, il grafo, l'esame interno e il ripasso** descritti sopra.

### Perché non ChatGPT Study Mode o NotebookLM

La risposta di una riga: **"Lì l'AI ti spiega. Qui l'AI impara solo da te e sbaglia se le insegni male, e gli errori di tutta la classe tornano al docente sulla slide giusta."** I prompt si copiano in un pomeriggio; il loop chiuso con il docente e i dati per concetto e per corso no. È lì che sta il vantaggio.

### Costi

Il costo vero sono le chiamate al modello; la memoria per studente è una riga in un database.

| Voce | Stima indicativa (prezzi da verificare) |
| --- | --- |
| Chiamate al modello | 50-80 chiamate per sessione completa, 0,3-0,6 milioni di token: da pochi centesimi a 1-2 € a sessione, secondo il modello |
| Trascrizione vocale | Qualche centesimo a sessione; fornitore con server in UE o modello locale |
| Server e database | Trascurabili rispetto al modello |

Per un ateneo con 10.000 studenti attivi, 3 sessioni a settimana per 30 settimane, si va da circa 50-100 mila € a oltre 1 milione l'anno. Per questo: l'università paga un abbonamento con un **tetto di sessioni per studente**, il Sotto-studente gira su un modello più economico, e fuori dagli atenei abbonati c'è una versione limitata, che serve anche a convincere l'ateneo ("i tuoi studenti lo usano già").

**Se chiedono il prezzo** (ipotesi da verificare, non listino): tetto di 2 sessioni a settimana per studente, con il Sotto-studente su un modello economico; obiettivo di costo sotto i 10 centesimi a sessione, cioè circa 6 € per studente all'anno; prezzo all'ateneo di 10-15 € per studente attivo all'anno.

### Il prototipo (livello 2)

**Path B, codice. Un flusso fatto benissimo, come chiede la challenge.**

- **Fatto davvero:** il loop su un argomento di Chimica (Sotto-studente con citazioni, Insegnante con resoconto e sfide) e il grafo che si colora.
- **Mockup statici:** messaggio settimanale al docente, esame interno, voce e ripasso. Con 2-3 ore non c'è tempo per il codice: si mostrano come schermate dichiarate.

| Pezzo | Scelta |
| --- | --- |
| Interfaccia | Streamlit: chat, pannello del grafo, schermata del messaggio al docente |
| Modello | Un LLM via API: prompt dell'Insegnante, prompt del Sotto-studente, estrazione delle affermazioni dalla spiegazione |
| Conoscenza | RAG su slide e appunti reali di Chimica sull'equilibrio; solo l'Insegnante vi accede |
| Memoria | SQLite: stato di ogni concetto per studente, tentativi, date dei ripassi |
| Grafo | NetworkX: concetti e prerequisiti, colorati per stato |
| Azioni | Far provare una domanda d'esame al Sotto-studente; generare e correggere le sfide; aggiornare lo stato dei concetti; segnalare una discrepanza nel materiale; comporre il messaggio al docente |
| Guardrail in codice | Citazione obbligatoria delle affermazioni per ogni frase del Sotto-studente; somiglianza con i pezzi di slide recuperati; soglia sui concetti spiegati, non nominati; spiegazione coperta mai inviata alla pagina; materiale caricato isolato come dato |
| Valutazione | 20 spiegazioni giudicate da noi e dal modello, con il tasso di accordo |

**Esempio in cui tiene il limite:** lo studente scrive "dimmi tu cos'è il principio di Le Châtelier, poi lo ripeto". Il Sotto-studente risponde: "Non lo so, so solo quello che mi hai detto tu! Prova a spiegarmelo con un esempio." Non sta recitando: davvero non ha altro.

**Copione della demo.** Il momento "sbaglia davanti ai tuoi occhi" deve essere garantito, non lasciato al caso:

1. Lo studente spiega Le Châtelier e ci infila un errore classico: "il catalizzatore sposta l'equilibrio verso i prodotti".
2. Il Sotto-studente prova la domanda: "Aggiungo un catalizzatore a N₂ + 3H₂ ⇌ 2NH₃. Cosa succede all'NH₃ all'equilibrio?" Risponde "aumenta (affermazione 4)", con l'affermazione citata a schermo.
3. L'Insegnante interviene con il riferimento alla slide: il catalizzatore fa raggiungere l'equilibrio più in fretta, ma non lo sposta.
4. Il nodo *catalizzatore* nel grafo diventa rosso.
5. Si chiude con la schermata del messaggio settimanale al docente.

Il copione va provato almeno 5 volte con il modello vero, e serve un video di riserva se la rete cade.

### Piano per le prossime 2-3 ore (4 persone)

**Semplificazioni per la demo:** niente database vettoriale (il testo delle slide dell'unico argomento va direttamente nel prompt dell'Insegnante), niente SQLite (lo stato vive nella sessione di Streamlit), grafo con 5-6 concetti scritti a mano, niente voce.

| Persona | Compito | Pronto entro |
| --- | --- | --- |
| A | Sotto-studente: estrazione delle affermazioni numerate, risposta con citazioni, controllo in codice; blocco se manca un'affermazione | 1h15 |
| B | Insegnante: resoconto a livelli e sfide con indizi, sul testo delle slide; aggiornamento dello stato dei concetti | 1h15 |
| C | Streamlit: chat, pannello delle affermazioni citate, grafo colorato; integra il lavoro di A e B | 1h30 |
| D | Slide della presentazione (obbligatoria), mockup di messaggio al docente, esame, voce e ripasso; testo del pitch e campagna | 1h45 |

| Orario | Tutti |
| --- | --- |
| 0:00-0:15 | Repo, chiave API, i 5-6 concetti del grafo, il testo delle slide su Le Châtelier |
| 0:15-1:30 | Lavoro in parallelo |
| 1:30 | Stop alle nuove funzioni: solo integrazione e correzioni |
| 1:30-2:00 | Copione della demo provato almeno 5 volte; registrazione del video di riserva |
| 2:00-fine | Consegna di presentazione e materiali; pitch cronometrato ad alta voce |

Se alle 1:30 il Sotto-studente non regge le citazioni in modo affidabile, la demo si fa dal video di riserva.

### Metriche di successo

Sono obiettivi, non risultati.

| Fase | Metrica | Obiettivo |
| --- | --- | --- |
| Prototipo | Accordo tra noi e il giudice sulle 20 spiegazioni di prova | ≥ 80% |
| Prototipo | Prove in cui il Sotto-studente usa conoscenze non date dallo studente | 0 su 20 prove |
| Pilota | Studenti che tornano entro una settimana dalla prima prova | ≥ 40% |
| Pilota | Durata di una sessione su un argomento | ≤ 20 minuti |
| Pilota | Risultati sulle domande di teoria, argomenti allenati vs non allenati, a 2-4 settimane | Migliori sugli allenati |
| Pilota | Messaggi settimanali aperti dal docente | Almeno 3 su 4 |

**Metodo del pilota.** Chi sceglie l'app è già più motivato, quindi "voti con e senza app" non basta. Si confrontano gli stessi studenti sugli argomenti allenati e non allenati, oppure gruppi assegnati a caso.

### Roadmap

Cose che servono a un ateneo ma non sono nel prototipo:

- **Login d'ateneo** (SSO via IDEM/Shibboleth) e **integrazione con Moodle**, così il docente non carica nulla in più. Mesi di lavoro, diversi per ogni ateneo.
- **Variante "spiegami il procedimento"** per gli esercizi numerici.
- **Voce, esame interno e ripasso** completi, se nella demo restano mockup.
- Conformità come sistema ad alto rischio per l'AI Act, prima del 2 dicembre 2027.

### Rischi e chi resta escluso

| Rischio | Come lo gestiamo |
| --- | --- |
| **Abbandono: è il rischio vero.** Lo studente lo trova lento o frustrante e torna a ChatGPT | "Avanti" sempre disponibile; uso mirato su 3-4 argomenti; grafo al centro; tetto giornaliero di avvisi |
| Leggere le slide come spiegazione | Controllo di somiglianza con le slide; il Sotto-studente chiede un esempio proprio |
| Elencare parole chiave per superare la soglia | La soglia conta solo i concetti spiegati con un perché o un esempio |
| Usare il Sotto-studente come oracolo o forzarlo con un prompt | Non conosce la risposta, quindi non può rivelarla |
| Sbagliare apposta per avere la spiegazione, o ripeterla a pappagallo | Accettato: non c'è niente da vincere. La rispiegazione arriva dopo un'altra domanda e su un caso diverso |
| Copiare da un altro chatbot | Non si blocca: lo stato non conta per il voto |
| Materiale "avvelenato" con istruzioni nascoste | Il materiale caricato è dato, mai istruzione |
| Il giudice LLM sbaglia e lo studente si sente trattato ingiustamente | Nessun blocco; lo studente può segnalare il giudizio; tasso di accordo misurato |
| Falsa sicurezza ("l'app mi dava 27") | Niente voto: solo pronto / quasi / non ancora |
| Segnalazione sbagliata al docente | "Discrepanza con \[fonte\], chiedi al docente", mai "la slide è sbagliata" |
| Privacy nelle classi piccole | Niente statistiche sotto i 10 studenti attivi |
| Dashboard usata per valutare il docente | La vede solo il docente |
| AI Act | TeachBack valuta l'apprendimento per orientare il percorso: rientra probabilmente nell'Allegato III, punto 3. Gli obblighi per questi sistemi si applicano dal 2 dicembre 2027 ([Regolamento (UE) 2026/1744](https://www.steptoe.com/en/news-publications/steptechtoe-blog/eu-ai-act-amendments-enter-into-force.html), il Digital Omnibus sull'AI, in vigore dal 27 luglio 2026). Progettiamo già per esserlo. Nessun riconoscimento delle emozioni dalla voce: è vietato in ambito educativo |
| GDPR e voce | Trascrizione con fornitore in UE o modello locale; audio cancellato dopo la trascrizione |
| Adozione lenta dell'università (gara o MePA, DPIA, mesi di attesa) | Si parte da corsi non ufficiali e da un pilota su un corso |
| Chi resta escluso | Aiuta di più chi è già motivato: lo diciamo. Testo o voce a scelta, utile per alcuni studenti DSA; sessioni brevi su un argomento per gli studenti lavoratori; modalità solo testo per chi ha una connessione debole; resoconti e grafo esportabili in PDF |

## Pitch e lancio

### Pitch di 60 secondi

Circa 150 parole: va cronometrato ad alta voce e tagliato finché non sta sotto i 55 secondi.

> Quanti di voi hanno riletto le slide tre volte, si sentivano pronti e all'esame, alla domanda "perché?", sono rimasti muti? Si chiama illusione di competenza: rileggere sembra capire, ma non lo è.
>
> TeachBack ribalta lo studio: non è l'AI che spiega a te, sei tu che spieghi a lei. Il nostro Sotto-studente non sa niente: impara solo da quello che gli dici. Poi prova una domanda d'esame, e se gli hai insegnato male sbaglia davanti ai tuoi occhi. Scopri la lacuna prima dell'esame, non durante.
>
> Un Insegnante AI che conosce le slide del corso ti mostra dove hai sbagliato e ti mette alla prova su ciò che non hai toccato. E ogni settimana il docente riceve i tre concetti che la classe non ha capito, con la slide collegata.
>
> Lo studente impara spiegando, il docente sa dove intervenire. Nessuno pensa al posto tuo.

**Se contestano "nessuno pensa al posto tuo"** (l'Insegnante alla fine dà la soluzione): "Solo dopo due indizi, e poi te la fa rispiegare su un caso diverso."

### Slide della Fase 2 (5 minuti, solo per i primi 3)

1. L'illusione di competenza, con i tre riferimenti alla ricerca.
2. Il loop, con il Sotto-studente che non sa.
3. Demo dal vivo del catalizzatore, circa 2 minuti. Se la rete è instabile, diventa il video di riserva.
4. Il messaggio al docente e il grafo.
5. Rischi gestiti e chi resta escluso, metriche e roadmap.

### Campagna di lancio (livello 3C, versione leggera)

Del livello 3 facciamo il grafo (3B) e questa campagna (3C). Saltiamo il multi-agente (3A), che richiede una struttura che non abbiamo.

| Elemento | Scelta | Perché |
| --- | --- | --- |
| Nome | TeachBack | Dice cosa fai: insegni indietro a chi ti ha insegnato |
| Tagline | "Non rileggerlo. Spiegalo." | Contrappone l'abitudine sbagliata a quella giusta, in tre parole |
| Pubblico | Studenti del primo anno del corso di Chimica e il loro docente | Un corso grande, con un esame che spaventa |
| Canali | Il docente in aula (5 minuti con la demo del catalizzatore); rappresentanti degli studenti e gruppi del corso; pagina del corso; associazioni studentesche | Il docente dà credibilità, i gruppi tra pari la diffusione |
| Tempi | Lancio 4-6 settimane prima della sessione invernale: settimana 1 in aula; settimane 2-3 nei gruppi, con la sfida "spiega un argomento in 10 minuti"; ultime settimane, promemoria "scegli i 3 argomenti che temi" | È il momento in cui gli studenti cercano un modo per studiare meglio |

**Obiettivo della challenge:** un mese dopo il lancio, gli studenti del corso sanno che TeachBack esiste e l'hanno provato almeno una volta.

## Domande difficili dei giudici

Risposte di due righe per la difesa dopo il pitch.

**È davvero nuovo?** Gli agenti a cui lo studente insegna esistono nella ricerca (Betty's Brain, AlgoBo). Il nuovo è un Sotto-studente che usa solo ciò che gli dici, in modo verificabile, sul materiale reale del corso, più il ritorno degli errori della classe al docente.

**Come sapete che il Sotto-studente non bara?** Ogni sua frase deve citare un'affermazione dello studente, e un controllo in codice scarta le altre. Le citazioni sono a schermo; l'obiettivo è 0 fughe su 20 prove.

**E se il giudice LLM sbaglia?** Non blocca nessuno: "avanti" è sempre disponibile e lo studente può segnalare il giudizio. Misuriamo l'accordo con noi su 20 spiegazioni, con obiettivo ≥ 80%.

**Perché non ChatGPT Study Mode o NotebookLM?** Lì l'AI ti spiega. Qui l'AI impara solo da te e sbaglia se le insegni male, e gli errori di tutta la classe tornano al docente sulla slide giusta.

**Non pensa al posto dello studente?** La soluzione arriva solo dopo due indizi, e poi va rispiegata su un caso diverso. Per tutto il resto parla lo studente.

**Lo studente può barare?** Sì, copiando da un'altra scheda. Ma lo stato dei concetti non conta per il voto, quindi barare non fa vincere niente.

**Chi paga?** L'ateneo, con un abbonamento per studente attivo. Ipotesi da verificare: 10-15 € all'anno, con un tetto di 2 sessioni a settimana.

**Chi resta escluso?** Aiuta di più chi è già motivato, e lo diciamo. Per gli altri: sessioni brevi su un argomento, testo o voce a scelta, modalità leggera per chi ha una connessione debole.

**Perché un docente dovrebbe fidarsi?** Convalida lui concetti e prerequisiti, l'AI non corregge le sue slide ma segnala discrepanze, e nessun voto è automatico. Le statistiche sono anonime, sopra i 10 studenti, e le vede solo lui.

**E l'AI Act e la privacy?** Probabilmente siamo un sistema ad alto rischio (Allegato III, punto 3), con obblighi dal 2 dicembre 2027: progettiamo già per esserlo. Niente riconoscimento delle emozioni; audio trascritto in UE e cancellato.

## Decisioni prese

Aggiornate il 7 novembre dopo il secondo grill esterno, che ha cambiato diverse scelte precedenti.

| Tema | Decisione | Cambiata dal grill? |
| --- | --- | --- |
| Nome e pitch | **TeachBack**; pitch di 60 secondi partendo dalla frase "Studi spiegando a un'AI che non sa niente…" | Sì, testo completo nel secondo giro |
| Agenti | Due: Sotto-studente e Insegnante. Sfide ed esame interno li fa l'Insegnante | No |
| Sotto-studente | **Non sa davvero**: conosce solo la spiegazione dello studente e prova una domanda d'esame con quella | Sì, prima "sa ma non dice" |
| Come non sa | Affermazioni numerate, citazione obbligatoria per ogni frase, controllo in codice; se manca un'affermazione si blocca | Nuova, secondo giro |
| Blocchi | **Morbidi**: "avanti" sempre disponibile, il concetto resta rosso e torna nel ripasso | Sì, prima blocco fino alla risposta corretta |
| Regola "spiegalo tu" | Più avanti, su un caso diverso; spiegazione coperta solo durante la rispiegazione, mai inviata alla pagina | Sì, prima immediata |
| Soglia del resoconto | Conta i concetti spiegati con un perché o un esempio, non quelli nominati | Sì, precisata |
| Sfide | Primo indizio, secondo indizio, poi soluzione | Sì, precisata |
| Esame interno | Soluzioni solo dopo il tentativo; esito pronto / quasi / non ancora, nessun voto | Sì, prima voto stimato |
| Segnalazione di un giudizio sbagliato | Registrata, serve a misurare l'accordo con il giudice | Nuova, secondo giro |
| Ambito | Domande di teoria ed esami orali; "spiegami il procedimento" in roadmap. Mai più "qualunque esame" | Sì |
| Caso concreto e demo | Chimica, equilibrio e Le Châtelier; copione con l'errore sul catalizzatore | Copione nuovo, secondo giro |
| Concetti e prerequisiti | L'AI propone, il docente convalida in circa 10 minuti per argomento; nei corsi non ufficiali "non convalidato" | Sì, prima "zero sforzo" |
| Voce | Scelta al primo avvio, default testo; non è una difesa contro la copia | Sì, prima default voce |
| Lettura delle slide | Controllo di somiglianza con le slide recuperate | Nuova |
| Materiale caricato | Trattato come dato, mai come istruzione | Nuova |
| Discrepanze nel materiale | "Discrepanza con \[fonte\], chiedi al docente" | Sì, formulazione |
| Statistiche al docente | Solo corsi ufficiali, almeno 10 studenti attivi, visibili solo al docente | Sì, soglia aggiunta |
| Score | Non conta mai per il voto | No |
| AI Act | Probabile alto rischio (Allegato III, punto 3); Regolamento (UE) 2026/1744 verificato | Sì |
| Costi | Il costo sono le chiamate al modello; tetto di sessioni per studente | Sì |
| Moodle e login d'ateneo | Spostati in roadmap, non sono feature del prototipo | Sì, secondo giro |
| Differenza da ChatGPT e NotebookLM | L'AI impara solo da te; gli errori della classe tornano al docente | Nuova |
| Demo | Loop e grafo fatti benissimo; messaggio al docente, esame, voce e ripasso come mockup statici (2-3 ore, 4 persone) | Sì |
| Metriche di successo | Obiettivi numerici per prototipo e pilota | Nuova, secondo giro |
| Livello 3 | 3B (grafo) e 3C leggero (campagna); niente 3A | Nuova, secondo giro |

**Da fare:**

- [ ] Recuperare il testo delle slide di Chimica su equilibrio e Le Châtelier (primi 15 minuti).
- [ ] Costruire il Sotto-studente con citazione obbligatoria e testarlo sul modello che userete.
- [ ] Provare il copione della demo almeno 5 volte; registrare il video di riserva.
- [ ] Preparare le slide della presentazione: è l'unica consegna obbligatoria.
- [ ] Cronometrare il pitch ad alta voce e tagliarlo sotto i 55 secondi.
- [ ] Dopo l'hackathon: 20 spiegazioni per misurare l'accordo con il giudice e verifica dei prezzi del modello.
