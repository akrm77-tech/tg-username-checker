# دليل الإعدادات

## متغيرات البيئة

| المتغير | الاستخدام | القيمة الافتراضية |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | توكن بوت Telegram المستخدم في `checker.py` | فارغ؛ يتعطل الإرسال بدونه |
| `TELEGRAM_CHAT_ID` | معرف المحادثة الافتراضية للإرسال | فارغ |
| `TELEGRAM_ALLOWED_CHAT_IDS` | قائمة محادثات مسموح لها باستخدام أوامر البوت، مفصولة بفواصل | لا توجد قائمة محددة |
| `TG_CHECKER_LOG_DIR` | مجلد ملف السجل | `logs` |
| `TG_CHECKER_STATS_FILE` | ملف إحصائيات استخدام البوت | `bot_usage_stats.json` |
| `TG_BOT_TOKEN` | توكن بديل تستخدمه طبقة الإعدادات الجديدة في `src/config.py` | فارغ |
| `TG_CHAT_ID` | معرف محادثة بديل تستخدمه طبقة الإعدادات الجديدة | فارغ |

تستخدم النسخة الحالية من `src/checker.py` متغيري `TELEGRAM_BOT_TOKEN` و`TELEGRAM_CHAT_ID`، بينما يدعم `src/config.py` أيضًا الاسمين `TG_BOT_TOKEN` و`TG_CHAT_ID` تمهيدًا لتوحيد الإعدادات أثناء إعادة الهيكلة.

## مثال Linux وmacOS

```bash
export TELEGRAM_BOT_TOKEN="توكن_البوت"
export TELEGRAM_CHAT_ID="123456789"
export TELEGRAM_ALLOWED_CHAT_IDS="123456789"
export TG_CHECKER_LOG_DIR="logs"
export TG_CHECKER_STATS_FILE="bot_usage_stats.json"
```

## مثال Windows PowerShell

```powershell
$env:TELEGRAM_BOT_TOKEN = "توكن_البوت"
$env:TELEGRAM_CHAT_ID = "123456789"
$env:TELEGRAM_ALLOWED_CHAT_IDS = "123456789"
$env:TG_CHECKER_LOG_DIR = "logs"
$env:TG_CHECKER_STATS_FILE = "bot_usage_stats.json"
```

## ملف الإعدادات الجديد

يوفر `src/config.py` نموذج `AppConfig` قابلًا للحفظ في JSON. يمكن استخدامه في الوحدات الجديدة بهذه الصورة:

```python
from pathlib import Path
from src.config import AppConfig

config = AppConfig.load(Path(".tg-username-checker.json"))
print(config.request_timeout)
```

لا يحفظ التطبيق التوكنات داخل المستودع. أضف ملفات الإعدادات المحلية إلى `.gitignore`، واستخدم متغيرات البيئة في البيئات المشتركة أو المؤتمتة. إذا تسرّب توكن، أوقفه وأنشئ توكنًا بديلًا من BotFather فورًا.
