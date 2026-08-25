import json
import tempfile
import unittest
from pathlib import Path

from src.config import AppConfig, TelegramConfig
from src.models import (
    Platform,
    PlatformCredential,
    ProxySettings,
    ScanResult,
    ScanStatus,
    ScanSummary,
)


class TelegramConfigTests(unittest.TestCase):
    def test_default_values_are_safe(self):
        config = TelegramConfig()

        self.assertEqual(config.token, "")
        self.assertEqual(config.chat_id, "")
        self.assertEqual(config.polling_timeout, 30)

    def test_invalid_polling_timeout_is_rejected(self):
        config = TelegramConfig(polling_timeout=0)

        with self.assertRaises(ValueError):
            config.validate()


class AppConfigTests(unittest.TestCase):
    def test_from_dict_converts_supported_values(self):
        config = AppConfig.from_dict(
            {
                "request_timeout": "4.5",
                "max_workers": "4",
                "request_delay": "0.25",
                "use_proxy": True,
                "proxies": ["http://127.0.0.1:8080"],
                "blacklist": ["admin"],
                "output_directory": "var/results",
                "telegram": {
                    "token": "token-value",
                    "chat_id": 123,
                    "polling_timeout": "20",
                },
            }
        )

        self.assertEqual(config.request_timeout, 4.5)
        self.assertEqual(config.max_workers, 4)
        self.assertEqual(config.request_delay, 0.25)
        self.assertTrue(config.use_proxy)
        self.assertEqual(config.output_directory, Path("var/results"))
        self.assertEqual(config.telegram.chat_id, "123")

    def test_load_applies_environment_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "telegram": {
                            "token": "file-token",
                            "chat_id": "file-chat",
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = AppConfig.load(
                config_path,
                environ={
                    "TG_BOT_TOKEN": "environment-token",
                    "TG_CHAT_ID": "environment-chat",
                },
            )

        self.assertEqual(config.telegram.token, "environment-token")
        self.assertEqual(config.telegram.chat_id, "environment-chat")

    def test_save_and_load_preserve_configuration(self):
        original = AppConfig.from_dict(
            {
                "max_workers": 3,
                "output_directory": "saved-results",
                "telegram": {"chat_id": "42"},
            }
        )

        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "nested" / "config.json"
            original.save(config_path)
            restored = AppConfig.load(config_path, environ={})

        self.assertEqual(restored.max_workers, 3)
        self.assertEqual(restored.output_directory, Path("saved-results"))
        self.assertEqual(restored.telegram.chat_id, "42")

    def test_invalid_worker_count_is_rejected(self):
        with self.assertRaises(ValueError):
            AppConfig.from_dict({"max_workers": 0})

    def test_non_object_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text("[]", encoding="utf-8")

            with self.assertRaises(ValueError):
                AppConfig.load(config_path, environ={})


class ModelTests(unittest.TestCase):
    def test_available_result_reports_availability(self):
        result = ScanResult(
            username="example",
            platform=Platform.TELEGRAM,
            status=ScanStatus.AVAILABLE,
        )

        self.assertTrue(result.available)
        self.assertEqual(result.platform, Platform.TELEGRAM)

    def test_empty_username_is_rejected(self):
        with self.assertRaises(ValueError):
            ScanResult(
                username="   ",
                platform=Platform.TELEGRAM,
                status=ScanStatus.INVALID,
            )

    def test_negative_response_time_is_rejected(self):
        with self.assertRaises(ValueError):
            ScanResult(
                username="example",
                platform="telegram",
                status=ScanStatus.ERROR,
                response_time_ms=-1,
            )

    def test_summary_counts_each_status(self):
        summary = ScanSummary()
        results = [
            ScanResult("one", Platform.TELEGRAM, ScanStatus.AVAILABLE),
            ScanResult("two", Platform.TELEGRAM, ScanStatus.TAKEN),
            ScanResult("three", Platform.TELEGRAM, ScanStatus.INVALID),
            ScanResult("four", Platform.TELEGRAM, ScanStatus.ERROR),
        ]

        for result in results:
            summary.add(result)

        self.assertEqual(summary.total, 4)
        self.assertEqual(summary.available, 1)
        self.assertEqual(summary.taken, 1)
        self.assertEqual(summary.invalid, 1)
        self.assertEqual(summary.errors, 1)

    def test_proxy_and_credentials_require_values(self):
        with self.assertRaises(ValueError):
            ProxySettings("")
        with self.assertRaises(ValueError):
            PlatformCredential(Platform.TELEGRAM, "")


if __name__ == "__main__":
    unittest.main()
