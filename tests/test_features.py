import ast
import copy
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from bot import BotService, Config, Store
from features import AI_TOOLS, CATALOG, Features, calculate, quiet_now, should_reply, source_text
from settings_ui import panel

STATE = dict(presence_mode='mentioned', media_enabled=True, response_length='short',
             tone='volgare', paused_until=None, quiet_start=None, quiet_end=None,
             random_probability=.035, random_cooldown=600, random_sent_at=None)


class MemoryDB:
    """SQL recording fake; exercises real command dispatch without external credentials."""
    def __init__(self):
        self.state = copy.deepcopy(STATE)
        self.calls = []
        self.rows = []

    async def run(self, sql, args=(), one=False):
        self.calls.append((sql, args))
        if sql.startswith('UPDATE chats SET'):
            keys = sql.split(' SET ', 1)[1].split(' WHERE ', 1)[0].split(',')
            for i, key in enumerate(keys):
                field = key.split('=')[0].strip()
                if field in self.state and i < len(args)-1:
                    self.state[field] = args[i]
        if sql.startswith('SELECT * FROM chats'):
            return self.state.copy()
        if one:
            return dict(self.state, id=7, profile='Profilo salvato', body='Una nota',
                        messaggi=2, utenti=1, primo='oggi', ultimo='oggi')
        return self.rows


def service():
    db = MemoryDB()
    s = BotService(Config('123:fake', 'unused', 'fake'), db, SimpleNamespace(ask=AsyncMock(return_value='Risultato AI')))
    s.send = AsyncMock()
    return s


def message():
    return SimpleNamespace(chat_id=-100, message_id=42, from_user=SimpleNamespace(id=123),
        reply_to_message=None, reply_poll=AsyncMock(), reply_text=AsyncMock())


class CommandTests(unittest.IsolatedAsyncioTestCase):
    pass


ARGS = {
    'ricorda': 'Preferisco esempi Python', 'nota': 'Appunto', 'todo': 'Controllare deploy',
    'cerca': 'deploy', 'scorda': '7', 'legginota': '7', 'eliminanota': '7',
    'completa': '7', 'riapri': '7', 'eliminatodo': '7',
    'sondaggio': 'Quando? | Oggi | Domani', 'calcola': '(2+3)*4',
    'conta': 'uno due', 'estrailink': 'https://example.org', 'silenzio': '23-8', 'frequenza': '3 10',
}


def command_case(name):
    async def test(self):
        s, m = service(), message()
        consumed = await s.features.handle(m, None, '/' + name, ARGS.get(name, 'Testo di prova' if name in AI_TOOLS else ''))
        self.assertTrue(consumed)
        if name in AI_TOOLS:
            s.ai.ask.assert_awaited_once()
            self.assertEqual(s.send.await_args.args[1], 'Risultato AI')
        elif name == 'sondaggio':
            m.reply_poll.assert_awaited_once_with('Quando?', ['Oggi', 'Domani'], is_anonymous=True, do_quote=False)
        else:
            self.assertGreater(s.send.await_count, 0)
        if name == 'calcola':
            self.assertEqual(s.send.await_args.args[1], '20')
        if name == 'conta':
            self.assertIn('Parole: 2', s.send.await_args.args[1])
        if name in ('ricorda', 'nota', 'todo'):
            sql, args = s.db.calls[-1]
            self.assertEqual(args[:2], (-100, 123))
            self.assertIn('INSERT INTO user_items', sql)
    return test


for command in CATALOG:
    setattr(CommandTests, 'test_command_' + command, command_case(command))


class RegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_settings_buttons_are_handled_and_persist(self):
        cases = {'presence': [('mentioned', 'presence_mode'), ('mentioned_random', 'presence_mode'), ('random', 'presence_mode')],
                 'media': [('off', 'media_enabled'), ('on', 'media_enabled')],
                 'length': [('long', 'response_length'), ('short', 'response_length')],
                 'tone': [('neutro', 'tone'), ('volgare', 'tone')], 'frequency': [('rare', 'random_probability')]}
        s = service()
        for page, pairs in cases.items():
            for value, field in pairs:
                query = SimpleNamespace(data=f'settings:set_{page}:{value}', from_user=SimpleNamespace(id=123),
                    message=SimpleNamespace(chat_id=-100, is_accessible=True), answer=AsyncMock(), edit_message_text=AsyncMock())
                await s.settings_callback(SimpleNamespace(callback_query=query), None)
                query.answer.assert_awaited_once()
                query.edit_message_text.assert_awaited_once()
                self.assertEqual(s.db.state[field], value == 'on' if page == 'media' else .01 if page == 'frequency' else value)
        for page in ('home', 'presence', 'media', 'length', 'tone', 'frequency', 'close'):
            query.data = 'settings:' + page
            await s.settings_callback(SimpleNamespace(callback_query=query), None)

    async def test_foreign_callback_cannot_mutate_sql(self):
        s = service()
        q = SimpleNamespace(data='settings:set_presence:invalid', message=SimpleNamespace(chat_id=-100,is_accessible=True),
                            from_user=SimpleNamespace(id=123), answer=AsyncMock())
        await s.settings_callback(SimpleNamespace(callback_query=q), None)
        self.assertEqual(s.db.calls, [])

    async def test_item_read_delete_update_scoped_to_owner_and_chat(self):
        for cmd in ('legginota', 'eliminanota', 'eliminatodo', 'scorda', 'completa', 'riapri'):
            s = service()
            await s.features.handle(message(), None, '/' + cmd, '999')
            sql, args = s.db.calls[-1]
            self.assertIn('chat_id=%s AND user_id=%s', sql)
            self.assertEqual(args[-4:-2], (-100, 123))
            self.assertEqual(args[-1], 999)

    async def test_empty_ai_input_makes_no_request(self):
        for cmd in AI_TOOLS:
            s = service()
            await s.features.handle(message(), None, '/' + cmd, '')
            s.ai.ask.assert_not_awaited()
            self.assertIn('Uso:', s.send.await_args.args[1])

    async def test_rate_limit_stops_all_new_commands(self):
        s = service()
        s.rate_allowed = lambda *args: False
        for cmd in CATALOG:
            self.assertTrue(await s.features.handle(message(), None, '/' + cmd, 'testo'))
        s.send.assert_not_awaited()
        s.ai.ask.assert_not_awaited()
        self.assertEqual(s.db.calls, [])

    async def test_invalid_numeric_input_does_not_write(self):
        for cmd, arg in [('frequenza','nan 10'),('frequenza','21 10'),('pausa','-1'),
                         ('silenzio','8-08'),('silenzio','25-8'),('eliminanota',"1 OR 1=1")]:
            s = service()
            await s.features.handle(message(), None, '/' + cmd, arg)
            self.assertEqual(s.db.calls, [])

    async def test_pool_retry_replaces_failed_pool(self):
        failed = SimpleNamespace(open=AsyncMock(side_effect=TimeoutError()), close=AsyncMock())
        conn = SimpleNamespace(execute=AsyncMock())
        manager = MagicMock()
        manager.__aenter__ = AsyncMock(return_value=conn)
        manager.__aexit__ = AsyncMock(return_value=False)
        good = SimpleNamespace(open=AsyncMock(), close=AsyncMock(), connection=lambda: manager)
        store = Store('unused')
        with patch.object(store, 'new_pool', side_effect=[failed, good]) as factory, patch('bot.asyncio.sleep', new=AsyncMock()):
            await store.start()
        self.assertIs(store.pool, good)
        self.assertEqual(factory.call_count, 2)
        failed.close.assert_awaited_once()
        good.close.assert_not_awaited()


class PureTests(unittest.TestCase):
    def test_catalog_has_fifty_distinct_telegram_commands(self):
        self.assertEqual(len(CATALOG), 50)
        import re
        for name in CATALOG:
            self.assertTrue(re.fullmatch('[a-z_]{1,32}', name))

    def test_calculator_rejects_code_and_expensive_expressions(self):
        self.assertEqual(calculate('2**3+4/2'), 10)
        for expression in ["__import__('os').system('echo bad')", '2**100000000', '1/0', '[1]*999999', 'True', '1e999', '(-1)**0.5']:
            with self.assertRaises(ValueError):
                calculate(expression)

    def test_three_modes_and_random_probability(self):
        for mode in ('mentioned', 'mentioned_random', 'random'):
            row = dict(STATE, presence_mode=mode)
            self.assertEqual(should_reply(row, True, draw=0), mode != 'random')
            self.assertEqual(should_reply(row, False, draw=0), mode != 'mentioned')
            self.assertFalse(should_reply(row, False, draw=.99))
            self.assertTrue(should_reply(row, True, private=True))

    def test_pause_cooldown_and_quiet_night(self):
        now = datetime(2026, 9, 15, 22, tzinfo=timezone.utc)
        row = dict(STATE, presence_mode='mentioned_random', quiet_start=23, quiet_end=8)
        self.assertTrue(quiet_now(row, now))
        self.assertFalse(should_reply(row, False, draw=0, now=now))
        self.assertTrue(should_reply(row, True, draw=0, now=now))
        row = dict(STATE, presence_mode='random', random_sent_at=now-timedelta(seconds=10))
        self.assertFalse(should_reply(row, False, draw=0, now=now))
        row['paused_until'] = now+timedelta(minutes=10)
        self.assertFalse(should_reply(row, True, private=True, now=now))

    def test_panel_marks_actual_selection_and_callback_sizes(self):
        for page in ('home','presence','media','length','tone','frequency'):
            text, keyboard = panel(STATE, page)
            self.assertTrue(text)
            for row in keyboard.inline_keyboard:
                for button in row:
                    self.assertLessEqual(len(button.callback_data.encode()), 64)
            if page == 'presence':
                self.assertEqual([b.text for r in keyboard.inline_keyboard for b in r if b.text.startswith('✓')], ['✓ Solo tag / reply'])

    def test_polling_receives_callback_updates(self):
        tree = ast.parse((Path(__file__).parents[1] / 'bot.py').read_text(encoding='utf-8'))
        polls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'start_polling']
        self.assertEqual(len(polls), 1)
        allowed = next(k.value for k in polls[0].keywords if k.arg == 'allowed_updates')
        self.assertIn('callback_query', ast.literal_eval(allowed))

    def test_source_reply_does_not_add_counted_labels(self):
        m = message()
        m.reply_to_message = SimpleNamespace(text='uno due', caption=None)
        self.assertEqual(source_text(m, ''), 'uno due')
        with self.assertRaises(ValueError):
            source_text(m, 'x'*8001)
