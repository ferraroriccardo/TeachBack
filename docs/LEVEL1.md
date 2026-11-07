# Livello 1 · Design

Checklist della challenge: problema e chi lo vive, idea in parole semplici, scenario in un momento reale, utente e contesto, metriche di successo, pitch provato.
Fonte completa e decisioni: [TeachBack - Reply Clash 2026.md](TeachBack%20-%20Reply%20Clash%202026.md).

## Il problema e chi lo vive

Rileggere slide e appunti dà una sensazione di fluidità che lo studente scambia per comprensione. È l'**illusione di competenza**, e lo studente se ne accorge solo all'esame, alla domanda "perché?".

Lo vivono soprattutto gli studenti dei primi anni nei corsi con domande di teoria e orali. La ricerca indica la strada:
- **recupero attivo** (Roediger e Karpicke, 2006);
- **spiegare per imparare** (Chi; Fiorella e Mayer, 2013);
- **effetto protégé**: ci si impegna di più per un agente a cui si insegna (Chase et al., 2009).

Dall'altra parte il **docente** non sa cosa la classe non ha capito finché non corregge gli esami.

## L'idea in parole semplici

Studi spiegando a un'AI che non sa niente: impara solo da te, e se le hai insegnato male sbaglia l'esercizio davanti ai tuoi occhi. Un'AI Insegnante che conosce le slide ti dice dove hai sbagliato. Ogni settimana il docente riceve i tre concetti che la classe non ha capito, ognuno con la sua slide.

## Scenario d'uso in un momento reale

Chimica Generale I, primo anno, due settimane prima dell'appello invernale. Giulia ha riletto tre volte le slide sull'equilibrio chimico e si sente pronta. Apre TeachBack e spiega Le Châtelier al Sotto-studente. Senza accorgersene dice che *"anche il catalizzatore sposta l'equilibrio verso i prodotti"*.

Il Sotto-studente prova la domanda d'esame sul catalizzatore e risponde *"l'NH3 aumenta (affermazione 3)"*. Giulia vede l'errore nascere dalla sua frase. L'Insegnante le indica la Slide 13 e, se lei lo chiede, il perché. Il nodo *Catalizzatore* diventa rosso e torna nel ripasso dopo un giorno. Il lunedì dopo, il docente legge che 18 studenti su 43 hanno sbagliato proprio quel concetto, e in aula ci dedica cinque minuti.

## Utente target e contesto

| Ruolo | Chi |
| --- | --- |
| Utente principale | Studenti dei primi anni, in corsi grandi con domande di teoria e orali, sui 3-4 argomenti che temono (non tutto il corso) |
| Secondo utente | Il docente del corso ufficiale: convalida concetti e prerequisiti in circa 10 minuti per argomento e riceve il messaggio settimanale |

Fuori ambito: esercizi numerici, dimostrazioni, programmazione e lingue. La variante "spiegami il procedimento" è in roadmap.

## Metriche di successo

Sono obiettivi, non risultati.

| Fase | Metrica | Obiettivo |
| --- | --- | --- |
| Prototipo | Accordo tra noi e il giudice su 20 spiegazioni | ≥ 80% |
| Prototipo | Prove in cui il Sotto-studente usa conoscenze non date | 0 su 20 |
| Pilota | Studenti che tornano entro una settimana | ≥ 40% |
| Pilota | Durata di una sessione su un argomento | ≤ 20 minuti |
| Pilota | Domande di teoria su argomenti allenati e non allenati, a 2-4 settimane | Migliori sugli allenati |
| Pilota | Messaggi settimanali aperti dal docente | Almeno 3 su 4 |

Stato attuale delle prime due metriche: vedi il README, sezione *Test e valutazione*.

## Pitch

Testo cronometrato in [pitch.md](pitch.md). Va provato ad alta voce e tenuto sotto i 55 secondi.
