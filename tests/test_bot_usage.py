import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.checker import BotUsageStats, TelegramBotManager


class BotUsageStatsTests(unittest.TestCase):
    def test_command_and_message_counters_are_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            stats_file = Path(directory) / "usage.json"
            stats = BotUsageStats(stats_file)
            stats.record_command("/stats", "success")
            stats.record_command("/unknown", "unknown")
            stats.record_command("/stats", "denied")
            stats.record_message(True)
            stats.record_message(False)

            loaded = BotUsageStats(stats_file).snapshot()

        self.assertEqual(loaded["commands_received"], 3)
        self.assertEqual(loaded["commands_allowed"], 2)
        self.assertEqual(loaded["commands_denied"], 1)
        self.assertEqual(loaded["commands_unknown"], 1)
        self.assertEqual(loaded["commands_succeeded"], 1)
        self.assertEqual(loaded["messages_sent"], 1)
        self.assertEqual(loaded["messages_failed"], 1)
        self.assertEqual(loaded["commands"]["/stats"], 2)

    def test_stats_command_is_available_to_allowed_chat(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(TelegramBotManager, "verify_bot", return_value=True):
                manager = TelegramBotManager("test-token", "123")
            manager.usage_stats = BotUsageStats(Path(directory) / "usage.json")

            response = manager.handle_command("/stats", chat_id="123")

        self.assertIn("إحصائيات استخدام البوت", response)
        self.assertEqual(manager.usage_stats.snapshot()["commands_succeeded"], 1)

    def test_unauthorized_chat_is_rejected_and_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(TelegramBotManager, "verify_bot", return_value=True):
                manager = TelegramBotManager("test-token", "123")
            manager.usage_stats = BotUsageStats(Path(directory) / "usage.json")

            response = manager.handle_command("/stats", chat_id="999")

        self.assertIn("غير مصرح", response)
        self.assertEqual(manager.usage_stats.snapshot()["commands_denied"], 1)


if __name__ == "__main__":
    unittest.main()
