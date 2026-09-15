# Verifica del pacchetto

Data: 15 settembre 2026. Ambiente locale Windows, Python 3.12.

Esito:

- Installazione dipendenze in ambiente virtuale pulito: riuscita.
- `pip check`: nessuna dipendenza incompatibile.
- `python -m py_compile bot.py`: riuscito.
- Import `bot`, `telegram`, `httpx`, `aiohttp`, `psycopg`, `psycopg_pool`: riusciti.
- Costruzione di `telegram.ext.Application` con token fittizio: riuscita, PTB 22.8.
- Test automatici: **14 passati**, **3 saltati** perché `TEST_DATABASE_URL` non configurata.

Copertura dei test eseguiti: fallback tecnico, mancato fallback per rifiuti o
errori di autorizzazione, limite globale API, timeout totale e di trasporto,
risposte API malformate, escaping HTML, chunking Unicode senza perdita di testo,
menzione solo sul primo blocco, rate limit utente/chat e risoluzione username
limitata alla chat corrente.

I test saltati verificano su PostgreSQL reale: identità admin fissata all'ID,
persistenza delle bozze GIF attraverso riapertura della connessione e commit
della lista, deduplicazione messaggi e separazione delle memorie tra chat.
Sono forniti nel progetto per eseguirli con un database di test dedicato.

Non eseguiti: connessioni reali a Telegram, Groq, OpenRouter, Neon/Supabase;
deploy Render; verifica sul campo della latenza o dell'uptime. Mancano le
credenziali dell'utente. Il README contiene la checklist per questi controlli.
