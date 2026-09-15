"""Optional integration tests: use ONLY a disposable dedicated test database."""
import os
import unittest
from types import SimpleNamespace

from bot import Store


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "TEST_DATABASE_URL not configured")
class PostgresTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Store(os.environ["TEST_DATABASE_URL"])
        await self.db.start()
        await self.clear()

    async def clear(self):
        await self.db.run("""TRUNCATE settings,chats,members,messages,media,
            curated_gifs,gif_sessions,gif_drafts,runtime_lease CASCADE""")

    async def asyncTearDown(self):
        await self.clear()
        await self.db.pool.close()

    async def test_admin_pinned_to_id(self):
        self.assertFalse(await self.db.admin(SimpleNamespace(id=1, username="other")))
        self.assertTrue(await self.db.admin(SimpleNamespace(id=2, username="SoyLe0")))
        self.assertFalse(await self.db.admin(SimpleNamespace(id=3, username="SoyLe0")))
        self.assertFalse(await self.db.admin(SimpleNamespace(id=2, username="newname")))
        self.assertTrue(await self.db.admin(SimpleNamespace(id=2, username="SOYLE0")))

    async def test_gif_drafts_commit_and_restart(self):
        await self.db.run("INSERT INTO gif_sessions VALUES(2)")
        await self.db.run("INSERT INTO gif_drafts VALUES(2,'unique1','file1'),(2,'unique2','file2')")
        await self.db.pool.close()
        self.db = Store(os.environ["TEST_DATABASE_URL"])
        await self.db.start()
        self.assertEqual(await self.db.run("SELECT * FROM curated_gifs"), [])
        self.assertEqual(await self.db.save_gifs(2), 2)
        self.assertEqual(len(await self.db.run("SELECT * FROM curated_gifs")), 2)
        self.assertEqual(await self.db.run("SELECT * FROM gif_drafts"), [])
        self.assertIsNone(await self.db.save_gifs(2))

    async def test_history_deduplication_and_chat_isolation(self):
        await self.db.run("INSERT INTO chats(chat_id) VALUES(1),(2)")
        user = SimpleNamespace(id=5, full_name="Mario", username="mario")
        await self.db.member(1, user)
        await self.db.member(2, user)
        await self.db.message(1, 1, 5, "user", "primo")
        await self.db.message(1, 1, 5, "user", "duplicato")
        await self.db.message(2, 1, 5, "user", "altra chat")
        rows = await self.db.run("SELECT body FROM messages WHERE chat_id=1")
        self.assertEqual(rows, [{"body": "primo"}])
        await self.db.run("UPDATE members SET profile='profilo privato' WHERE chat_id=1")
        row = await self.db.run("SELECT profile FROM members WHERE chat_id=2", one=True)
        self.assertEqual(row['profile'], '')


if __name__ == "__main__":
    unittest.main()
