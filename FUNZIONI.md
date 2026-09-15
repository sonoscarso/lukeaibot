# Le 50 nuove funzioni

Il menu generale è `/comandi`; categorie: `/comandi ai` e `/comandi strumenti`.
Tutte le funzioni rispettano il rate limit. Le funzioni AI usano una richiesta
per esecuzione; non navigano, non aprono URL, non eseguono codice e non inviano
messaggi ad altri contatti. Si può passare il testo dopo il comando o usarlo in
risposta a un messaggio. Limite input 8000 caratteri, con errore esplicito se superato.

## Testo, analisi e codice: 20 funzioni AI

| # | Comando | Uso / risultato |
|---|---|---|
| 1 | `/riassumi` | In reply a un testo: sintesi fedele in punti. |
| 2 | `/traduci inglese` | In reply: traduzione nella lingua indicata; italiano se non specificata. |
| 3 | `/correggi` | In reply: corregge grammatica e ortografia senza cambiare significato. |
| 4 | `/riscrivi formale` | In reply: riscrittura nel registro richiesto. |
| 5 | `/semplifica` | In reply: riduce complessità e spiega i termini tecnici. |
| 6 | `/spiega cache HTTP` | Spiegazione con esempio e limiti dell'analogia. |
| 7 | `/approfondisci indici SQL` | Approfondisce meccanismo, implicazioni e limiti. |
| 8 | `/confronta SQLite e PostgreSQL` | Confronto per criteri, con informazioni mancanti esplicite. |
| 9 | `/procontro lavorare da remoto` | Vantaggi, svantaggi, condizioni e rischi. |
| 10 | `/verificatesi` | In reply: analizza coerenza e assunzioni. Non è una verifica web dei fatti. |
| 11 | `/estrai` | In reply: nomi, date, cifre e vincoli presenti nel testo. |
| 12 | `/azioni` | In reply a un verbale: attività, responsabili e scadenze, senza inventarli. |
| 13 | `/titoli` | In reply: cinque titoli pertinenti senza clickbait. |
| 14 | `/scaletta guida ai backup` | Struttura ordinata per un documento. |
| 15 | `/email chiedi un aggiornamento sulla consegna` | Bozza con oggetto e corpo; non invia email. |
| 16 | `/risposta cortese ma ferma` | In reply: bozza di risposta pronta da copiare. |
| 17 | `/codice funzione Python per leggere CSV` | Snippet con istruzioni; non esegue codice. |
| 18 | `/debug` | In reply a log/codice: cause probabili e correzione minima. |
| 19 | `/documenta` | In reply a codice: parametri, ritorni, errori ed esempio. |
| 20 | `/test` | In reply a codice: test comportamentali e casi limite, non eseguiti. |

## Gestione, memoria e utilità: 30 funzioni locali

| # | Comando | Uso / risultato |
|---|---|---|
| 21 | `/comandi [ai\|strumenti\|tutti]` | Catalogo delle 50 funzioni. |
| 22 | `/ping` | Reattività del bot e tempo della query database. |
| 23 | `/stato` | Modello, presenza, tono, media, lunghezza, pausa e frequenza. |
| 24 | `/id` | ID utente, chat e messaggio, utile per configurare ADMIN_USER_ID. |
| 25 | `/statistiche` | Numero di messaggi/utenti e periodo osservato nella chat. |
| 26 | `/topattivi` | Dieci partecipanti con più messaggi osservati. |
| 27 | `/mieistat` | Statistiche dei propri messaggi nella chat. |
| 28 | `/cerca deploy` | Fino a 10 risultati dalla sola cronologia di questa chat. |
| 29 | `/profilo` | Legge il proprio profilo salvato, senza consumare AI. |
| 30 | `/ricorda preferisco esempi Python` | Salva un fatto personale per il contesto AI; restituisce un ID. |
| 31 | `/ricordi [pagina]` | Elenca i propri fatti espliciti, 10 per pagina. |
| 32 | `/scorda 7` | Elimina il proprio fatto esplicito con ID 7 in questa chat. |
| 33 | `/nota controllare il preventivo` | Salva una nota e restituisce un ID. |
| 34 | `/note [pagina]` | Elenca le proprie note, 10 per pagina. |
| 35 | `/legginota 7` | Legge per intero la propria nota con ID 7. |
| 36 | `/eliminanota 7` | Elimina la propria nota con ID 7. |
| 37 | `/todo controllare il deploy` | Crea un'attività personale aperta. |
| 38 | `/attivita [pagina]` | Elenca le proprie attività aperte. |
| 39 | `/completate [pagina]` | Elenca le proprie attività completate. |
| 40 | `/completa 7` | Segna la propria attività come completata. |
| 41 | `/riapri 7` | Riapre la propria attività. |
| 42 | `/eliminatodo 7` | Elimina la propria attività. |
| 43 | `/sondaggio Quando? \| Oggi \| Domani` | Sondaggio Telegram anonimo con 2–10 opzioni distinte. |
| 44 | `/calcola (20+5)*3` | Aritmetica con parentesi; + - * / // % **, limiti su profondità ed esponente. |
| 45 | `/conta` | In reply: conteggio caratteri, parole e righe. |
| 46 | `/estrailink` | In reply: fino a 30 URL HTTP(S) unici, senza visitarli. |
| 47 | `/pausa 30` | Ferma le risposte conversazionali per 30 minuti; range 1–1440. |
| 48 | `/riprendi` | Interrompe subito la pausa. |
| 49 | `/silenzio 23-8` | Blocca interventi casuali in questa fascia, Europe/Rome; `off` disattiva. |
| 50 | `/frequenza 3 10` | 3% di probabilità per messaggio non indirizzato, almeno 10 minuti tra interventi. |

## Persistenza e comportamento

- Note, attività e fatti espliciti sono accessibili ai comandi solo del loro
  autore e della stessa chat. Il risultato dei comandi di gruppo è visibile al
  gruppo; per appunti riservati usa una chat privata con il bot.
- Le rimozioni per ID cancellano l'elemento, non i messaggi originali in Telegram
  o nell'archivio del bot. `/scorda` non è una cancellazione globale dei dati utente.
- Note e attività ammettono 2000 caratteri. Le liste sono paginate; la lettura
  integrale della nota usa `/legginota`. I ricordi nel prompt sono limitati ai
  10 più recenti e 300 caratteri ciascuno per evitare prompt enormi.
- Tutti i partecipanti possono cambiare le impostazioni della chat, come nelle
  versioni precedenti. La gestione della lista GIF resta riservata a @SoyLe0.
- Il tono si sceglie dal pannello: Volgare e tagliente, Diretto, Neutro.
- Il casuale avviene solo quando arrivano messaggi osservabili. I cooldown e gli
  orari silenziosi persistono; non vengono creati messaggi temporizzati a chat vuota.
- Nuove tabelle e colonne vengono aggiunte automaticamente senza cancellare dati.
- Le 50 funzioni sono aggiuntive: `/persona`, `/conosci`, `/argomenta`, `/negra`
  e il pannello preesistente non sono conteggiati nel totale.
