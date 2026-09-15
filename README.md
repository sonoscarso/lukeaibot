# Bot Telegram AI — Python + Render + PostgreSQL

Progetto pronto per un Render Web Service Python 3.12. Un unico processo esegue
long polling Telegram asincrono e server HTTP su `0.0.0.0:$PORT`.
Nessun database SQLite, nessun salvataggio locale dei dati del bot.

## Nuova versione: 50 funzioni e pannello funzionante

Apri `/imposgiacomino`: categorie presenza, sticker/GIF, lunghezza, tono e
frequenza casuale. La spunta indica il valore realmente salvato; puoi tornare
indietro o chiudere. Il tono predefinito è **volgare e tagliente**: il prompt
consente esplicitamente parolacce senza asterischi e battute in risposta agli
insulti. Nessuna sostituzione locale delle parolacce; restano le scelte del
modello e le regole del provider. Non esiste una garanzia di assenza di rifiuti.

Le **50 nuove funzioni** sono descritte con esempi in [FUNZIONI.md](FUNZIONI.md).
Usa `/comandi`, `/comandi ai` o `/comandi strumenti`. I comandi sono registrati
anche nel menu Telegram all'avvio dell'istanza attiva.

Il casuale è una probabilità sui nuovi messaggi non indirizzati del gruppo,
non un timer che scrive quando tutti tacciono. Default: 3,5%, minimo 10 minuti.
Modalità 3 ignora tag/reply, ma continua a estrarre casualmente gli altri messaggi;
modalità 2 risponde ai tag/reply e valuta casualmente gli altri. In privato il bot
risponde normalmente; `/pausa` sospende la conversazione anche in privato.
I comandi restano sempre disponibili (salvo rate limit).
`/silenzio 23-8` limita solo gli interventi casuali, con fuso Europe/Rome.

Correzioni incluse: ricezione degli eventi `callback_query` nel polling, parsing
dei bottoni presenza, gestione dei click ripetuti, intervallo casuale persistente
e chiusura sicura quando il database non è stato inizializzato.

## Scelta AI verificata il 15 settembre 2026

**Groq, modello `llama-3.3-70b-versatile`**, API compatibile OpenAI, endpoint
`https://api.groq.com/openai/v1/chat/completions`.
Il modello è nella lista di produzione e Groq indica circa 280 token/s:
è una misura del provider, non un benchmark di questo progetto né una garanzia
sul tempo totale della risposta. La documentazione attuale lo contrassegna
**Enterprise / Contact Sales**: non si può garantire l'accesso gratuito con ogni
account. Verifica disponibilità, permessi e quote nella tua console. Le quote
pubblicate in precedenza in questo README appartenevano al modello GPT-OSS,
non a Llama; sono state rimosse. Il modello rimane quello richiesto dall'utente.
Per tornare alla scelta iniziale modifica `AI_MODEL=openai/gpt-oss-20b` in Render.

Fonti ufficiali: [modelli Groq](https://console.groq.com/docs/models),
[limiti e piano gratuito](https://console.groq.com/docs/rate-limits),
[console e chiavi](https://console.groq.com/keys).

**Fallback opzionale OpenRouter**: `OPENROUTER_API_KEY` e
`FALLBACK_MODEL=openrouter/free`. Quest'ultimo seleziona un modello gratuito
disponibile; qualità e latenza possono cambiare. Sono accettati anche ID con
suffisso `:free`. Nessun passaggio automatico a modelli a pagamento.
Il fallback scatta per timeout, errori di rete, HTTP 404/408/429/5xx.
Non scatta per rifiuti testuali, `refusal`, `content_filter`, HTTP 400/401/403 o
risposte ambigue: non è un meccanismo per aggirare filtri.
Il contenuto viene inviato al secondo provider solo se il fallback scatta.

Fonti: [router gratuito](https://openrouter.ai/docs/faq),
[modelli free](https://openrouter.ai/docs/guides/routing/model-variants/free),
[quote OpenRouter](https://openrouter.ai/docs/api_reference/limits).

## Piano realizzato

1. Verifica provider attuale e configurazione di un fallback gratuito esplicito.
2. Schema PostgreSQL automatico per chat, utenti, messaggi, profili e media.
3. Comandi Telegram, autorizzazione admin e acquisizione GIF transazionale.
4. Contesto limitato, recupero ricordi e stile/persona persistente per chat.
5. HTTP health, long polling, controllo istanza attiva e arresto ordinato.
6. Test locali, guida di deploy e archivio distribuibile.

## Avvio su Render

1. Crea un bot con **@BotFather**, `/newbot`, e conserva il token.
2. Crea una chiave gratuita Groq dalla console indicata sopra.
3. Crea un PostgreSQL su Neon o Supabase e copia la stringa di connessione
   PostgreSQL, **non** l'URL HTTP del progetto o una chiave API Supabase.
   Se nei log compare `PoolTimeout`, verifica che il valore Render inizi con
   `postgresql://` o `postgres://`, includa `?sslmode=require`, e contenga host,
   porta, database, utente e password validi. Non usare un URL HTTP Supabase,
   una chiave API, né una stringa scaduta del pooler. Il bot ritenta cinque volte
   e poi termina con un messaggio generico senza stampare credenziali.
   Usa un database dedicato a questo bot e un utente con permessi di creazione
   tabelle. Mantieni TLS, ad esempio `?sslmode=require`; usa `verify-full` con
   certificati verificabili quando previsto dal provider.
   Neon: connection string del pannello Connect. Supabase: se l'endpoint diretto
   IPv6 non è raggiungibile, scegli il pooler che supporta IPv4. La libreria usa
   `prepare_threshold=None` e solo lock transazionali, compatibili con pooler.
4. Estrai lo ZIP. Carica **il contenuto di `telegram-ai-bot/` nella radice** di
   un repository Git. Non caricare il tuo `.env`.
5. In Render crea un **Blueprint** dal repository: verrà letto `render.yaml`.
   Inserisci `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `GROQ_API_KEY`, `ADMIN_USER_ID`.
   `ADMIN_USER_ID` è l'ID Telegram numerico di **@SoyLe0**. È raccomandato;
   per il bootstrap senza ID puoi lasciarlo vuoto o impostare `0`.
6. In alternativa crea manualmente un **Web Service / Python / Free**:
   build `pip install -r requirements.txt`, start `python bot.py`,
   health check `/health`, Python 3.12, stesse variabili.
7. Attendi il log `Bot avviato in long polling` e apri
   `https://NOME-SERVIZIO.onrender.com/health`: a regime restituisce
   `{"ok":true,"status":"running"}`.
8. Apri il bot su Telegram, premi Start e prova `/persona sei Napoleone`,
   poi scrivigli. Aggiungilo al gruppo.

Per osservare i messaggi di gruppo, configura `/setprivacy` → Disable in
@BotFather (può essere necessario rimuovere e aggiungere nuovamente il bot),
oppure rendilo amministratore con i permessi appropriati. Deve poter inviare
testo, GIF e sticker. Gli altri bot e gli amministratori anonimi vengono ignorati.
Fonte: [FAQ Telegram su privacy e messaggi ricevuti](https://core.telegram.org/bots/faq).

Il bot riceve solo nuovi messaggi consegnati da Telegram. Non scarica il passato,
non può enumerare tutti i membri e non risolve arbitrariamente username privati
mai osservati. Per un utente sconosciuto usa il comando in risposta a un suo
messaggio. I profili sono **sempre separati per chat e ID numerico utente**.

## UptimeRobot e limiti reali del gratuito

Crea un monitor HTTP(S) con URL `https://NOME-SERVIZIO.onrender.com/health`
e intervallo 5 minuti. Anche `/` espone lo stesso controllo. Il ping è traffico
HTTP in ingresso; il long polling Telegram è traffico in uscita.

Render Free sospende dopo 15 minuti senza traffico in ingresso. I ping possono
ridurre l'inattività, ma non garantiscono disponibilità continua: rimangono
riavvii, quote mensili (750 ore condivise per workspace), cold start e possibili
sospensioni per elevato traffico esterno, incluse chiamate API/database.
Non usare Render Postgres Free per memoria permanente: scade dopo 30 giorni.
Fonte: [limiti ufficiali Render Free](https://render.com/docs/free).

## Comandi

| Comando | Comportamento |
| --- | --- |
| `/start`, `/help` | Istruzioni e informativa sui dati osservati. |
| `/persona <descrizione>` | Salva lo stile nella chat corrente (1500 caratteri). Qualsiasi partecipante può cambiarlo, come richiesto. |
| `/negra @utente` o reply | Menzione HTML sicura, frase AI casuale, poi GIF casuale della lista admin. Il nome del comando non impone contenuti razzisti. |
| `/listaaggiorna` | Solo @SoyLe0 in privato: avvia/riprende raccolta GIF. |
| GIF durante acquisizione | Memorizza una bozza su PostgreSQL; invia GIF come animazioni Telegram, non come documenti generici. |
| `/stop` | Aggiunge atomicamente le bozze alla lista attiva, elimina duplicati e termina la sessione. Non rimuove GIF precedenti. |
| `/conosci @utente` o reply | Aggiorna e mostra profilo da nome, username, bio se Telegram la espone, messaggi osservati e risposte ad altri utenti. |
| `/conosci gruppo` | Aggiorna fino a 8 profili, partendo dai mai elaborati o meno aggiornati; ripetere per proseguire. Evita esplosioni di richieste API nei gruppi grandi. |
| `/argomenta <tesi>` | Circa 100 parole nella persona corrente; non inventa prove a supporto di premesse false. |
| `/imposgiacomino` | Apre il pannello interattivo con bottoni per modalità presenza, media e lunghezza risposte. Include il pulsante indietro. |
| `/imposgiacomo 1\|2\|3` | Alias testuale: 1 solo tag/reply; 2 tag/reply più interventi casuali; 3 solo interventi casuali. |

Sono accettate anche maiuscole nei comandi e `/comando@NomeDelBot`.
In privato risponde al testo; nei gruppi risponde ai comandi, alle menzioni
`@NomeDelBot` e alle risposte ai propri messaggi. Gli altri messaggi vengono
osservati senza risposta. Le richieste troppo ravvicinate sono ignorate.

Lo stile permette linguaggio volgare e blasfemo quando il provider lo consente.
Non disabilita filtri e non promette risposte senza limiti. Le istruzioni di persona
non autorizzano scraping, doxxing o invenzione di informazioni sugli utenti.

### Identità amministratore

Controllo case-insensitive su username `SoyLe0` **e** ID numerico fissato.
Con `ADMIN_USER_ID` si verifica subito l'identità attesa. Senza, la prima
operazione privata autorizzata di @SoyLe0 fissa l'ID nella tabella `settings`.
Questo è un bootstrap basato sul possessore attuale dello username, non una
verifica di chi lo possedesse in passato. Se cambia username, i privilegi si
bloccano. Per un trasferimento legittimo modifica l'ID nella configurazione
e nella riga `settings.admin_id` tramite il pannello database.

## Memoria e media

- `messages`: testo osservato (massimo 16000 caratteri per messaggio), autore,
  chat, ID messaggio e una breve indicazione del reply. Nessuna eliminazione
  automatica; non vengono scaricati allegati o cronologie precedenti.
- `members`: nome, username corrente osservato, bio eventualmente accessibile,
  profilo sintetico, data dell'ultima osservazione e dell'ultimo profilo.
- `user_items`: note, attività e fatti salvati con `/ricorda`, separati per chat
  e autore. Le liste mostrano solo gli elementi di chi esegue il comando.
  In un gruppo il testo restituito è visibile al gruppo: non è una cassaforte privata.
  Il prompt conversazionale include fino a 10 fatti espliciti recenti, massimo
  300 caratteri ciascuno. `/scorda`, `/eliminanota` e `/eliminatodo` rimuovono
  solo l'elemento selezionato: i messaggi originali restano nella cronologia.
- Il profilo si aggiorna con `/conosci`; durante la conversazione viene anche
  aggiornato se ci sono almeno 20 messaggi dell'utente successivi all'ultimo profilo.
- Il prompt include persona, interlocutore, profilo, sintesi gruppo, ultimi
  `HISTORY_LIMIT` messaggi entro `CONTEXT_CHARS`, più fino a 4 ricordi della
  stessa chat/utente recuperati per parole pertinenti. I limiti sono in caratteri,
  non token: non garantiscono di stare sotto ogni quota TPM del provider.
- `/conosci gruppo` salva anche una sintesi dell'ultimo blocco elaborato.
  I profili individuali dei blocchi precedenti restano nel database.
- Archiviazione persistente non significa ricordo perfetto: la ricerca per
  parole e le sintesi possono omettere dettagli. Non viene promesso di ricordare
  ogni dato a ogni risposta. Le quote PostgreSQL restano finite: controlla spazio
  e backup dal tuo provider; il bot non cancella automaticamente ricordi.
- GIF/sticker nei gruppi: salva solo `file_id` e `file_unique_id`; deduplica per
  chat. Riutilizzo automatico solo se il modello propone `[MEDIA]`, passa una
  probabilità (8% di default) e sono trascorsi 180 secondi dall'ultimo media.
- `SHARE_GROUP_MEDIA=true` permette il riuso dei media osservati anche altrove,
  come richiesto. Con `false` il riuso automatico resta nella chat di origine.
  La lista GIF amministrativa è globale e separata dai media osservati.
- `/negra` invia la GIF esplicitamente richiesta, soggetta al rate limit dei
  comandi; il cooldown dei media automatici non impedisce questa azione.
  File rifiutati da Telegram vengono disabilitati e possono essere ripristinati
  reinviandoli. I `file_id` appartengono al bot originale: non riusare questo DB
  con un altro token/bot senza gestire la migrazione dei media.

Informa i partecipanti che il bot memorizza i messaggi visibili e invia porzioni
di contesto ai provider. Non condivide testo/profili tra chat. Non rileva in
automatico messaggi cancellati o utenti usciti: i record persistono. Per richieste
di cancellazione o correzione il gestore interviene nel database; non ci sono
endpoint HTTP che espongono memorie o segreti.

## Variabili ambiente

| Variabile | Default / significato |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Obbligatoria, token BotFather. |
| `DATABASE_URL` | Obbligatoria, URI PostgreSQL con TLS del provider. |
| `GROQ_API_KEY` | Obbligatoria, chiave Groq. |
| `AI_MODEL` | `llama-3.3-70b-versatile`; verificare quote e permessi del proprio piano Groq. |
| `OPENROUTER_API_KEY` | Vuota: fallback disabilitato. |
| `FALLBACK_MODEL` | `openrouter/free`, oppure modello `:free`. |
| `ADMIN_USER_ID` | Vuoto/0: bootstrap username; meglio ID numerico di @SoyLe0. |
| `PORT` | `10000`; Render lo fornisce automaticamente. |
| `AI_TIMEOUT_SECONDS` | `25`, intervallo 1–60, timeout totale per singolo provider. |
| `AI_MAX_TOKENS` | `1200`, intervallo 128–4096; include l'eventuale ragionamento del modello. |
| `HISTORY_LIMIT` | `16`, intervallo 1–100. |
| `CONTEXT_CHARS` | `12000`, intervallo 2000–24000 per la cronologia; persona, profili e richiesta hanno limiti separati. |
| `PROFILE_BATCH_SIZE` | `8`, intervallo 1–30. Un profilo costa una richiesta AI. |
| `USER_COOLDOWN_SECONDS` | `8`, minimo 0; stesso utente anche tra chat diverse. |
| `CHAT_COOLDOWN_SECONDS` | `3`, minimo 0. |
| `GLOBAL_AI_RPM` | `20`, intervallo 1–100; include fallback e sintesi, è un limite locale di richieste, non di token. |
| `MEDIA_PROBABILITY` | `0.08`, tra 0 e 1; `0` disattiva il riuso spontaneo. |
| `MEDIA_COOLDOWN_SECONDS` | `180`, minimo 0, persistente per chat. |
| `SHARE_GROUP_MEDIA` | `true`; `false` per limitare il riuso spontaneo al gruppo di origine. |
| `LOG_LEVEL` | `INFO`; i log non includono prompt, chiavi, URL PostgreSQL o token Telegram. |

Il limite locale richieste/minuto e i cooldown comandi ripartono al riavvio.
Le quote ufficiali restano applicate dai provider. `/help` e gestione GIF admin
non consumano AI e non sono soggetti al cooldown dei comandi AI.

## Esecuzione locale e test

```sh
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell, in alternativa:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Compila .env con le tue credenziali.
python bot.py
```

Controlli senza credenziali, con Python 3.12:

```sh
python -m py_compile bot.py
python -c "import bot, telegram, httpx, aiohttp, psycopg, psycopg_pool"
python -m unittest discover -s tests -v
```

I test automatici usano un trasporto HTTP simulato per verificare fallback,
rifiuti, timeout, rate limiting, menzioni e chunking Unicode. Non richiedono
token. Il test PostgreSQL opzionale in `tests/test_postgres.py` usa
`TEST_DATABASE_URL`: **solo un database vuoto di test dedicato**, perché pulisce
le tabelle dello schema del bot prima e dopo i test. Senza variabile viene saltato.

### Verifica reale dopo il deploy

1. `/health` diventa `running`; in privato il bot risponde.
2. @SoyLe0 apre `/listaaggiorna`, invia due GIF e fa `/stop`; un altro account è respinto.
3. In gruppo un utente scrive, poi un altro risponde con `/negra`: menzione e GIF arrivano in ordine.
4. Cambia `/persona`, esegui `/conosci` in reply; riavvia il servizio e verifica persona, profilo e GIF.
5. Controlla che il bot ignori conversazioni di gruppo non indirizzate e che il riuso spontaneo sia raro.

Non sono incluse credenziali. I test Telegram/Groq/PostgreSQL live e il deploy
richiedono i tuoi account; il pacchetto non implica che siano stati eseguiti.

## Affidabilità e diagnosi

- Una lease PostgreSQL di 60 secondi, rinnovata ogni 15, assegna il polling a
  una sola istanza cooperante. Durante il rolling deploy la nuova istanza può
  rispondere `/health` con `standby` e HTTP 200, permettendo a Render di fermare
  quella vecchia. Subentra entro circa 60 secondi se la vecchia muore senza pulizia.
  Mantieni un solo Web Service e non avviare copie che usano un altro database.
- La health a regime controlla che il ciclo abbia verificato DB e Telegram
  recentemente. Non consuma quota AI e non misura la salute dei provider AI.
  `standby` significa processo pronto ma **non ancora responsabile del polling**.
- Se il database o la verifica Telegram falliscono, il processo termina per
  consentire il riavvio. Errori transitori del polling sono gestiti da PTB;
  `Conflict` arresta il processo e richiede di eliminare l'altra istanza.
- Gli aggiornamenti sono processati in sequenza: niente corse tra `/stop` e
  GIF o tra due modifiche di persona. Un comando `/conosci gruppo` può però
  ritardare le risposte delle altre chat: abbassa `PROFILE_BATCH_SIZE` se serve.
- L'avvio del polling elimina l'eventuale webhook precedente tramite PTB.
  Usa questo token esclusivamente con questo bot. Non scarta intenzionalmente
  gli aggiornamenti pendenti. Telegram può comunque perderli dopo downtime
  prolungato; un crash fra consegna Telegram, risposta e commit non offre
  garanzie exactly-once. I messaggi archiviati sono deduplicati per chat/ID.
- Errori quota AI: aspetta il ripristino, riduci history/profili, controlla le
  quote nella console. Una chiave errata non viene nascosta dal fallback.
- Profilo sconosciuto: usa reply o fai scrivere l'utente nel gruppo visibile.
- Health 503 persistente: verifica credenziali, rete, SSL e permessi SQL.
- Lista GIF vuota: termina l'acquisizione con `/stop`; le bozze non sono ancora pubblicate.

Riferimenti tecnici: [python-telegram-bot async](https://docs.python-telegram-bot.org/en/stable/telegram.ext.application.html),
[pool PostgreSQL asincrono](https://www.psycopg.org/psycopg3/docs/advanced/pool.html).
