import time
import requests
import random
import threading
import logging
import json
import os
import re
from logging.handlers import RotatingFileHandler
from datetime import datetime
from colorama import init, Fore, Style, Back
from collections import defaultdict
import csv
import sys

# تهيئة colorama
init(autoreset=True)

LOG_DIR = os.getenv("TG_CHECKER_LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("tg_username_checker")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "checker.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(file_handler)

logger.propagate = False

# ============ إعدادات البانر ============

def print_banner():
    """طباعة البانر الترحيبي"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════╗
{Fore.GREEN}  █████╗ ██╗  ██╗██████╗   ███╗   ███╗
{Fore.GREEN} ██╔══██╗██║ ██╔╝██╔══██╗  ████╗ ████║
{Fore.GREEN} ███████║█████╔╝ ██████╔╝  ██╔████╔██║
{Fore.GREEN} ██╔══██║██╔═██╗ ██╔══╗██║ ██║╚██╔╝██║
{Fore.GREEN} ██║  ██║██║  ██╗██║  ║██║ ██║ ╚═╝ ██║
{Fore.GREEN} ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚══╝ ╚═╝     ╚═╝
{Fore.CYAN}╠══════════════════════════════════════════════════════╣
{Fore.YELLOW}  🎯 {Fore.WHITE}صياد الأسماء المحترف {Fore.YELLOW}🎯
{Fore.CYAN}╚══════════════════════════════════════════════════════╝
    """
    print(banner)

# ============ إعدادات البوت ============


class BotUsageStats:
    """إحصائيات استخدام البوت مع حفظ دوري في ملف محلي."""

    def __init__(self, stats_file=None):
        self.stats_file = stats_file or os.getenv(
            "TG_CHECKER_STATS_FILE", "bot_usage_stats.json"
        )
        self.lock = threading.Lock()
        self.data = self._default_data()
        self._load()

    @staticmethod
    def _default_data():
        return {
            "started_at": datetime.now().isoformat(),
            "last_activity": None,
            "commands_received": 0,
            "commands_allowed": 0,
            "commands_denied": 0,
            "commands_unknown": 0,
            "commands_succeeded": 0,
            "commands_failed": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "commands": {},
        }

    def _load(self):
        try:
            with open(self.stats_file, "r", encoding="utf-8") as file:
                loaded = json.load(file)
            if isinstance(loaded, dict):
                self.data.update(loaded)
                if not isinstance(self.data.get("commands"), dict):
                    self.data["commands"] = {}
        except FileNotFoundError:
            return
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("تعذر تحميل إحصائيات البوت: %s", exc)

    def _save_locked(self):
        temporary_file = f"{self.stats_file}.tmp"
        try:
            with open(temporary_file, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=2, ensure_ascii=False)
            os.replace(temporary_file, self.stats_file)
        except OSError as exc:
            logger.error("تعذر حفظ إحصائيات البوت: %s", exc)
            try:
                os.remove(temporary_file)
            except OSError:
                pass

    def record_command(self, command, outcome):
        with self.lock:
            self.data["commands_received"] += 1
            self.data["last_activity"] = datetime.now().isoformat()
            self.data["commands"][command] = (
                self.data["commands"].get(command, 0) + 1
            )
            if outcome == "denied":
                self.data["commands_denied"] += 1
            elif outcome == "unknown":
                self.data["commands_allowed"] += 1
                self.data["commands_unknown"] += 1
            elif outcome == "success":
                self.data["commands_allowed"] += 1
                self.data["commands_succeeded"] += 1
            elif outcome == "failed":
                self.data["commands_allowed"] += 1
                self.data["commands_failed"] += 1
            self._save_locked()

    def record_message(self, success):
        with self.lock:
            key = "messages_sent" if success else "messages_failed"
            self.data[key] += 1
            self.data["last_activity"] = datetime.now().isoformat()
            self._save_locked()

    def snapshot(self):
        with self.lock:
            return json.loads(json.dumps(self.data, ensure_ascii=False))


class TelegramBotManager:
    """مدير البوت المتقدم"""
    
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = str(chat_id or os.getenv("TELEGRAM_CHAT_ID", ""))
        self.enabled = bool(self.bot_token and self.chat_id)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.last_sent = 0
        self.min_interval = 2
        self.failed_attempts = 0
        self.max_failures = 5
        self.usage_stats = BotUsageStats()
        self.command_handlers = {
            "/help": self._command_help,
            "/stats": self._command_stats,
        }
        
        if self.enabled:
            self.verify_bot()
    
    def verify_bot(self):
        """التحقق من صحة البوت"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_name = data['result'].get('username', 'Unknown')
                    logger.info("تم التحقق من البوت: %s", bot_name)
                    print(f"{Fore.GREEN}✅ البوت يعمل: @{bot_name}")
                    return True
            logger.warning("فشل التحقق من البوت، رمز HTTP: %s", response.status_code)
            return False
        except Exception as exc:
            logger.exception("فشل التحقق من البوت: %s", exc)
            print(f"{Fore.RED}❌ فشل التحقق من البوت: {exc}")
            return False

    def _allowed_chat_ids(self):
        configured = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
        if configured.strip():
            return {
                value.strip()
                for value in configured.split(",")
                if value.strip()
            }
        return {str(self.chat_id).strip()} if self.chat_id else set()

    def _command_help(self, args):
        return "الأوامر المتاحة:\n/stats - عرض إحصائيات استخدام البوت\n/help - عرض هذه المساعدة"

    def format_usage_stats(self):
        stats = self.usage_stats.snapshot()
        commands = stats.get("commands", {})
        popular = sorted(commands.items(), key=lambda item: item[1], reverse=True)
        popular_lines = "\n".join(
            f"• {name}: {count}" for name, count in popular[:10]
        ) or "لا توجد أوامر مسجلة"
        return (
            "📊 <b>إحصائيات استخدام البوت</b>\n\n"
            f"• الأوامر المستلمة: {stats['commands_received']}\n"
            f"• الأوامر المسموحة: {stats['commands_allowed']}\n"
            f"• المحاولات المرفوضة: {stats['commands_denied']}\n"
            f"• الأوامر غير المعروفة: {stats['commands_unknown']}\n"
            f"• الأوامر الناجحة: {stats['commands_succeeded']}\n"
            f"• الأوامر الفاشلة: {stats['commands_failed']}\n"
            f"• الرسائل المرسلة: {stats['messages_sent']}\n"
            f"• الرسائل الفاشلة: {stats['messages_failed']}\n"
            f"• آخر نشاط: {stats.get('last_activity') or 'لا يوجد'}\n\n"
            "<b>الأوامر الأكثر استخدامًا:</b>\n"
            f"{popular_lines}"
        )

    def _command_stats(self, args):
        return self.format_usage_stats()

    def handle_command(self, command, args=None, chat_id=None):
        """التحقق من الصلاحية وتنفيذ أمر واحد دون تسجيل محتوى الأسرار."""
        args = args or []
        command_name = (command or "").strip().split()[0] if command else ""
        command_name = command_name.split("@", 1)[0].lower()
        if command_name and not command_name.startswith("/"):
            command_name = f"/{command_name}"

        if not self.usage_stats:
            self.usage_stats = BotUsageStats()

        if not chat_id or str(chat_id).strip() not in self._allowed_chat_ids():
            self.usage_stats.record_command(command_name or "<empty>", "denied")
            logger.warning("تم رفض أمر من محادثة غير مصرح بها: %s", chat_id)
            return "❌ غير مصرح لك باستخدام أوامر هذا البوت."

        handler = self.command_handlers.get(command_name)
        if handler is None:
            self.usage_stats.record_command(command_name or "<empty>", "unknown")
            logger.info("أمر غير معروف: %s", command_name or "<empty>")
            return "❌ أمر غير معروف. أرسل /help لعرض الأوامر المتاحة."

        try:
            response = handler(args)
            self.usage_stats.record_command(command_name, "success")
            logger.info("تم تنفيذ الأمر: %s", command_name)
            return str(response)
        except Exception as exc:
            self.usage_stats.record_command(command_name, "failed")
            logger.exception("فشل تنفيذ الأمر %s: %s", command_name, exc)
            return "❌ حدث خطأ أثناء تنفيذ الأمر. راجع السجل للمزيد من التفاصيل."

    def send_text(self, text, chat_id=None):
        """إرسال نص عام مع تسجيل نتيجة العملية."""
        if not self.enabled:
            return False
        target_chat_id = str(chat_id or self.chat_id)
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            response = self.session.post(
                url,
                params={"chat_id": target_chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            success = response.status_code == 200
            self.usage_stats.record_message(success)
            if success:
                logger.info("تم إرسال رسالة إلى المحادثة %s", target_chat_id)
            else:
                logger.warning(
                    "فشل إرسال رسالة، رمز HTTP: %s", response.status_code
                )
            return success
        except requests.RequestException as exc:
            self.usage_stats.record_message(False)
            logger.exception("خطأ شبكة أثناء إرسال رسالة: %s", exc)
            return False

    def poll_updates(self, stop_event=None):
        """استقبال أوامر البوت في الخلفية حتى يتم إيقاف الحدث."""
        stop_event = stop_event or threading.Event()
        offset = None
        logger.info("بدأ استقبال أوامر البوت")
        while not stop_event.is_set() and self.enabled:
            try:
                params = {"timeout": 20}
                if offset is not None:
                    params["offset"] = offset
                response = self.session.get(
                    f"https://api.telegram.org/bot{self.bot_token}/getUpdates",
                    params=params,
                    timeout=25,
                )
                if response.status_code != 200:
                    logger.warning(
                        "فشل استقبال تحديثات البوت، رمز HTTP: %s",
                        response.status_code,
                    )
                    stop_event.wait(5)
                    continue
                payload = response.json()
                if not payload.get("ok"):
                    logger.warning("أعاد Telegram استجابة غير ناجحة للتحديثات")
                    stop_event.wait(5)
                    continue
                for update in payload.get("result", []):
                    offset = update.get("update_id", 0) + 1
                    message = update.get("message", {})
                    text = message.get("text", "")
                    if not text.startswith("/"):
                        continue
                    parts = text.split()
                    response_text = self.handle_command(
                        parts[0],
                        parts[1:],
                        message.get("chat", {}).get("id"),
                    )
                    self.send_text(
                        response_text,
                        message.get("chat", {}).get("id"),
                    )
            except requests.RequestException as exc:
                logger.warning("خطأ اتصال أثناء استقبال الأوامر: %s", exc)
                stop_event.wait(5)
            except (ValueError, KeyError) as exc:
                logger.exception("استجابة غير صالحة من Telegram: %s", exc)
                stop_event.wait(5)
            except Exception as exc:
                logger.exception("خطأ غير متوقع في استقبال الأوامر: %s", exc)
                stop_event.wait(5)
        logger.info("توقف استقبال أوامر البوت")
    
    def send_message(self, username, quality=None, found_count=None):
        """إرسال رسالة محسنة مع معلومات إضافية"""
        if not self.enabled:
            return False
        
        current_time = time.time()
        if current_time - self.last_sent < self.min_interval:
            time.sleep(self.min_interval - (current_time - self.last_sent))
        
        try:
            message = self.format_message(username, quality, found_count)
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            params = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = self.session.post(url, params=params, timeout=10)
            
            if response.status_code == 200:
                self.last_sent = time.time()
                self.failed_attempts = 0
                self.usage_stats.record_message(True)
                logger.info("تم إرسال نتيجة الاسم: %s", username)
                print(f"{Fore.GREEN}📤 تم الإرسال للبوت: @{username}")
                return True
            else:
                self.failed_attempts += 1
                self.usage_stats.record_message(False)
                logger.warning(
                    "فشل إرسال نتيجة الاسم %s، رمز HTTP: %s",
                    username,
                    response.status_code,
                )
                return False
                
        except Exception as exc:
            self.failed_attempts += 1
            self.usage_stats.record_message(False)
            logger.exception("فشل إرسال الرسالة: %s", exc)
            
            if self.failed_attempts >= self.max_failures:
                print(f"{Fore.RED}⚠️ تم تعطيل البوت بسبب فشل متكرر")
                self.enabled = False
            
            return False
    
    def format_message(self, username, quality=None, found_count=None):
        """تنسيق الرسالة المرسلة"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        quality_stars = ''
        if quality is not None:
            if quality >= 12:
                quality_stars = '⭐' * 3 + ' ممتاز!'
            elif quality >= 8:
                quality_stars = '⭐' * 2 + ' جيد'
            elif quality >= 5:
                quality_stars = '⭐' * 1 + ' متوسط'
            else:
                quality_stars = '💫 عادي'
        
        message = f"""
<b>🎣 تم العثور على اسم مستخدم جديد!</b>

<b>👤 الاسم:</b> @{username}
<b>📏 الطول:</b> {len(username)} أحرف
<b>⭐ الجودة:</b> {quality_stars}
<b>📅 التاريخ:</b> {timestamp}
<b>🔗 الرابط:</b> https://t.me/{username}

━━━━━━━━━━━━━━━━━━━━
<b>📊 إحصائيات:</b>
• تم العثور على: {found_count or '?'} اسم
• وقت الاكتشاف: {timestamp}
        """
        return message
    
    def send_startup_message(self):
        """إرسال رسالة بدء التشغيل"""
        if not self.enabled:
            return False
        
        message = f"""
<b>🚀 بدء البحث عن الأسماء!</b>

<b>📏 طول الأسماء:</b> 5-7 أحرف
<b>⚡ عدد الخيوط:</b> 5
<b>🎯 الهدف:</b> العثور على أسماء متاحة

━━━━━━━━━━━━━━━━━━━━
<b>✅ البوت جاهز للعمل</b>
        """
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            params = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = self.session.post(url, params=params, timeout=10)
            success = response.status_code == 200
            self.usage_stats.record_message(success)
            if success:
                logger.info("تم إرسال رسالة بدء التشغيل")
            else:
                logger.warning(
                    "فشل إرسال رسالة بدء التشغيل، رمز HTTP: %s",
                    response.status_code,
                )
            return success
        except requests.RequestException as exc:
            self.usage_stats.record_message(False)
            logger.exception("فشل إرسال رسالة بدء التشغيل: %s", exc)
            return False

# ============ دوال البحث ============

def get_username_length():
    """الحصول على طول اسم المستخدم من المستخدم"""
    while True:
        try:
            print(f"\n{Fore.YELLOW}📏 اختر طول اسم المستخدم:")
            print(f"{Fore.CYAN}   [1] قصير (3-5 أحرف)")
            print(f"{Fore.CYAN}   [2] متوسط (6-8 أحرف)")
            print(f"{Fore.CYAN}   [3] طويل (9-12 أحرف)")
            print(f"{Fore.CYAN}   [4] مخصص (أدخل الطول بنفسك)")
            
            choice = input(f"{Fore.YELLOW}اختر رقم (1-4): {Fore.RESET}").strip()
            
            if choice == '1':
                return random.randint(3, 5)
            elif choice == '2':
                return random.randint(6, 8)
            elif choice == '3':
                return random.randint(9, 12)
            elif choice == '4':
                min_len = int(input(f"{Fore.YELLOW}أدخل أقل طول: {Fore.RESET}"))
                max_len = int(input(f"{Fore.YELLOW}أدخل أقصى طول: {Fore.RESET}"))
                if min_len < 3 or max_len > 20:
                    print(f"{Fore.RED}❌ الطول يجب أن يكون بين 3 و 20")
                    continue
                return random.randint(min_len, max_len)
            else:
                print(f"{Fore.RED}❌ اختيار غير صحيح، حاول مرة أخرى")
        except ValueError:
            print(f"{Fore.RED}❌ يرجى إدخال رقم صحيح")

def generate_username(length):
    """توليد اسم مستخدم عشوائي"""
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    prefixes = ['mr', 'dr', 'pro', 'x', 'z', 'alpha', 'beta', 'tech', 'dev', 'web']
    
    if random.random() > 0.5 and length > 3:
        prefix = random.choice(prefixes)
        if len(prefix) < length:
            return prefix + ''.join(random.choices(chars, k=length-len(prefix)))
    
    return ''.join(random.choices(chars, k=length))

def check_username(username, session):
    """التحقق من توفر اسم المستخدم"""
    try:
        url = f"https://t.me/{username}"
        response = session.get(url, timeout=10)
        
        if 'tgme_page_extra' in response.text:
            return False, "غير متوفر ❌"
        elif 'If you have <strong>Telegram</strong>' in response.text:
            return True, "متوفر ✅"
        else:
            return False, "غير معروف ⚠️"
            
    except requests.exceptions.Timeout:
        return False, "انتهى الوقت ⏰"
    except requests.exceptions.ConnectionError:
        return False, "مشكلة في الاتصال 📡"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def check_quality(username):
    """تقييم جودة الاسم"""
    score = 0
    length = len(username)
    
    if length <= 4:
        score += 10
    elif length <= 6:
        score += 5
    
    if not any(c.isdigit() for c in username):
        score += 5
    
    if username[0].isupper():
        score += 3
    
    common_patterns = ['tech', 'pro', 'dev', 'web', 'ai', 'bot', 'cloud', 'data']
    for pattern in common_patterns:
        if pattern in username.lower():
            score += 7
            break
    
    return score

def display_stats(username_length, total_checked, found, last_username, status_counts):
    """عرض الإحصائيات"""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.YELLOW}📊 إحصائيات آخر 30 يوزر:")
    print(f"{Fore.CYAN}{'━'*60}")
    print(f"{Fore.GREEN}   ✓ تم التحقق: {total_checked}")
    print(f"{Fore.GREEN}   ✓ تم العثور: {found}")
    print(f"{Fore.YELLOW}   📏 طول اليوزر: {username_length} أحرف")
    
    if status_counts:
        print(f"{Fore.CYAN}   📊 الحالة:")
        for status, count in status_counts.items():
            color = Fore.GREEN if 'متوفر' in status else Fore.RED
            print(f"      {color}{status}: {count}")
    
    if last_username:
        print(f"{Fore.GREEN}   ✓ آخر اسم: @{last_username}")
    
    print(f"{Fore.MAGENTA}{'='*60}\n")

# ============ الكلاس الرئيسي ============

class TelegramChecker:
    """الكلاس الرئيسي للتحقق من الأسماء"""
    
    def __init__(self, bot_token=None, chat_id=None, username_length=6):
        self.bot_manager = TelegramBotManager(bot_token, chat_id) if bot_token else None
        self.username_length = username_length
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.found_usernames = []
        self.total_checked = 0
        self.last_username = None
        self.lock = threading.Lock()
        self.running = True
        self.status_counts = {}
        self.check_counter = 0
        self.start_time = datetime.now()
        
        # إرسال رسالة بدء التشغيل
        if self.bot_manager and self.bot_manager.enabled:
            self.bot_manager.send_startup_message()
    
    def worker(self):
        """دالة العمل لكل خيط"""
        while self.running:
            username = generate_username(self.username_length)
            is_available, status = check_username(username, self.session)
            
            with self.lock:
                self.total_checked += 1
                self.check_counter += 1
                self.last_username = username
                
                if status not in self.status_counts:
                    self.status_counts[status] = 0
                self.status_counts[status] += 1
            
            if is_available:
                quality = check_quality(username)
                with self.lock:
                    self.found_usernames.append(username)
                    print(f"{Fore.GREEN}✅ [{self.total_checked}] متوفر: @{username} (جودة: {quality}/15)")
                
                # إرسال إلى البوت
                if self.bot_manager and self.bot_manager.enabled:
                    self.bot_manager.send_message(username, quality, len(self.found_usernames))
            else:
                print(f"{Fore.RED}❌ [{self.total_checked}] غير متوفر: @{username} - {status}")
            
            # عرض الإحصائيات كل 30 يوزر
            with self.lock:
                if self.check_counter >= 30:
                    display_stats(
                        self.username_length,
                        self.total_checked,
                        len(self.found_usernames),
                        self.last_username,
                        self.status_counts
                    )
                    self.check_counter = 0
            
            # انتظار لتجنب الحظر
            time.sleep(1.5 + random.uniform(0, 0.5))
    
    def start(self, threads_count=5):
        """بدء عملية التحقق"""
        print(f"\n{Fore.YELLOW}🚀 بدء التحقق بـ {threads_count} خيط...")
        print(f"{Fore.CYAN}📏 طول اليوزر: {self.username_length} أحرف")
        print(f"{Fore.YELLOW}📊 سيتم عرض الإحصائيات كل 30 يوزر")
        print(f"{Fore.CYAN}{'━'*60}\n")
        
        threads = []
        for _ in range(threads_count):
            thread = threading.Thread(target=self.worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """إيقاف العملية"""
        self.running = False
        elapsed = datetime.now() - self.start_time
        
        print(f"\n{Fore.YELLOW}🛑 تم إيقاف العملية")
        print(f"{Fore.GREEN}📊 الإحصائيات النهائية:")
        print(f"{Fore.CYAN}{'━'*60}")
        print(f"{Fore.GREEN}   ✓ تم التحقق: {self.total_checked}")
        print(f"{Fore.GREEN}   ✓ تم العثور: {len(self.found_usernames)}")
        print(f"{Fore.YELLOW}   📏 طول اليوزر: {self.username_length} أحرف")
        print(f"{Fore.YELLOW}   ⏰ المدة: {str(elapsed).split('.')[0]}")
        
        if self.found_usernames:
            print(f"{Fore.CYAN}📝 الأسماء التي تم العثور عليها:")
            for username in self.found_usernames:
                quality = check_quality(username)
                print(f"   {Fore.GREEN}- @{username} (جودة: {quality}/15)")
        
        print(f"{Fore.CYAN}{'━'*60}")

# ============ إعداد البوت ============

def setup_bot():
    """إعداد البوت مع خيارات متعددة"""
    print(f"\n{Fore.CYAN}╔{'═'*56}╗")
    print(f"{Fore.YELLOW}  🤖 إعداد البوت:")
    print(f"{Fore.CYAN}╠{'═'*56}╣")
    print(f"{Fore.WHITE}  [1] {Fore.GREEN}تفعيل البوت")
    print(f"{Fore.WHITE}  [2] {Fore.RED}تعطيل البوت (بدون إرسال)")
    print(f"{Fore.CYAN}╚{'═'*56}╝")
    
    choice = input(f"{Fore.YELLOW}اختر (1-2): {Fore.RESET}").strip()
    
    if choice == '2':
        print(f"{Fore.YELLOW}⚠️ سيتم التشغيل بدون بوت")
        return None, None
    
    if choice == '1':
        token = input(f"{Fore.YELLOW}🔑 أدخل توكن البوت: {Fore.RESET}").strip()
        chat_id = input(f"{Fore.YELLOW}🆔 أدخل معرف الشات: {Fore.RESET}").strip()
        
        if not token or not chat_id:
            print(f"{Fore.RED}❌ التوكن والمعرف مطلوبين!")
            return setup_bot()
        
        # اختبار البوت
        temp_bot = TelegramBotManager(token, chat_id)
        if temp_bot.verify_bot():
            return token, chat_id
        else:
            print(f"{Fore.RED}❌ البوت غير صحيح! حاول مرة أخرى")
            return setup_bot()
    
    return None, None

# ============ البرنامج الرئيسي ============

def main():
    try:
        # مسح الشاشة
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # عرض البانر
        print_banner()
        
        print(f"{Fore.CYAN}{'━'*60}")
        print(f"{Fore.YELLOW}⚠️  تحذير: استخدام هذه الأداة قد يخالف شروط تيليجرام")
        print(f"{Fore.YELLOW}📌 اضغط Ctrl+C للخروج في أي وقت")
        print(f"{Fore.CYAN}{'━'*60}")
        
        # اختيار طول اليوزر
        username_length = get_username_length()
        print(f"{Fore.GREEN}✅ تم اختيار طول {username_length} أحرف")
        
        # إعداد البوت
        bot_token, chat_id = setup_bot()
        
        print(f"{Fore.CYAN}{'━'*60}")
        
        # عدد الخيوط
        try:
            threads = int(input(f"{Fore.YELLOW}⚡ عدد الخيوط (1-10, افتراضي 5): {Fore.RESET}") or 5)
            threads = min(max(threads, 1), 10)
        except ValueError:
            threads = 5
        
        print(f"{Fore.CYAN}{'━'*60}")
        print(f"{Fore.GREEN}✅ بدء التشغيل...")
        time.sleep(1)
        
        # بدء التشغيل
        checker = TelegramChecker(bot_token, chat_id, username_length)
        command_stop_event = threading.Event()
        command_thread = None
        if checker.bot_manager and checker.bot_manager.enabled:
            command_thread = threading.Thread(
                target=checker.bot_manager.poll_updates,
                args=(command_stop_event,),
                name="telegram-command-polling",
                daemon=True,
            )
            command_thread.start()
            logger.info("تم تشغيل استقبال أوامر البوت في الخلفية")

        try:
            checker.start(threads)
        finally:
            command_stop_event.set()
            if command_thread:
                command_thread.join(timeout=3)
            logger.info("انتهى تشغيل الماسح")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 تم الخروج من البرنامج")
    except Exception as exc:
        logger.exception("خطأ غير متوقع في البرنامج: %s", exc)
        print(f"{Fore.RED}❌ حدث خطأ: {exc}")

if __name__ == "__main__":
    main()
