import asyncio
import html
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx

from bot import AI, AIUnavailable, BotService, Config, chunks, mention


def config(**kwargs):
    return Config(token="123:fake", database="postgresql://unused", groq_key="fake", **kwargs)


class TextTests(unittest.TestCase):
    def test_unicode_chunking_is_lossless_and_within_telegram_limit(self):
        text = "😃<&>à\n" * 3000
        parts = list(chunks(text))
        self.assertGreater(len(parts), 1)
        self.assertEqual("".join(parts), text)
        self.assertTrue(all(len(p.encode("utf-16-le")) // 2 <= 3500 for p in parts))

    def test_mention_cannot_inject_html(self):
        self.assertEqual(mention(42, '<b>"X"&'),
            '<a href="tg://user?id=42">&lt;b&gt;&quot;X&quot;&amp;</a>')

    def test_rate_limit_user_cross_chat_and_independent_users(self):
        service = BotService(config(), None, None)
        self.assertTrue(service.rate_allowed(1, 10))
        self.assertFalse(service.rate_allowed(2, 10))
        self.assertFalse(service.rate_allowed(1, 11))
        self.assertTrue(service.rate_allowed(2, 11))


class AITests(unittest.IsolatedAsyncioTestCase):
    async def call(self, handler, **kwargs):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await AI(config(**kwargs), client).ask([{"role": "user", "content": "ciao"}])

    async def test_technical_failure_uses_free_fallback(self):
        hosts = []
        def handler(request):
            hosts.append(request.url.host)
            if len(hosts) == 1:
                return httpx.Response(429)
            return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
        self.assertEqual(await self.call(handler, fallback_key="fake"), "ok")
        self.assertEqual(hosts, ["api.groq.com", "openrouter.ai"])

    async def test_refusal_does_not_use_fallback(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={"choices": [{"message": {"refusal": "Non consentito"}}]})
        self.assertEqual(await self.call(handler, fallback_key="fake"), "Non consentito")
        self.assertEqual(len(calls), 1)

    async def test_textual_refusal_is_returned_unchanged(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={"choices": [{"message": {"content": "Non posso aiutarti."}}]})
        self.assertEqual(await self.call(handler, fallback_key="fake"), "Non posso aiutarti.")
        self.assertEqual(len(calls), 1)

    async def test_content_filter_does_not_use_fallback(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={"choices": [{"finish_reason": "content_filter", "message": {}}]})
        self.assertIn("non consente", await self.call(handler, fallback_key="fake"))
        self.assertEqual(len(calls), 1)

    async def test_auth_and_policy_errors_do_not_fallback(self):
        for status in (400, 401, 403):
            calls = []
            def handler(request):
                calls.append(request)
                return httpx.Response(status)
            with self.assertRaises(AIUnavailable):
                await self.call(handler, fallback_key="fake")
            self.assertEqual(len(calls), 1)

    async def test_transport_failure_uses_fallback(self):
        calls = []
        def handler(request):
            calls.append(request)
            if len(calls) == 1:
                raise httpx.ReadTimeout("test")
            return httpx.Response(200, json={"choices": [{"message": {"content": "recovered"}}]})
        self.assertEqual(await self.call(handler, fallback_key="fake"), "recovered")

    async def test_wall_clock_timeout_is_bounded(self):
        async def handler(request):
            await asyncio.sleep(.1)
            return httpx.Response(200)
        with self.assertRaises(AIUnavailable):
            await self.call(handler, timeout=.01)

    async def test_malformed_response_does_not_fallback(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={"error": "unknown"})
        with self.assertRaises(AIUnavailable):
            await self.call(handler, fallback_key="fake")
        self.assertEqual(len(calls), 1)

    async def test_global_limit_counts_fallback(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(500)
        with self.assertRaises(AIUnavailable):
            await self.call(handler, fallback_key="fake", ai_rpm=1)
        self.assertEqual(len(calls), 1)


class TelegramTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_escapes_model_output_and_preserves_mention(self):
        db = SimpleNamespace(message=AsyncMock())
        message = SimpleNamespace(chat_id=1, reply_text=AsyncMock(return_value=SimpleNamespace(
            message_id=5, from_user=SimpleNamespace(id=99))))
        service = BotService(config(), db, None)
        body = '<a href="https://fake.invalid">x</a>' + "😀" * 3000
        prefix = mention(2, "<utente>") + " "
        await service.send(message, body, prefix)
        calls = message.reply_text.await_args_list
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].args[0].startswith(prefix + "&lt;a"))
        self.assertFalse(calls[1].args[0].startswith(prefix))
        self.assertEqual(db.message.await_count, 2)

    async def test_username_resolution_stays_in_chat(self):
        db = SimpleNamespace(run=AsyncMock(return_value={"user_id": 8}))
        service = BotService(config(), db, None)
        message = SimpleNamespace(chat_id=-123, reply_to_message=None)
        self.assertEqual(await service.target(message, "@TestUser"), {"user_id": 8})
        self.assertEqual(db.run.await_args.args[1], (-123, "testuser"))
        self.assertIsNone(await service.target(message, "@x' OR true"))


if __name__ == "__main__":
    unittest.main()
