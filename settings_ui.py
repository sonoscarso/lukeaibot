"""Pure panel rendering; selected values always reflect persisted state."""
from telegram import InlineKeyboardButton as Button, InlineKeyboardMarkup

MODES = {'mentioned': 'Solo tag / reply', 'mentioned_random': 'Tag / reply + casuale', 'random': 'Solo casuale'}
TONES = {'volgare': 'Volgare e tagliente', 'diretto': 'Diretto', 'neutro': 'Neutro'}


def panel(row, page='home'):
    back = [Button('‹ Indietro', callback_data='settings:home')]
    if page == 'home':
        text = (f"Impostazioni della chat\n\nPresenza: {MODES[row['presence_mode']]}\n"
                f"Media: {'attivi' if row['media_enabled'] else 'disattivati'}\n"
                f"Risposte: {'lunghe' if row['response_length']=='long' else 'brevi'}\n"
                f"Tono: {TONES[row['tone']]}\n\nLe modifiche vengono salvate automaticamente.")
        rows = [[Button(label, callback_data='settings:' + name)] for name, label in
                [('presence', 'Quando intervengo'), ('media', 'Sticker e GIF'), ('length', 'Lunghezza risposte'),
                 ('tone', 'Tono'), ('frequency', 'Frequenza casuale'), ('close', 'Chiudi')]]
    elif page in ('presence', 'length', 'tone'):
        key = {'presence': 'presence_mode', 'length': 'response_length', 'tone': 'tone'}[page]
        values = MODES if page == 'presence' else TONES if page == 'tone' else {'short': 'Brevi', 'long': 'Lunghe'}
        text = {'presence': 'Quando intervengo\nI comandi restano disponibili. Il casuale si attiva sui nuovi messaggi del gruppo.',
                'length': 'Lunghezza risposte\nBrevi: una o due frasi. Lunghe: approfondite quando serve. Saluti e battute restano brevi. I comandi di analisi hanno lunghezze proprie.',
                'tone': 'Tono\nVolgare permette parolacce esplicite e battute taglienti.'}[page]
        rows = [[Button(('✓ ' if row[key] == value else '') + label,
                        callback_data=f'settings:set_{page}:{value}')] for value, label in values.items()] + [back]
    elif page == 'media':
        text = 'Sticker e GIF\nStato: ' + ('attivi' if row['media_enabled'] else 'disattivati')
        rows = [[Button('✓ Attivi' if row['media_enabled'] else 'Attiva', callback_data='settings:set_media:on')],
                [Button('Disattiva' if row['media_enabled'] else '✓ Disattivati', callback_data='settings:set_media:off')], back]
    elif page == 'frequency':
        text = (f"Interventi casuali: {row['random_probability']*100:g}% per messaggio, almeno "
                f"{row['random_cooldown']//60} minuti tra due interventi.\n\n"
                'Per valori personalizzati: /frequenza 3 10\nOrari silenziosi: /silenzio 23-8')
        rows = [[Button(label, callback_data=f'settings:set_frequency:{value}')]
                for value, label in [('rare', 'Rari: 1%, 30 minuti'), ('normal', 'Normali: 3%, 10 minuti'), ('often', 'Frequenti: 8%, 5 minuti')]] + [back]
    elif page == 'close':
        return 'Pannello chiuso. /imposgiacomino per riaprirlo.', None
    else:
        raise ValueError('Pagina non valida')
    return text, InlineKeyboardMarkup(rows)
