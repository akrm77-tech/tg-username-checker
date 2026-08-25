"""إدارة إعدادات أداة فحص أسماء المستخدمين."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path(".tg-username-checker.json")


@dataclass
class TelegramConfig:
    """إعدادات بوت Telegram."""

    token: str = ""
    chat_id: str = ""
    polling_timeout: int = 30

    def validate(self) -> None:
        if self.polling_timeout < 1 or self.polling_timeout > 60:
            raise ValueError("polling_timeout يجب أن يكون بين 1 و60 ثانية")


@dataclass
class AppConfig:
    """إعدادات التطبيق القابلة للحفظ والتحميل."""

    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    request_timeout: float = 10.0
    max_workers: int = 10
    request_delay: float = 0.0
    use_proxy: bool = False
    proxies: list[str] = field(default_factory=list)
    blacklist: list[str] = field(default_factory=list)
    output_directory: Path = Path("results")
    platform_tokens: dict[str, dict[str, str]] = field(default_factory=dict)

    def validate(self) -> None:
        """تحقق من أن القيم الأساسية منطقية قبل بدء التشغيل."""
        if self.request_timeout <= 0:
            raise ValueError("request_timeout يجب أن يكون أكبر من صفر")
        if self.max_workers < 1 or self.max_workers > 100:
            raise ValueError("max_workers يجب أن يكون بين 1 و100")
        if self.request_delay < 0:
            raise ValueError("request_delay لا يمكن أن يكون سالبًا")
        if not isinstance(self.proxies, list):
            raise TypeError("proxies يجب أن تكون قائمة")
        if not isinstance(self.blacklist, list):
            raise TypeError("blacklist يجب أن تكون قائمة")
        self.telegram.validate()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        """إنشاء الإعدادات من قاموس مع تجاهل المفاتيح غير المعروفة."""
        telegram_data = data.get("telegram", {})
        telegram = TelegramConfig(
            token=str(telegram_data.get("token", "")),
            chat_id=str(telegram_data.get("chat_id", "")),
            polling_timeout=int(telegram_data.get("polling_timeout", 30)),
        )

        output_directory = Path(data.get("output_directory", "results"))
        config = cls(
            telegram=telegram,
            request_timeout=float(data.get("request_timeout", 10.0)),
            max_workers=int(data.get("max_workers", 10)),
            request_delay=float(data.get("request_delay", 0.0)),
            use_proxy=bool(data.get("use_proxy", False)),
            proxies=[str(proxy) for proxy in data.get("proxies", [])],
            blacklist=[str(word) for word in data.get("blacklist", [])],
            output_directory=output_directory,
            platform_tokens={
                str(platform): {
                    str(key): str(value)
                    for key, value in values.items()
                }
                for platform, values in data.get("platform_tokens", {}).items()
            },
        )
        config.validate()
        return config

    @classmethod
    def load(
        cls,
        path: Path = DEFAULT_CONFIG_PATH,
        *,
        environ: dict[str, str] | None = None,
    ) -> "AppConfig":
        """حمّل الإعدادات من JSON ثم طبّق متغيرات البيئة إن وُجدت."""
        environment = os.environ if environ is None else environ
        data: dict[str, Any] = {}

        if path.exists():
            with path.open("r", encoding="utf-8") as config_file:
                loaded = json.load(config_file)
            if not isinstance(loaded, dict):
                raise ValueError("ملف الإعدادات يجب أن يحتوي على كائن JSON")
            data = loaded

        config = cls.from_dict(data)
        config.telegram.token = environment.get("TG_BOT_TOKEN", config.telegram.token)
        config.telegram.chat_id = environment.get("TG_CHAT_ID", config.telegram.chat_id)
        config.validate()
        return config

    def save(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        """احفظ الإعدادات بصيغة JSON، وأنشئ مجلد الوجهة عند الحاجة."""
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        payload["output_directory"] = str(self.output_directory)
        with path.open("w", encoding="utf-8") as config_file:
            json.dump(payload, config_file, ensure_ascii=False, indent=2)
            config_file.write("\n")
