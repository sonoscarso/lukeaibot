"""Fifty discoverable commands. No external browsing or code execution."""
from __future__ import annotations

import ast
import math
import operator
import random
import re
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


AI_TOOLS = {
    "riassumi": ("Riassunto fedele", "Riassumi il testo in punti, mantenendo fatti e riserve."),
    "traduci": ("Traduzione nella lingua indicata", "Traduci nella lingua richiesta all'inizio del testo. Se assente usa italiano; conserva registro e significato."),
    "correggi": ("Correzione grammaticale", "Correggi ortografia e grammatica senza cambiare significato. Restituisci il testo corretto."),
    "riscrivi": ("Riscrittura con stile richiesto", "Riscrivi secondo lo stile richiesto, mantenendo i fatti. In assenza di stile rendi il testo chiaro e diretto."),
    "semplifica": ("Testo in linguaggio semplice", "Semplifica per un principiante, spiegando i termini tecnici."),
    "spiega": ("Spiegazione con esempio", "Spiega il concetto e includi un esempio concreto e un limite dell'analogia."),
    "approfondisci": ("Analisi estesa", "Approfondisci meccanismo, implicazioni e limiti. Distingui fatti e ipotesi."),
    "confronta": ("Confronto tra alternative", "Confronta le alternative indicate per criteri pratici, vantaggi e svantaggi; evidenzia dati mancanti."),
    "procontro": ("Vantaggi e svantaggi", "Elenca pro e contro della proposta con condizioni e rischi."),
    "verificatesi": ("Analisi logica di una tesi", "Analizza coerenza, assunzioni e possibili controesempi. Non hai accesso al web: non presentare questa analisi come verifica di fatti attuali né inventare fonti."),
    "estrai": ("Estrazione di dati dal testo", "Estrai nomi, date, cifre e vincoli presenti. Non aggiungere dati mancanti."),
    "azioni": ("Azioni, responsabili e scadenze", "Estrai azioni operative, responsabili e scadenze. Usa 'non indicato' quando mancano."),
    "titoli": ("Cinque titoli pertinenti", "Proponi cinque titoli precisi per il testo senza clickbait."),
    "scaletta": ("Scaletta di un documento", "Crea una scaletta ordinata per il documento richiesto, con punti da sviluppare."),
    "email": ("Bozza email", "Scrivi una bozza email con oggetto e corpo, coerente con la richiesta. Non inviare nulla e non inventare recapiti."),
    "risposta": ("Bozza di risposta a un messaggio", "Prepara una risposta pronta da copiare al messaggio fornito nello stile richiesto. Non inviarla a terzi."),
    "codice": ("Snippet di codice spiegato", "Proponi codice per il compito indicato e spiega come usarlo. Non eseguirlo e non dichiarare test eseguiti."),
    "debug": ("Diagnosi di codice o errore", "Analizza il codice/log, identifica cause probabili e correzione minima. Non inventare risultati di esecuzione."),
    "documenta": ("Documentazione di codice", "Documenta interfaccia, parametri, ritorni, errori ed esempio d'uso del codice fornito."),
    "test": ("Casi di test per codice", "Proponi test di comportamento, casi limite e input non validi del codice fornito; non affermare di averli eseguiti."),
}
LOCAL_TOOLS = {
    "comandi": "Catalogo delle 50 funzioni, per categoria",
    "ping": "Verifica reattività del bot e database",
    "stato": "Modello e impostazioni attive della chat",
    "id": "ID numerici della chat, utente e messaggio",
    "statistiche": "Conteggi di messaggi e utenti osservati",
    "topattivi": "Dieci partecipanti più attivi nei messaggi osservati",
    "mieistat": "Statistiche personali nella chat",
    "cerca": "Cerca testo nella cronologia della chat",
    "profilo": "Legge il proprio profilo salvato senza nuova chiamata AI",
    "ricorda": "Salva un fatto esplicito personale per la memoria AI",
    "ricordi": "Elenca i propri fatti espliciti salvati",
    "scorda": "Rimuove un proprio fatto esplicito tramite ID",
    "nota": "Salva una nota personale nella chat",
    "note": "Elenca le proprie note, con pagine",
    "legginota": "Legge una propria nota tramite ID",
    "eliminanota": "Rimuove una propria nota tramite ID",
    "todo": "Aggiunge un'attività personale",
    "attivita": "Elenca le proprie attività aperte",
    "completate": "Elenca le proprie attività completate",
    "completa": "Segna un'attività come completata",
    "riapri": "Riapre un'attività completata",
    "eliminatodo": "Rimuove una propria attività tramite ID",
    "sondaggio": "Crea un sondaggio anonimo Telegram",
    "calcola": "Calcolo aritmetico senza eseguire codice",
    "conta": "Conta parole, caratteri e righe di un testo",
    "estrailink": "Estrae URL HTTP(S) unici senza aprirli",
    "pausa": "Sospende le risposte conversazionali per alcuni minuti",
    "riprendi": "Riattiva subito le risposte conversazionali",
    "silenzio": "Configura orari silenziosi per interventi casuali",
    "frequenza": "Regola probabilità e intervallo degli interventi casuali",
}
CATALOG = {**{k: v[0] for k, v in AI_TOOLS.items()}, **LOCAL_TOOLS}

EXTRA_SCHEMA = """
ALTER TABLE chats ADD COLUMN IF NOT EXISTS tone TEXT NOT NULL DEFAULT 'volgare';
ALTER TABLE chats ADD COLUMN IF NOT EXISTS paused_until TIMESTAMPTZ;
ALTER TABLE chats ADD COLUMN IF NOT EXISTS quiet_start INTEGER;
ALTER TABLE chats ADD COLUMN IF NOT EXISTS quiet_end INTEGER;
ALTER TABLE chats ADD COLUMN IF NOT EXISTS random_probability DOUBLE PRECISION NOT NULL DEFAULT 0.035;
ALTER TABLE chats ADD COLUMN IF NOT EXISTS random_cooldown INTEGER NOT NULL DEFAULT 600;
ALTER TABLE chats ADD COLUMN IF NOT EXISTS random_sent_at TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS user_items (
 id BIGSERIAL PRIMARY KEY, chat_id BIGINT NOT NULL REFERENCES chats(chat_id),
 user_id BIGINT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('note','todo','memory')),
 body TEXT NOT NULL, done BOOLEAN NOT NULL DEFAULT false, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS user_items_scope ON user_items(chat_id,user_id,kind,id DESC);
"""


def calculate(expression):
    """Small arithmetic grammar, bounded in size, depth, exponent and result."""
    if not expression or len(expression) > 200:
        raise ValueError("Usa un'espressione di massimo 200 caratteri.")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise ValueError("Espressione non valida.") from None
    binary = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
              ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}

    def visit(node, depth=0):
        if depth > 20:
            raise ValueError("Espressione troppo complessa.")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            result = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            result = visit(node.operand, depth + 1) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in binary:
            left, right = visit(node.left, depth + 1), visit(node.right, depth + 1)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Esponente massimo: 10.")
            result = binary[type(node.op)](left, right)
        else:
            raise ValueError("Sono ammessi solo numeri, parentesi e + - * / // % **.")
        if type(result) not in (int, float) or not math.isfinite(result) or abs(result) > 1e15:
            raise ValueError("Risultato fuori limite (10^15).")
        return result
    try:
        return visit(tree.body)
    except (ZeroDivisionError, OverflowError):
        raise ValueError("Divisione per zero o risultato fuori limite.") from None


def quiet_now(settings, now=None):
    start, end = settings.get('quiet_start'), settings.get('quiet_end')
    if start is None or end is None:
        return False
    hour = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo('Europe/Rome')).hour
    return start <= hour < end if start < end else hour >= start or hour < end


def should_reply(settings, addressed, private=False, draw=None, now=None):
    now = now or datetime.now(timezone.utc)
    if settings.get('paused_until') and settings['paused_until'] > now:
        return False
    if private:
        return True
    mode = settings['presence_mode']
    if addressed:
        return mode != 'random'
    if mode == 'mentioned' or quiet_now(settings, now):
        return False
    last = settings.get('random_sent_at')
    if last and (now - last).total_seconds() < settings.get('random_cooldown', 600):
        return False
    return (random.random() if draw is None else draw) < settings.get('random_probability', .035)


def source_text(message, arg):
    reply = message.reply_to_message
    quoted = (reply.text or reply.caption or '') if reply else ''
    text = (arg + ('\n\n' + quoted if quoted else '')).strip()
    if len(text) > 8000:
        raise ValueError('Testo troppo lungo: massimo 8000 caratteri.')
    return text


class Features:
    def __init__(self, service):
        self.s, self.db = service, service.db

    async def handle(self, message, context, command, arg):
        name = command.lstrip('/')
        if name not in CATALOG:
            return False
        if not self.s.rate_allowed(message.chat_id, message.from_user.id):
            return True
        try:
            if name in AI_TOOLS:
                await self.ai_tool(message, name, arg)
            else:
                await self.local_tool(message, context, name, arg.strip())
        except ValueError as exc:
            await self.s.send(message, str(exc))
        return True

    async def ai_tool(self, message, name, arg):
        text = source_text(message, arg)
        if not text:
            raise ValueError(f"Uso: /{name} <testo o richiesta>, oppure rispondi a un messaggio.")
        chat = await self.db.run("SELECT * FROM chats WHERE chat_id=%s", (message.chat_id,), one=True)
        length = "Sii conciso." if chat['response_length'] == 'short' else "Fornisci dettagli utili."
        # Text utilities use only the supplied text, never unrelated private memories.
        result = await self.s.ai.ask([
            {'role': 'system', 'content': self.s.base_prompt + '\nTono attivo: ' + chat['tone'] +
             ' (neutro: senza parolacce; diretto: senza forzarle; volgare: consentite esplicitamente).' +
             '\nCompito: ' + AI_TOOLS[name][1] + '\n' + length},
            {'role': 'user', 'content': text}])
        await self.s.send(message, result.replace('[MEDIA]', '').strip() or 'Nessun testo restituito.')

    async def local_tool(self, m, context, name, arg):
        cid, uid = m.chat_id, m.from_user.id
        send = lambda text: self.s.send(m, text)
        if name == 'comandi':
            category = arg or 'tutti'
            selected = AI_TOOLS if category == 'ai' else LOCAL_TOOLS if category == 'strumenti' else CATALOG
            if category not in ('ai', 'strumenti', 'tutti'):
                raise ValueError('Uso: /comandi [ai|strumenti|tutti]')
            await send('50 funzioni — /comandi ai o /comandi strumenti\n\n' + '\n'.join('/' + k + ' — ' + CATALOG[k] for k in selected))
        elif name == 'ping':
            start = time.monotonic()
            await self.db.run('SELECT 1')
            await send(f"Bot attivo. Risposta database: {(time.monotonic()-start)*1000:.0f} ms.")
        elif name == 'stato':
            row = await self.db.run('SELECT * FROM chats WHERE chat_id=%s', (cid,), one=True)
            await send(f"Modello: {self.s.c.model}\nPresenza: {row['presence_mode']}\nTono: {row['tone']}\n"
                       f"Media: {row['media_enabled']}\nRisposte: {row['response_length']}\nPausa fino a: {row['paused_until']}\n"
                       f"Casuale: {row['random_probability']*100:g}%, minimo {row['random_cooldown']} secondi.")
        elif name == 'id':
            await send(f"Utente: {uid}\nChat: {cid}\nMessaggio: {m.message_id}")
        elif name in ('statistiche', 'mieistat'):
            row = await self.db.run("""SELECT count(*) AS messaggi, count(DISTINCT user_id) AS utenti,
                min(created_at) AS primo, max(created_at) AS ultimo FROM messages
                WHERE chat_id=%s AND role='user' AND (%s::bigint IS NULL OR user_id=%s)""",
                (cid, uid if name == 'mieistat' else None, uid), one=True)
            await send('\n'.join(f'{k}: {v}' for k, v in row.items()) + '\nSolo cronologia osservata dal bot.')
        elif name == 'topattivi':
            rows = await self.db.run("""SELECT m.user_id,u.name,count(*) AS n FROM messages m
                JOIN members u ON u.chat_id=m.chat_id AND u.user_id=m.user_id
                WHERE m.chat_id=%s AND m.role='user' GROUP BY m.user_id,u.name ORDER BY n DESC LIMIT 10""", (cid,))
            await send('\n'.join(f"{r['name']}: {r['n']} messaggi" for r in rows) or 'Nessun dato.')
        elif name == 'cerca':
            if not 3 <= len(arg) <= 100:
                raise ValueError('Uso: /cerca <testo di 3–100 caratteri>')
            rows = await self.db.run("""SELECT message_id,user_id,body FROM messages WHERE chat_id=%s
                AND message_id<>%s AND strpos(lower(body),lower(%s))>0 ORDER BY message_id DESC LIMIT 10""", (cid, m.message_id, arg))
            await send('\n\n'.join(f"Messaggio {r['message_id']} — utente {r['user_id']}\n{r['body'][:500]}" for r in rows) or 'Nessun risultato in questa chat.')
        elif name == 'profilo':
            row = await self.db.run('SELECT profile FROM members WHERE chat_id=%s AND user_id=%s', (cid, uid), one=True)
            await send(row['profile'] or 'Profilo non ancora sintetizzato. Usa /conosci in reply.')
        elif name in ('ricorda', 'nota', 'todo'):
            body = source_text(m, arg)
            if not body or len(body) > 2000:
                raise ValueError(f'Uso: /{name} <testo di massimo 2000 caratteri> o reply.')
            kind = {'ricorda': 'memory', 'nota': 'note', 'todo': 'todo'}[name]
            row = await self.db.run("INSERT INTO user_items(chat_id,user_id,kind,body) VALUES(%s,%s,%s,%s) RETURNING id", (cid, uid, kind, body), one=True)
            await send(f"Salvato con ID {row['id']}.")
        elif name in ('ricordi', 'note', 'attivita', 'completate'):
            page = int(arg or '1')
            if not 1 <= page <= 10000:
                raise ValueError('Pagina non valida (1–10000).')
            kind = {'ricordi': 'memory', 'note': 'note', 'attivita': 'todo', 'completate': 'todo'}[name]
            rows = await self.db.run("""SELECT id,body,done FROM user_items WHERE chat_id=%s AND user_id=%s
                AND kind=%s AND (%s <> 'todo' OR done=%s) ORDER BY id DESC LIMIT 10 OFFSET %s""",
                (cid, uid, kind, kind, name == 'completate', (page-1)*10))
            await send(f'Pagina {page}. Per continuare: /{name} {page+1}\n\n' +
                       ('\n\n'.join(f"#{r['id']} {r['body'][:500]}" for r in rows) or 'Nessun elemento.'))
        elif name in ('scorda', 'legginota', 'eliminanota', 'completa', 'riapri', 'eliminatodo'):
            if not arg.isdigit() or len(arg) > 18:
                raise ValueError(f'Uso: /{name} <ID numerico>')
            kind = 'memory' if name == 'scorda' else 'note' if name in ('legginota', 'eliminanota') else 'todo'
            args = (cid, uid, kind, int(arg))
            where = ' WHERE chat_id=%s AND user_id=%s AND kind=%s AND id=%s'
            if name == 'legginota':
                row = await self.db.run('SELECT body FROM user_items' + where, args, one=True)
                await send(row['body'] if row else 'Nota non trovata tra le tue note in questa chat.')
            else:
                if name in ('completa', 'riapri'):
                    row = await self.db.run('UPDATE user_items SET done=%s' + where + ' RETURNING id', (name == 'completa', *args), one=True)
                else:
                    row = await self.db.run('DELETE FROM user_items' + where + ' RETURNING id', args, one=True)
                await send('Operazione salvata.' if row else 'Elemento non trovato tra i tuoi in questa chat.')
        elif name == 'sondaggio':
            parts = [p.strip() for p in arg.split('|')]
            if not 3 <= len(parts) <= 11 or not all(parts) or len(parts[0]) > 200 or any(len(p)>80 for p in parts[1:]) or len(set(parts[1:])) != len(parts[1:]):
                raise ValueError('Uso: /sondaggio Domanda | Opzione A | Opzione B (2–10 opzioni uniche, max 80 caratteri; domanda max 200)')
            await m.reply_poll(parts[0], parts[1:], is_anonymous=True, do_quote=False)
        elif name == 'calcola':
            await send(str(calculate(arg)))
        elif name == 'conta':
            text = source_text(m, arg)
            if not text:
                raise ValueError('Uso: /conta <testo> o reply.')
            await send(f"Caratteri: {len(text)}\nParole: {len(re.findall(r'\S+', text))}\nRighe: {len(text.splitlines())}")
        elif name == 'estrailink':
            text = source_text(m, arg)
            if not text:
                raise ValueError('Uso: /estrailink <testo> o reply.')
            links = list(dict.fromkeys(re.findall(r'https?://[^\s<>]+', text)))[:30]
            await send('\n'.join(links) or 'Nessun URL HTTP(S) trovato.')
        elif name == 'pausa':
            minutes = int(arg or '30')
            if not 1 <= minutes <= 1440:
                raise ValueError('Uso: /pausa <minuti 1–1440>, default 30.')
            await self.db.run("UPDATE chats SET paused_until=now()+%s*interval '1 minute' WHERE chat_id=%s", (minutes, cid))
            await send(f'Conversazione sospesa per {minutes} minuti. Comandi disponibili; /riprendi riattiva.')
        elif name == 'riprendi':
            await self.db.run('UPDATE chats SET paused_until=NULL WHERE chat_id=%s', (cid,))
            await send('Conversazione riattivata.')
        elif name == 'silenzio':
            if arg == 'off':
                start, end = None, None
            else:
                match = re.fullmatch(r'(\d{1,2})-(\d{1,2})', arg)
                if not match or not all(0 <= int(v) <= 23 for v in match.groups()) or int(match[1]) == int(match[2]):
                    raise ValueError('Uso: /silenzio 23-8 oppure /silenzio off. Fuso Europe/Rome, solo interventi casuali.')
                start, end = map(int, match.groups())
            await self.db.run('UPDATE chats SET quiet_start=%s,quiet_end=%s WHERE chat_id=%s', (start, end, cid))
            await send('Orario silenzioso salvato (Europe/Rome).')
        elif name == 'frequenza':
            parts = arg.split()
            if len(parts) != 2:
                raise ValueError('Uso: /frequenza <percentuale 0–20> <minuti minimi 1–1440>, esempio: /frequenza 3 10')
            probability, minutes = float(parts[0]), int(parts[1])
            if not 0 <= probability <= 20 or not 1 <= minutes <= 1440:
                raise ValueError('Percentuale 0–20 e minuti 1–1440.')
            await self.db.run('UPDATE chats SET random_probability=%s,random_cooldown=%s WHERE chat_id=%s', (probability/100, minutes*60, cid))
            await send(f'Interventi casuali: {probability:g}% per messaggio non indirizzato, distanti almeno {minutes} minuti.')
