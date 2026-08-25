"""نماذج البيانات المشتركة بين وحدات التطبيق."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class Platform(StrEnum):
    """المنصات التي يمكن فحص أسماء المستخدمين فيها."""

    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    TIKTOK = "tiktok"


class ScanStatus(StrEnum):
    """الحالات المحتملة لنتيجة فحص اسم مستخدم."""

    AVAILABLE = "available"
    TAKEN = "taken"
    INVALID = "invalid"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ScanResult:
    """نتيجة فحص اسم مستخدم واحد على منصة محددة."""

    username: str
    platform: Platform | str
    status: ScanStatus
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None
    response_time_ms: float | None = None

    @property
    def available(self) -> bool:
        """أعد True عندما يكون الاسم متاحًا."""
        return self.status is ScanStatus.AVAILABLE

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValueError("username لا يمكن أن يكون فارغًا")
        if isinstance(self.platform, str):
            object.__setattr__(self, "platform", self.platform.strip().lower())
        if self.response_time_ms is not None and self.response_time_ms < 0:
            raise ValueError("response_time_ms لا يمكن أن تكون سالبة")


@dataclass(slots=True)
class ScanSummary:
    """ملخص مجموعة من نتائج الفحص."""

    total: int = 0
    available: int = 0
    taken: int = 0
    invalid: int = 0
    errors: int = 0

    def add(self, result: ScanResult) -> None:
        """أضف نتيجة إلى الملخص."""
        self.total += 1
        if result.status is ScanStatus.AVAILABLE:
            self.available += 1
        elif result.status is ScanStatus.TAKEN:
            self.taken += 1
        elif result.status is ScanStatus.INVALID:
            self.invalid += 1
        elif result.status is ScanStatus.ERROR:
            self.errors += 1


@dataclass(frozen=True, slots=True)
class ProxySettings:
    """إعدادات بروكسي اختيارية لطلبات الشبكة."""

    url: str
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.url.strip():
            raise ValueError("عنوان البروكسي لا يمكن أن يكون فارغًا")


@dataclass(frozen=True, slots=True)
class PlatformCredential:
    """بيانات اعتماد منصة، مع إبقاء القيمة خارج السجلات النصية."""

    platform: Platform | str
    token: str
    chat_id: str | None = None

    def __post_init__(self) -> None:
        if not self.token.strip():
            raise ValueError("token لا يمكن أن يكون فارغًا")
