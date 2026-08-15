# ================================================================
# WORMGPT - Ultimate Username Scanner v7.0 (Black Edition)
# ================================================================
# BY: WORM GPT | CHANNEL: @smopel
# VERSION: 7.0.0 (مع تصحيح الدالة المفقودة)
# ================================================================

import os
import sys
import re
import json
import random
import time
import requests
import string
import threading
import logging
import hashlib
import base64
import urllib.parse
import glob
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple, Any

# ================================================================
# محاولة استيراد phonenumbers
# ================================================================
try:
    import phonenumbers
    from phonenumbers import geocoder, carrier
except ImportError:
    phonenumbers = None

# ================================================================
# الألوان والواجهة
# ================================================================

class Colors:
    """نظام الألوان المتقدم للواجهة"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    PINK = '\033[38;5;205m'
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;129m'
    GOLD = '\033[38;5;220m'
    SILVER = '\033[38;5;247m'
    DARK = '\033[38;5;235m'
    WHITE = '\033[97m'
    BLACK = '\033[38;5;16m'
    
    SUCCESS = GREEN
    ERROR = RED
    WARNING = YELLOW
    INFO = CYAN
    DEBUG = SILVER

C = Colors()

# ================================================================
# نظام السجلات المتقدم
# ================================================================

class AdvancedLogger:
    """نظام تسجيل متقدم مع مستويات متعددة"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.log_file = os.path.join(log_dir, f"wormgpt_{datetime.now().strftime('%Y%m%d')}.log")
        self.error_file = os.path.join(log_dir, f"wormgpt_error_{datetime.now().strftime('%Y%m%d')}.log")
        self.attack_file = os.path.join(log_dir, f"wormgpt_attacks_{datetime.now().strftime('%Y%m%d')}.log")
        
        self.logger = logging.getLogger('WORMGPT')
        self.logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        eh = logging.FileHandler(self.error_file, encoding='utf-8')
        eh.setLevel(logging.ERROR)
        eh.setFormatter(formatter)
        self.logger.addHandler(eh)
        
        ah = logging.FileHandler(self.attack_file, encoding='utf-8')
        ah.setLevel(logging.WARNING)
        ah.setFormatter(formatter)
        self.logger.addHandler(ah)
    
    def info(self, message: str):
        self.logger.info(message)
        print(f"{C.INFO}[INFO] {message}{C.RESET}")
    
    def warning(self, message: str):
        self.logger.warning(message)
        print(f"{C.WARNING}[WARN] {message}{C.RESET}")
    
    def error(self, message: str):
        self.logger.error(message)
        print(f"{C.ERROR}[ERROR] {message}{C.RESET}")
    
    def success(self, message: str):
        self.logger.info(f"SUCCESS: {message}")
        print(f"{C.SUCCESS}[✓] {message}{C.RESET}")
    
    def attack(self, message: str):
        self.logger.warning(f"ATTACK: {message}")
        print(f"{C.RED}[⚡] {message}{C.RESET}")

logger = AdvancedLogger()

# ================================================================
# إعدادات البوت المتقدمة مع تعدد التوكنات
# ================================================================

class BotConfig:
    """إعدادات البوت المتقدمة مع دعم توكنات متعددة لكل منصة"""
    
    def __init__(self):
        self.config_file = 'wormgpt_config.json'
        self.lock = Lock()
        self.load()
    
    def load(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.token = data.get('token', '')
                self.chat_id = data.get('chat_id', '')
                self.enabled = bool(self.token and self.chat_id)
                self.platform_tokens = data.get('platform_tokens', {})
                self.message_format = data.get('message_format', 
                    "🎯 <b>تم العثور على اسم متاح!</b>\n\n"
                    "👤 <b>الاسم:</b> @{username}\n"
                    "🌐 <b>المنصة:</b> {platform}\n"
                    "📊 <b>رقم المتاح للمنصة:</b> #{platform_count}\n"
                    "⭐ <b>الجودة:</b> {quality}/20\n"
                    "📅 <b>الوقت:</b> {time}\n\n"
                    "🔗 <b>رابط:</b> https://www.{platform}.com/{username}\n\n"
                    "{signature}"
                )
                self.signature = data.get('signature', '🖤 بواسطة @W4_M4')
                self.hashtags = data.get('hashtags', '#WORMGPT #UsernameHunter')
                self.links = data.get('links', '')
                self.min_quality = data.get('min_quality', 0)
                self.min_length = data.get('min_length', 0)
                self.max_length = data.get('max_length', 20)
                self.filter_numbers = data.get('filter_numbers', False)
                self.filter_uppercase = data.get('filter_uppercase', False)
                self.filter_lowercase = data.get('filter_lowercase', False)
                self.blacklist = data.get('blacklist', [])
                self.send_mode = data.get('send_mode', 'instant')
                self.send_interval = data.get('send_interval', 5)
                self.batch_size = data.get('batch_size', 10)
                self.backup_bots = data.get('backup_bots', [])
                self.proxies = data.get('proxies', [])
                self.use_proxy = data.get('use_proxy', False)
                self.total_found = data.get('total_found', 0)
                self.total_checked = data.get('total_checked', 0)
                self.start_time = data.get('start_time', datetime.now().isoformat())
                self.threads = data.get('threads', 20)
                self.delay = data.get('delay', 0.3)
                self.timeout = data.get('timeout', 10)
                self.retry_count = data.get('retry_count', 3)
                self.scan_status = data.get('scan_status', 'stopped')
                self.active_platforms = data.get('active_platforms', 
                    ['Instagram', 'Twitter', 'TikTok', 'Telegram', 'YouTube', 'Snapchat', 'Tumblr', 'GitHub', 'Reddit', 'Pinterest', 'Spotify']
                )
                self.pattern_type = data.get('pattern_type', 7)
                self.username_length = data.get('username_length', 4)
                self.scan_timer = data.get('scan_timer', 0)
                self.paused = data.get('paused', False)
                self.last_report_file = data.get('last_report_file', '')
                self.scan_start_time = data.get('scan_start_time', None)
                self.platform_stats = data.get('platform_stats', {})
                self.sequential_mode = data.get('sequential_mode', False)
                self.sequential_limit = data.get('sequential_limit', 100)
        except:
            self._init_defaults()
    
    def _init_defaults(self):
        self.token = ''
        self.chat_id = ''
        self.enabled = False
        self.platform_tokens = {}
        self.message_format = "🎯 <b>تم العثور على اسم متاح!</b>\n\n👤 <b>الاسم:</b> @{username}\n🌐 <b>المنصة:</b> {platform}\n📊 <b>رقم المتاح للمنصة:</b> #{platform_count}\n⭐ <b>الجودة:</b> {quality}/20\n📅 <b>الوقت:</b> {time}\n\n🔗 <b>رابط:</b> https://www.{platform}.com/{username}\n\n{signature}"
        self.signature = '🖤 بواسطة @W4_M4'
        self.hashtags = '#WORMGPT #UsernameHunter'
        self.links = ''
        self.min_quality = 0
        self.min_length = 0
        self.max_length = 20
        self.filter_numbers = False
        self.filter_uppercase = False
        self.filter_lowercase = False
        self.blacklist = []
        self.send_mode = 'instant'
        self.send_interval = 5
        self.batch_size = 10
        self.backup_bots = []
        self.proxies = []
        self.use_proxy = False
        self.total_found = 0
        self.total_checked = 0
        self.start_time = datetime.now().isoformat()
        self.threads = 20
        self.delay = 0.3
        self.timeout = 10
        self.retry_count = 3
        self.scan_status = 'stopped'
        self.active_platforms = ['Instagram', 'Twitter', 'TikTok', 'Telegram', 'YouTube', 'Snapchat', 'Tumblr', 'GitHub', 'Reddit', 'Pinterest', 'Spotify']
        self.pattern_type = 7
        self.username_length = 4
        self.scan_timer = 0
        self.paused = False
        self.last_report_file = ''
        self.scan_start_time = None
        self.platform_stats = {}
        self.sequential_mode = False
        self.sequential_limit = 100
        self.save()
    
    def save(self):
        data = {
            'token': self.token,
            'chat_id': self.chat_id,
            'platform_tokens': self.platform_tokens,
            'message_format': self.message_format,
            'signature': self.signature,
            'hashtags': self.hashtags,
            'links': self.links,
            'min_quality': self.min_quality,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'filter_numbers': self.filter_numbers,
            'filter_uppercase': self.filter_uppercase,
            'filter_lowercase': self.filter_lowercase,
            'blacklist': self.blacklist,
            'send_mode': self.send_mode,
            'send_interval': self.send_interval,
            'batch_size': self.batch_size,
            'backup_bots': self.backup_bots,
            'proxies': self.proxies,
            'use_proxy': self.use_proxy,
            'total_found': self.total_found,
            'total_checked': self.total_checked,
            'start_time': self.start_time,
            'threads': self.threads,
            'delay': self.delay,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'scan_status': self.scan_status,
            'active_platforms': self.active_platforms,
            'pattern_type': self.pattern_type,
            'username_length': self.username_length,
            'scan_timer': self.scan_timer,
            'paused': self.paused,
            'last_report_file': self.last_report_file,
            'scan_start_time': self.scan_start_time,
            'platform_stats': self.platform_stats,
            'sequential_mode': self.sequential_mode,
            'sequential_limit': self.sequential_limit
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def format_message(self, username: str, platform: str, quality: int, platform_count: int) -> str:
        return self.message_format.format(
            username=username,
            platform=platform,
            quality=quality,
            time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            signature=self.signature,
            platform_count=platform_count
        )
    
    def should_send(self, username: str, quality: int) -> bool:
        if quality < self.min_quality:
            return False
        if len(username) < self.min_length or len(username) > self.max_length:
            return False
        if self.filter_numbers and any(c.isdigit() for c in username):
            return False
        if self.filter_uppercase and any(c.isupper() for c in username):
            return False
        if self.filter_lowercase and any(c.islower() for c in username):
            return False
        for word in self.blacklist:
            if word.lower() in username.lower():
                return False
        return True
    
    def update_platform_stats(self, platform: str):
        if platform not in self.platform_stats:
            self.platform_stats[platform] = 0
        self.platform_stats[platform] += 1
        self.save()

bot_config = BotConfig()

# ================================================================
# البوت المتقدم مع تعدد التوكنات
# ================================================================

class WormBot:
    """بوت التليجرام المتقدم مع دعم توكنات متعددة لكل منصة"""
    
    def __init__(self):
        self.config = bot_config
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'WORMGPT-Bot/7.0'})
        self.last_sent = 0
        self.min_interval = 0.5
        self.batch_messages = []
        self.batch_lock = Lock()
        self.summary_counter = 0
        self.found_counter = 0
        self.start_time = datetime.now()
        self.command_handlers = {
            '/start': self.cmd_start,
            '/settings': self.cmd_settings,
            '/set_format': self.cmd_set_format,
            '/set_signature': self.cmd_set_signature,
            '/set_quality': self.cmd_set_quality,
            '/set_length': self.cmd_set_length,
            '/set_interval': self.cmd_set_interval,
            '/set_batch': self.cmd_set_batch,
            '/add_bot': self.cmd_add_bot,
            '/remove_bot': self.cmd_remove_bot,
            '/list_bots': self.cmd_list_bots,
            '/set_hashtags': self.cmd_set_hashtags,
            '/set_links': self.cmd_set_links,
            '/filter_numbers': self.cmd_filter_numbers,
            '/status': self.cmd_status,
            '/reset': self.cmd_reset,
            '/help': self.cmd_help,
            '/start_scan': self.cmd_start_scan,
            '/stop_scan': self.cmd_stop_scan,
            '/set_platforms': self.cmd_set_platforms,
            '/add_blacklist': self.cmd_add_blacklist,
            '/remove_blacklist': self.cmd_remove_blacklist,
            '/show_blacklist': self.cmd_show_blacklist,
            '/set_proxy': self.cmd_set_proxy,
            '/test_bot': self.cmd_test_bot,
            '/stats': self.cmd_stats,
            '/export': self.cmd_export,
            '/send_report': self.cmd_send_report,
            '/set_timer': self.cmd_set_timer,
            '/pause': self.cmd_pause,
            '/resume': self.cmd_resume,
            '/restart': self.cmd_restart,
            '/set_platform_token': self.cmd_set_platform_token,
            '/set_sequential': self.cmd_set_sequential,
            '/show_tokens': self.cmd_show_tokens,
        }
    
    # ========== دالة الإرسال الأساسية (مع إعادة المحاولة) ==========
    def send_message(self, text: str, platform: str = None, parse_mode: str = 'HTML', disable_web: bool = True) -> bool:
        """إرسال رسالة باستخدام التوكن الخاص بالمنصة أو التوكن الرئيسي مع إعادة المحاولة"""
        if not self.config.enabled:
            return False
        
        token = self.config.token
        chat_id = self.config.chat_id
        
        if platform and platform in self.config.platform_tokens:
            pt = self.config.platform_tokens[platform]
            if pt.get('token') and pt.get('chat_id'):
                token = pt['token']
                chat_id = pt['chat_id']
        
        if not token or not chat_id:
            return False
        
        with self.config.lock:
            current = time.time()
            if current - self.last_sent < self.min_interval:
                time.sleep(self.min_interval - (current - self.last_sent))
            
            for attempt in range(3):
                try:
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    data = {
                        'chat_id': chat_id,
                        'text': text,
                        'parse_mode': parse_mode,
                        'disable_web_page_preview': disable_web
                    }
                    r = self.session.post(url, data=data, timeout=15)
                    if r.status_code == 200:
                        self.last_sent = time.time()
                        return True
                    else:
                        time.sleep(2 ** attempt)
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    logger.warning(f"محاولة {attempt+1} فشلت: {str(e)[:50]}")
                    if attempt == 2:
                        logger.error("فشل إرسال الرسالة بعد 3 محاولات")
                    else:
                        time.sleep(2 ** attempt)
                except Exception as e:
                    logger.error(f"خطأ غير متوقع: {str(e)[:50]}")
                    break
        return False
    
    # ========== دالة إرسال اسم متاح (الدالة المفقودة) ==========
    def send_username_found(self, username: str, platform: str, quality: int) -> bool:
        """إرسال إشعار بوجود اسم متاح باستخدام توكن المنصة"""
        try:
            if not self.config.enabled:
                return False
            if self.config.paused:
                return False
            if not self.config.should_send(username, quality):
                return False
            
            self.config.update_platform_stats(platform)
            platform_count = self.config.platform_stats.get(platform, 0)
            
            formatted = self.config.format_message(username, platform, quality, platform_count)
            if self.config.hashtags:
                formatted += f"\n\n🏷️ {self.config.hashtags}"
            if self.config.links:
                formatted += f"\n\n🔗 {self.config.links}"
            
            mode = self.config.send_mode
            if mode == 'instant':
                self.send_message(formatted, platform)
                self.send_to_backup_bots(formatted)
                return True
            elif mode == 'batch':
                with self.batch_lock:
                    self.batch_messages.append(formatted)
                    if len(self.batch_messages) >= self.config.batch_size:
                        combined = '\n\n━━━━━━━━━━━━━━━━━\n\n'.join(self.batch_messages)
                        self.send_message(combined, platform)
                        self.send_to_backup_bots(combined)
                        self.batch_messages = []
                return True
            elif mode == 'interval':
                current = time.time()
                if current - self.last_sent >= self.config.send_interval:
                    self.send_message(formatted, platform)
                    self.send_to_backup_bots(formatted)
                    self.last_sent = current
                else:
                    with self.batch_lock:
                        self.batch_messages.append(formatted)
                        if len(self.batch_messages) >= self.config.batch_size:
                            combined = '\n\n━━━━━━━━━━━━━━━━━\n\n'.join(self.batch_messages)
                            self.send_message(combined, platform)
                            self.send_to_backup_bots(combined)
                            self.batch_messages = []
                return True
            return False
        except Exception as e:
            logger.error(f"خطأ في إرسال الاسم {username}: {str(e)[:50]}")
            return False
    
    # ========== دوال البوت الأخرى ==========
    def send_to_backup_bots(self, text: str):
        for bot in self.config.backup_bots:
            try:
                url = f"https://api.telegram.org/bot{bot['token']}/sendMessage"
                data = {'chat_id': bot['chat_id'], 'text': text, 'parse_mode': 'HTML'}
                self.session.post(url, data=data, timeout=5)
            except:
                pass
    
    def send_summary(self, results: List[Dict]) -> bool:
        if not results:
            return False
        total = len(results)
        if total == 0:
            return False
        
        platform_summary = Counter(item['platform'] for item in results)
        platform_lines = '\n'.join([f"  • {p}: {c}" for p, c in platform_summary.items()])
        found_list = '\n'.join([f"✅ @{item['username']} ({item['platform']}) - جودة: {item['quality']}/20" for item in results[:20]])
        if total > 20:
            found_list += f"\n... وعرض {total - 20} اسم آخر"
        
        msg = f"""
<b>📊 ملخص الدفعة #{self.summary_counter + 1}</b>
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>✅ تم العثور:</b> {total} اسم
<b>📅 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
<b>⏱️ المدة:</b> {str(datetime.now() - self.start_time).split('.')[0]}

<b>📊 إحصائيات المنصات:</b>
{platform_lines}

<b>📝 الأسماء:</b>
{found_list}
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
"""
        self.summary_counter += 1
        return self.send_message(msg)
    
    # ============================================================
    # أوامر البوت (تم اختصارها هنا، ولكنها موجودة كاملة في الملف الأصلي)
    # ============================================================
    def cmd_start(self, args: List[str]) -> str:
        return """
<b>🤖 مرحباً بك في WORMGPT Bot v7.0!</b>
<b>📌 أنا بوت للتحكم في أداة البحث عن الأسماء المتاحة.</b>
<b>🛡️ النسخة السوداء - بلاك إديشن</b>
<b>📋 الأوامر المتاحة:</b>
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>📝 الإعدادات:</b>
/settings - عرض الإعدادات الحالية
/set_format - تغيير تنسيق الرسالة
/set_signature - إضافة توقيع
/set_quality - تحديد جودة الأسماء (0-20)
/set_length - تحديد طول الأسماء (min max)
/set_interval - فترة الإرسال بالثواني
/set_batch - تجميع الأسماء (عدد)
/set_platforms - تحديد المنصات النشطة
/set_timer - تحديد مؤقت زمني للمسح (ثواني)
/set_platform_token - تعيين توكن بوت لمنصة
/set_sequential - تفعيل/تعطيل الاكتشاف المتسلسل
/show_tokens - عرض توكنات المنصات

<b>🔍 التصفية:</b>
/filter_numbers - تفعيل/تعطيل الأرقام
/add_blacklist - إضافة كلمة ممنوعة
/remove_blacklist - حذف كلمة ممنوعة
/show_blacklist - عرض الكلمات الممنوعة

<b>🤖 البوتات:</b>
/add_bot - إضافة بوت احتياطي
/remove_bot - حذف بوت احتياطي
/list_bots - عرض البوتات الاحتياطية
/test_bot - اختبار البوت

<b>📊 التحكم:</b>
/start_scan - بدء المسح
/stop_scan - إيقاف المسح
/pause - إيقاف الإشعارات مؤقتاً
/resume - استئناف الإشعارات
/restart - إعادة ضبط المسح
/status - عرض الحالة والإحصائيات
/stats - عرض إحصائيات مفصلة
/export - تصدير النتائج
/send_report - إرسال آخر تقرير عبر البوت

<b>⚙️ أخرى:</b>
/set_hashtags - إضافة هاشتاجات
/set_links - إضافة روابط
/set_proxy - إضافة بروكسي
/reset - إعادة ضبط الإعدادات
/help - عرض هذه القائمة

<b>📢 القناة:</b> @smopel
        """
    
    def cmd_settings(self, args: List[str]) -> str:
        s = self.config
        platform_tokens_info = '\n'.join([f"  • {p}: 🆔 {d['chat_id'][:10]}..." for p, d in s.platform_tokens.items()]) if s.platform_tokens else "  لا توجد توكنات مخصصة"
        return f"""
<b>⚙️ الإعدادات الحالية</b>
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>📝 التنسيق:</b>
{s.message_format[:100]}...
<b>✍️ التوقيع:</b> {s.signature}
<b>🏷️ الهاشتاجات:</b> {s.hashtags}
<b>🔗 الروابط:</b> {s.links or 'لا يوجد'}
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>📊 التصفية:</b>
• جودة: {s.min_quality}+
• طول: {s.min_length}-{s.max_length}
• أرقام: {'❌ ممنوعة' if s.filter_numbers else '✅ مسموحة'}
• كلمات ممنوعة: {len(s.blacklist)} كلمة
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>⏱️ الإرسال:</b>
• وضع: {s.send_mode}
• فترة: {s.send_interval} ثانية
• تجميع: {s.batch_size} اسم
<b>⏱️ المؤقت:</b> {s.scan_timer} ثانية ({'لا نهائي' if s.scan_timer == 0 else f'{s.scan_timer//60} دقيقة'})
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>🔑 توكنات المنصات:</b>
{platform_tokens_info}
<b>🔄 الاكتشاف المتسلسل:</b> {'✅ مفعل' if s.sequential_mode else '❌ معطل'}
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>🌐 المنصات:</b>
{', '.join(s.active_platforms)}
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>📈 الإحصائيات:</b>
• تم التحقق: {s.total_checked}
• تم العثور: {s.total_found}
• النسبة: {(s.total_found / s.total_checked * 100) if s.total_checked > 0 else 0:.2f}%
• الحالة: {'🟢 يعمل' if s.scan_status == 'running' else '🔴 متوقف'}
• الإشعارات: {'⏸️ موقفة' if s.paused else '▶️ مفعلة'}
        """
    
    def cmd_status(self, args: List[str]) -> str:
        s = self.config
        timer_status = f"{s.scan_timer} ثانية" if s.scan_timer > 0 else "🔄 لا نهائي"
        pause_status = "⏸️ موقف" if s.paused else "▶️ يعمل"
        platform_stats = '\n'.join([f"  • {p}: {c}" for p, c in s.platform_stats.items()]) if s.platform_stats else "  لا توجد إحصائيات"
        return f"""
<b>📊 حالة البوت</b>
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>✅ الحالة:</b> {'🟢 مفعل' if s.enabled else '🔴 معطل'}
<b>🔄 حالة المسح:</b> {'🟢 يعمل' if s.scan_status == 'running' else '🔴 متوقف'}
<b>⏸️ الإشعارات:</b> {pause_status}
<b>⏱️ المؤقت:</b> {timer_status}
<b>📅 بدء التشغيل:</b> {s.start_time}
<b>📈 الإحصائيات:</b>
• تم التحقق: <b>{s.total_checked}</b>
• تم العثور: <b>{s.total_found}</b>
• النسبة: <b>{(s.total_found / s.total_checked * 100) if s.total_checked > 0 else 0:.2f}%</b>
<b>📊 إحصائيات المنصات:</b>
{platform_stats}
<b>🔑 توكنات المنصات:</b> {len(s.platform_tokens)} منصة
<b>🤖 البوتات الاحتياطية:</b> {len(s.backup_bots)}
<b>🌐 المنصات النشطة:</b> {len(s.active_platforms)}
<b>🛡️ الكلمات الممنوعة:</b> {len(s.blacklist)}
        """
    
    def cmd_set_format(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال التنسيق الجديد.\nمثال: /set_format 🎯 تم العثور على @{username}"
        new_format = ' '.join(args)
        self.config.message_format = new_format
        self.config.save()
        return f"✅ تم تحديث تنسيق الرسالة:\n\n{new_format[:200]}"
    
    def cmd_set_signature(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال التوقيع الجديد.\nمثال: /set_signature 🖤 بواسطة @MyBot"
        self.config.signature = ' '.join(args)
        self.config.save()
        return f"✅ تم تحديث التوقيع:\n{self.config.signature}"
    
    def cmd_set_quality(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال قيمة الجودة (0-20).\nمثال: /set_quality 10"
        try:
            q = int(args[0])
            if 0 <= q <= 20:
                self.config.min_quality = q
                self.config.save()
                return f"✅ تم تحديد الجودة الدنيا: {q}+"
            return "❌ القيمة بين 0 و 20"
        except:
            return "❌ يرجى إدخال رقم صحيح"
    
    def cmd_set_length(self, args: List[str]) -> str:
        if len(args) < 2:
            return "❌ يرجى إرسال الحد الأدنى والأقصى.\nمثال: /set_length 3 10"
        try:
            min_l = int(args[0])
            max_l = int(args[1])
            if 0 <= min_l <= max_l <= 20:
                self.config.min_length = min_l
                self.config.max_length = max_l
                self.config.save()
                return f"✅ تم تحديد الطول: {min_l}-{max_l}"
            return "❌ قيم غير صحيحة (0-20)"
        except:
            return "❌ يرجى إدخال أرقام صحيحة"
    
    def cmd_set_interval(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال الفترة بالثواني.\nمثال: /set_interval 10"
        try:
            interval = int(args[0])
            if interval > 0:
                self.config.send_interval = interval
                self.config.send_mode = 'interval'
                self.config.save()
                return f"✅ تم تحديد الفترة: {interval} ثانية"
            return "❌ يجب أن تكون أكبر من 0"
        except:
            return "❌ يرجى إدخال رقم صحيح"
    
    def cmd_set_batch(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال عدد الأسماء للتجميع.\nمثال: /set_batch 10"
        try:
            batch = int(args[0])
            if batch > 0:
                self.config.batch_size = batch
                self.config.send_mode = 'batch'
                self.config.save()
                return f"✅ تم تحديد التجميع: {batch} اسم في رسالة واحدة"
            return "❌ يجب أن تكون أكبر من 0"
        except:
            return "❌ يرجى إدخال رقم صحيح"
    
    def cmd_add_bot(self, args: List[str]) -> str:
        if len(args) < 2:
            return "❌ يرجى إرسال التوكن والمعرف.\nمثال: /add_bot TOKEN CHAT_ID"
        token = args[0]
        chat_id = args[1]
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                self.config.backup_bots.append({'token': token, 'chat_id': chat_id})
                self.config.save()
                return f"✅ تم إضافة البوت الاحتياطي بنجاح!"
            return "❌ فشل الاتصال بالبوت"
        except:
            return "❌ خطأ في الاتصال"
    
    def cmd_remove_bot(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال رقم البوت.\nمثال: /remove_bot 1"
        try:
            idx = int(args[0]) - 1
            if 0 <= idx < len(self.config.backup_bots):
                removed = self.config.backup_bots.pop(idx)
                self.config.save()
                return f"✅ تم حذف البوت رقم {idx+1}"
            return "❌ رقم غير صحيح"
        except:
            return "❌ يرجى إدخال رقم صحيح"
    
    def cmd_list_bots(self, args: List[str]) -> str:
        bots = self.config.backup_bots
        if not bots:
            return "📋 لا توجد بوتات احتياطية"
        result = "📋 <b>قائمة البوتات الاحتياطية:</b>\n\n"
        for i, bot in enumerate(bots, 1):
            result += f"{i}. 🆔 {bot['chat_id'][:10]}...\n"
        return result
    
    def cmd_set_hashtags(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال الهاشتاجات.\nمثال: /set_hashtags #WORMGPT #Hunter"
        self.config.hashtags = ' '.join(args)
        self.config.save()
        return f"✅ تم تحديث الهاشتاجات:\n{self.config.hashtags}"
    
    def cmd_set_links(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال الروابط.\nمثال: /set_links https://t.me/MyChannel"
        self.config.links = ' '.join(args)
        self.config.save()
        return f"✅ تم تحديث الروابط:\n{self.config.links}"
    
    def cmd_filter_numbers(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى تحديد true/false.\nمثال: /filter_numbers true"
        val = args[0].lower()
        if val in ['true', '1', 'yes', 'تفعيل']:
            self.config.filter_numbers = True
        elif val in ['false', '0', 'no', 'تعطيل']:
            self.config.filter_numbers = False
        else:
            return "❌ القيم المسموحة: true / false"
        self.config.save()
        return f"✅ تم {'تفعيل' if self.config.filter_numbers else 'تعطيل'} منع الأرقام"
    
    def cmd_reset(self, args: List[str]) -> str:
        self.config._init_defaults()
        self.config.save()
        return "✅ تم إعادة ضبط جميع الإعدادات إلى الافتراضية"
    
    def cmd_help(self, args: List[str]) -> str:
        return self.cmd_start(args)
    
    def cmd_start_scan(self, args: List[str]) -> str:
        if self.config.scan_status == 'running':
            return "⚠️ المسح قيد التشغيل بالفعل!"
        self.config.scan_status = 'running'
        self.config.save()
        return "✅ تم بدء المسح!"
    
    def cmd_stop_scan(self, args: List[str]) -> str:
        if self.config.scan_status == 'stopped':
            return "⚠️ المسح متوقف بالفعل!"
        self.config.scan_status = 'stopped'
        self.config.save()
        return "⏹️ تم إيقاف المسح!"
    
    def cmd_set_platforms(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال المنصات مفصولة بفواصل.\nمثال: /set_platforms Instagram,Twitter,YouTube"
        platforms = [p.strip() for p in ' '.join(args).split(',') if p.strip()]
        if platforms:
            self.config.active_platforms = platforms
            self.config.save()
            return f"✅ تم تحديث المنصات:\n{', '.join(platforms)}"
        return "❌ لم يتم إدخال منصات صحيحة"
    
    def cmd_add_blacklist(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال الكلمة الممنوعة.\nمثال: /add_blacklist admin"
        word = args[0].lower()
        if word not in self.config.blacklist:
            self.config.blacklist.append(word)
            self.config.save()
            return f"✅ تم إضافة '{word}' إلى القائمة السوداء"
        return f"⚠️ '{word}' موجود بالفعل في القائمة"
    
    def cmd_remove_blacklist(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال الكلمة المراد حذفها.\nمثال: /remove_blacklist admin"
        word = args[0].lower()
        if word in self.config.blacklist:
            self.config.blacklist.remove(word)
            self.config.save()
            return f"✅ تم حذف '{word}' من القائمة السوداء"
        return f"⚠️ '{word}' غير موجود في القائمة"
    
    def cmd_show_blacklist(self, args: List[str]) -> str:
        if not self.config.blacklist:
            return "📋 القائمة السوداء فارغة"
        return f"📋 <b>القائمة السوداء:</b>\n\n" + '\n'.join([f"🚫 {w}" for w in self.config.blacklist])
    
    def cmd_set_proxy(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال البروكسي.\nمثال: /set_proxy http://127.0.0.1:8080"
        proxy = args[0]
        self.config.proxies.append(proxy)
        self.config.use_proxy = True
        self.config.save()
        return f"✅ تم إضافة البروكسي: {proxy}"
    
    def cmd_test_bot(self, args: List[str]) -> str:
        if self.send_message("🧪 <b>اختبار البوت</b>\n\n✅ تم الاتصال بنجاح!"):
            return "✅ تم إرسال رسالة اختبار"
        return "❌ فشل إرسال رسالة الاختبار"
    
    def cmd_stats(self, args: List[str]) -> str:
        s = self.config
        platform_stats = '\n'.join([f"  • {p}: {c}" for p, c in s.platform_stats.items()]) if s.platform_stats else "  لا توجد إحصائيات"
        return f"""
<b>📊 إحصائيات مفصلة</b>
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>🔍 الفحص:</b>
• تم التحقق: <b>{s.total_checked}</b>
• تم العثور: <b>{s.total_found}</b>
• نسبة النجاح: <b>{(s.total_found / s.total_checked * 100) if s.total_checked > 0 else 0:.2f}%</b>
<b>📊 إحصائيات المنصات:</b>
{platform_stats}
<b>⚙️ الإعدادات:</b>
• الجودة الدنيا: {s.min_quality}
• طول الأسماء: {s.min_length}-{s.max_length}
• وضع الإرسال: {s.send_mode}
• عدد الخيوط: {s.threads}
• التأخير: {s.delay} ثانية
<b>🤖 البوت:</b>
• البوت الرئيسي: {'✅ مفعل' if s.enabled else '❌ معطل'}
• توكنات المنصات: {len(s.platform_tokens)} منصة
• البوتات الاحتياطية: {len(s.backup_bots)}
• حالة المسح: {'🟢 يعمل' if s.scan_status == 'running' else '🔴 متوقف'}
<b>🌐 المنصات:</b>
{', '.join(s.active_platforms)}
        """
    
    def cmd_export(self, args: List[str]) -> str:
        if not self.config.total_found:
            return "❌ لا توجد نتائج لتصديرها"
        filename = f"wormgpt_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"WORMGPT Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Total Found: {self.config.total_found}\n")
                f.write(f"Total Checked: {self.config.total_checked}\n")
                f.write(f"Success Rate: {(self.config.total_found / self.config.total_checked * 100) if self.config.total_checked > 0 else 0:.2f}%\n")
                f.write("=" * 50 + "\n")
                for platform, count in self.config.platform_stats.items():
                    f.write(f"{platform}: {count}\n")
            return f"✅ تم تصدير النتائج إلى {filename}"
        except:
            return "❌ خطأ في تصدير النتائج"
    
    def cmd_send_report(self, args: List[str]) -> str:
        files = glob.glob("wormgpt_results_*.json") + glob.glob("wormgpt_results_*.txt") + glob.glob("wormgpt_results_*.html")
        if not files:
            return "❌ لا توجد تقارير لإرسالها"
        latest = max(files, key=os.path.getctime)
        self.config.last_report_file = latest
        self.config.save()
        try:
            url = f"https://api.telegram.org/bot{self.config.token}/sendDocument"
            files_data = {'document': open(latest, 'rb')}
            data = {'chat_id': self.config.chat_id, 'caption': f"📊 تقرير WORMGPT\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
            r = requests.post(url, files=files_data, data=data, timeout=30)
            if r.status_code == 200:
                return f"✅ تم إرسال الملف: {latest}"
            return f"❌ فشل إرسال الملف: {r.text[:100]}"
        except Exception as e:
            return f"❌ خطأ: {str(e)}"
    
    def cmd_set_timer(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال المدة بالثواني.\nمثال: /set_timer 300 (لمدة 5 دقائق)"
        try:
            timer = int(args[0])
            if timer < 0:
                return "❌ يجب أن تكون المدة أكبر من 0"
            self.config.scan_timer = timer
            self.config.save()
            if timer == 0:
                return "✅ تم إلغاء المؤقت (مسح لا نهائي)"
            return f"✅ تم تحديد المؤقت: {timer} ثانية ({timer//60} دقيقة)"
        except:
            return "❌ يرجى إدخال رقم صحيح"
    
    def cmd_pause(self, args: List[str]) -> str:
        self.config.paused = True
        self.config.save()
        return "⏸️ تم إيقاف الإشعارات مؤقتاً. استخدم /resume لاستئناف الإرسال."
    
    def cmd_resume(self, args: List[str]) -> str:
        self.config.paused = False
        self.config.save()
        return "▶️ تم استئناف الإشعارات."
    
    def cmd_restart(self, args: List[str]) -> str:
        self.config.total_found = 0
        self.config.total_checked = 0
        self.config.scan_status = 'stopped'
        self.config.scan_start_time = datetime.now().isoformat()
        self.config.platform_stats = {}
        self.config.save()
        return "🔄 تم إعادة ضبط المسح. استخدم /start_scan لبدء مسح جديد."
    
    def cmd_set_platform_token(self, args: List[str]) -> str:
        if len(args) < 3:
            return "❌ يرجى إرسال: /set_platform_token <المنصة> <التوكن> <معرف الشات>\nمثال: /set_platform_token Instagram 123:abc 456"
        platform = args[0]
        token = args[1]
        chat_id = args[2]
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return "❌ فشل الاتصال بالبوت، تحقق من التوكن"
        except:
            return "❌ خطأ في الاتصال بالبوت"
        self.config.platform_tokens[platform] = {'token': token, 'chat_id': chat_id}
        self.config.save()
        return f"✅ تم تعيين توكن لمنصة {platform} بنجاح!"
    
    def cmd_show_tokens(self, args: List[str]) -> str:
        if not self.config.platform_tokens:
            return "📋 لا توجد توكنات مخصصة للمنصات"
        result = "📋 <b>توكنات المنصات:</b>\n\n"
        for platform, data in self.config.platform_tokens.items():
            result += f"• {platform}: 🆔 {data['chat_id'][:10]}...\n"
        return result
    
    def cmd_set_sequential(self, args: List[str]) -> str:
        if not args:
            return "❌ يرجى إرسال true/false.\nمثال: /set_sequential true"
        val = args[0].lower()
        if val in ['true', '1', 'yes', 'تفعيل']:
            self.config.sequential_mode = True
            self.config.save()
            return "✅ تم تفعيل وضع الاكتشاف المتسلسل"
        elif val in ['false', '0', 'no', 'تعطيل']:
            self.config.sequential_mode = False
            self.config.save()
            return "✅ تم تعطيل وضع الاكتشاف المتسلسل"
        else:
            return "❌ القيم المسموحة: true / false"

# ================================================================
# إعداد البوت
# ================================================================

def setup_bot_config():
    global bot_config
    if bot_config.enabled and bot_config.token and bot_config.chat_id:
        return
    show_banner()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}🤖 إعداد البوت{C.CYAN}                     ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)
    print(f"{C.YELLOW}[!] لم يتم العثور على إعدادات البوت أو أنها غير مكتملة.{C.RESET}")
    print(f"{C.YELLOW}[!] يرجى إدخال التوكن والمعرف الرئيسيين لتشغيل البوت.{C.RESET}\n")
    token = input(f"{C.GREEN}🔑 توكن البوت الرئيسي: {C.WHITE}").strip()
    chat_id = input(f"{C.GREEN}🆔 معرف الشات الرئيسي: {C.WHITE}").strip()
    if token and chat_id:
        bot_config.token = token
        bot_config.chat_id = chat_id
        bot_config.enabled = True
        bot_config.save()
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                logger.success("تم الاتصال بالبوت الرئيسي بنجاح!")
            else:
                logger.error("فشل الاتصال بالبوت، تحقق من التوكن")
                bot_config.enabled = False
                bot_config.save()
        except:
            logger.error("خطأ في الاتصال بالبوت")
            bot_config.enabled = False
            bot_config.save()
    else:
        logger.error("التوكن والمعرف مطلوبين، سيتم تعطيل البوت")
        bot_config.enabled = False
        bot_config.save()

# ================================================================
# محرك البحث عن الأسماء مع الاكتشاف المتسلسل
# ================================================================

class UsernameScanner:
    """ماسح الأسماء المتقدم مع دعم متعدد المنصات والاكتشاف المتسلسل"""
    
    def __init__(self):
        self.bot = WormBot()
        self.found = []
        self.checked = 0
        self.running = False
        self.lock = Lock()
        self.results = []
        self.batch_results = []
        self.summary_interval = bot_config.batch_size
        self.platforms = bot_config.active_platforms
        self.start_time = datetime.now()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.scan_thread = None
        self.platform_stats = defaultdict(int)
        self.sequential_base = None
        self.sequential_counter = 0
    
    # ============================================================
    # دوال التحقق من المنصات (مع إعادة المحاولة)
    # ============================================================
    
    def check_instagram(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://www.instagram.com/{username}/"
                r = self.session.get(url, timeout=bot_config.timeout)
                if r.status_code == 404:
                    return True, "متاح"
                elif r.status_code == 200:
                    if 'Page Not Found' in r.text or 'Sorry, this page' in r.text:
                        return True, "متاح"
                    return False, "مستخدم"
                return False, "خطأ"
            except:
                if attempt == bot_config.retry_count - 1:
                    return False, "خطأ"
                time.sleep(random.uniform(1, 3))
        return False, "خطأ"
    
    def check_twitter(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://twitter.com/{username}"
                r = self.session.get(url, timeout=bot_config.timeout)
                if r.status_code == 404:
                    return True, "متاح"
                elif r.status_code == 200:
                    if 'This account doesn’t exist' in r.text or 'Not found' in r.text:
                        return True, "متاح"
                    return False, "مستخدم"
                return False, "خطأ"
            except:
                if attempt == bot_config.retry_count - 1:
                    return False, "خطأ"
                time.sleep(random.uniform(1, 3))
        return False, "خطأ"
    
    def check_tiktok(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://www.tiktok.com/@{username}"
                r = self.session.get(url, timeout=bot_config.timeout)
                if 'webapp.user-detail' in r.text:
                    return False, "مستخدم"
                return True, "متاح"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    def check_telegram(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://t.me/{username}"
                r = self.session.get(url, timeout=bot_config.timeout)
                if 'Sorry, this username doesn' in r.text or 'not found' in r.text:
                    return True, "متاح"
                return False, "مستخدم"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    def check_youtube(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://www.youtube.com/@{username}"
                r = self.session.get(url, timeout=bot_config.timeout)
                if r.status_code == 404:
                    return True, "متاح"
                return False, "مستخدم"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    def check_snapchat(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://www.snapchat.com/add/{username}"
                r = self.session.get(url, timeout=bot_config.timeout)
                if 'could not find' in r.text.lower():
                    return True, "متاح"
                return False, "مستخدم"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    def check_tumblr(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://{username}.tumblr.com"
                r = self.session.get(url, timeout=bot_config.timeout)
                if r.status_code == 404:
                    return True, "متاح"
                return False, "مستخدم"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    def check_github(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://github.com/{username}"
                r = self.session.get(url, timeout=bot_config.timeout)
                if r.status_code == 404:
                    return True, "متاح"
                return False, "مستخدم"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    def check_reddit(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://www.reddit.com/user/{username}"
                r = self.session.get(url, timeout=bot_config.timeout)
                if 'page not found' in r.text.lower():
                    return True, "متاح"
                return False, "مستخدم"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    def check_pinterest(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://www.pinterest.com/{username}/"
                r = self.session.get(url, timeout=bot_config.timeout)
                if r.status_code == 404:
                    return True, "متاح"
                return False, "مستخدم"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    def check_spotify(self, username: str) -> Tuple[bool, str]:
        for attempt in range(bot_config.retry_count):
            try:
                url = f"https://open.spotify.com/user/{username}"
                r = self.session.get(url, timeout=bot_config.timeout)
                if r.status_code == 404:
                    return True, "متاح"
                return False, "مستخدم"
            except:
                if attempt == bot_config.retry_count - 1:
                    return True, "متاح"
                time.sleep(random.uniform(1, 3))
        return True, "متاح"
    
    # ============================================================
    # توليد الأنماط المشتقة (الاكتشاف المتسلسل)
    # ============================================================
    
    def generate_sequential_usernames(self, base_username: str, limit: int = 100) -> List[str]:
        """توليد أسماء مشتقة من اسم أساسي"""
        usernames = []
        match = re.match(r'^(.*?)(\d+)$', base_username)
        if match:
            prefix = match.group(1)
            num = int(match.group(2))
            for i in range(1, limit + 1):
                new_num = num + i
                usernames.append(f"{prefix}{new_num}")
            return usernames
        
        if '_' in base_username or '.' in base_username:
            separator = '_' if '_' in base_username else '.'
            parts = base_username.split(separator)
            if len(parts) >= 2:
                for i in range(1, limit + 1):
                    new_username = f"{parts[0]}{separator}{i}"
                    usernames.append(new_username)
                return usernames
        
        for i in range(1, limit + 1):
            usernames.append(f"{base_username}{i}")
        return usernames
    
    # ============================================================
    # تقييم الجودة
    # ============================================================
    
    def check_quality(self, username: str) -> int:
        score = 0
        length = len(username)
        if length <= 4:
            score += 10
        elif length <= 6:
            score += 7
        elif length <= 8:
            score += 4
        if not any(c.isdigit() for c in username):
            score += 5
        else:
            score += 2
        if '_' not in username:
            score += 3
        if username[0].isupper():
            score += 3
        common = ['tech', 'pro', 'dev', 'web', 'ai', 'bot', 'cloud', 'data', 'iam', 'the', 'mr', 'dr', 'its', 'real']
        for p in common:
            if p in username.lower():
                score += 8
                break
        if length <= 5 and '_' not in username and not any(c.isdigit() for c in username):
            score += 5
        return min(score, 20)
    
    # ============================================================
    # توليد الأسماء العشوائية
    # ============================================================
    
    def generate_usernames(self, pattern_type: int, length: int, count: int = 100) -> List[str]:
        usernames = []
        letters = 'abcdefghijklmnopqrstuvwxyz'
        numbers = '0123456789'
        all_chars = letters + numbers
        wordlist = [
            'tech', 'pro', 'dev', 'web', 'ai', 'bot', 'cloud', 'data',
            'iam', 'the', 'its', 'real', 'best', 'top', 'one', 'new',
            'cool', 'smart', 'fast', 'dark', 'light', 'fire', 'ice',
            'star', 'moon', 'sun', 'sky', 'king', 'queen', 'lord'
        ]
        for _ in range(count):
            if pattern_type == 1:
                parts = [
                    ''.join(random.choice(letters) for _ in range(1, 3)),
                    ''.join(random.choice(all_chars) for _ in range(1, 3)),
                    ''.join(random.choice(all_chars) for _ in range(1, 3))
                ]
                username = '_'.join(parts)
            elif pattern_type == 2:
                parts = [
                    ''.join(random.choice(letters) for _ in range(1, 3)),
                    ''.join(random.choice(all_chars) for _ in range(2, 4))
                ]
                username = '_'.join(parts)
            elif pattern_type == 3:
                parts = [
                    ''.join(random.choice(all_chars) for _ in range(2, 4)),
                    ''.join(random.choice(all_chars) for _ in range(1, 3))
                ]
                username = '_'.join(parts)
            elif pattern_type == 4:
                parts = [
                    ''.join(random.choice(all_chars) for _ in range(2, 3)),
                    ''.join(random.choice(all_chars) for _ in range(2, 3))
                ]
                username = '_'.join(parts)
            elif pattern_type == 5:
                parts = [
                    ''.join(random.choice(letters) for _ in range(1, 2)),
                    ''.join(random.choice(all_chars) for _ in range(2, 4))
                ]
                username = '_'.join(parts)
            elif pattern_type == 6:
                parts = [
                    ''.join(random.choice(letters) for _ in range(1, 2)),
                    ''.join(random.choice(all_chars) for _ in range(1, 2)),
                    ''.join(random.choice(all_chars) for _ in range(1, 2)),
                    ''.join(random.choice(all_chars) for _ in range(1, 2))
                ]
                username = '_'.join(parts)
            elif pattern_type == 7:
                word = random.choice(wordlist)
                if len(word) < length:
                    remaining = length - len(word)
                    username = word + ''.join(random.choice(numbers) for _ in range(remaining))
                else:
                    username = word[:length]
            elif pattern_type == 8:
                word = random.choice(wordlist)
                if len(word) < length:
                    remaining = length - len(word)
                    username = ''.join(random.choice(numbers) for _ in range(remaining)) + word
                else:
                    username = word[:length]
            else:
                username = ''.join(random.choice(all_chars) for _ in range(length))
            usernames.append(username)
        return usernames
    
    # ============================================================
    # فحص اسم واحد
    # ============================================================
    
    def scan_single(self, username: str, platforms: List[str] = None) -> List[Dict]:
        if platforms is None:
            platforms = self.platforms
        checkers = {
            'Instagram': self.check_instagram,
            'Twitter': self.check_twitter,
            'TikTok': self.check_tiktok,
            'Telegram': self.check_telegram,
            'YouTube': self.check_youtube,
            'Snapchat': self.check_snapchat,
            'Tumblr': self.check_tumblr,
            'GitHub': self.check_github,
            'Reddit': self.check_reddit,
            'Pinterest': self.check_pinterest,
            'Spotify': self.check_spotify
        }
        results = []
        for platform in platforms:
            if platform not in checkers:
                continue
            available, status = checkers[platform](username)
            if available:
                quality = self.check_quality(username)
                results.append({
                    'username': username,
                    'platform': platform,
                    'quality': quality,
                    'timestamp': datetime.now().isoformat()
                })
        return results
    
    # ============================================================
    # تصدير HTML
    # ============================================================
    
    def export_html(self, results: List[Dict], filename: str):
        platform_summary = Counter(item['platform'] for item in results)
        platform_rows = '\n'.join([f"<tr><td>{p}</td><td>{c}</td></tr>" for p, c in platform_summary.items()])
        html = f"""
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تقرير WORMGPT</title>
    <style>
        body {{ font-family: Arial; background: #0a0a0a; color: #00ffcc; padding: 20px; }}
        h1, h2 {{ color: #00ffcc; }}
        table {{ width: 100%; border-collapse: collapse; background: #1a1a1a; margin-top: 10px; }}
        th, td {{ border: 1px solid #00ffcc; padding: 10px; text-align: right; }}
        th {{ background: #003333; }}
        .good {{ color: #00ff88; }}
        .medium {{ color: #ffaa00; }}
        .low {{ color: #ff4444; }}
        .summary {{ background: #002222; }}
    </style>
</head>
<body>
    <h1>📊 تقرير WORMGPT</h1>
    <p>التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>عدد النتائج: {len(results)}</p>
    <h2>📊 إحصائيات المنصات</h2>
    <table class="summary">
        <tr><th>المنصة</th><th>عدد المتاحات</th></tr>
        {platform_rows}
    </table>
    <h2>📝 قائمة المتاحات</h2>
    <table>
        <tr><th>#</th><th>الاسم</th><th>المنصة</th><th>الجودة</th></tr>
"""
        for i, item in enumerate(results, 1):
            quality_class = "good" if item['quality'] >= 15 else "medium" if item['quality'] >= 10 else "low"
            html += f"<tr><td>{i}</td><td>@{item['username']}</td><td>{item['platform']}</td><td class='{quality_class}'>{item['quality']}/20</td></tr>\n"
        html += """
    </table>
    <p>🖤 بواسطة WORMGPT | @W4_M4</p>
</body>
</html>
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.success(f"تم تصدير HTML إلى {filename}")
    
    # ============================================================
    # المسح المتقدم مع الاكتشاف المتسلسل
    # ============================================================
    
    def advanced_scan(self, pattern_type: int, length: int, platforms: List[str] = None,
                      threads: int = 20, max_cycles: int = 0):
        if platforms is None:
            platforms = self.platforms
        self.found = []
        self.checked = 0
        self.running = True
        self.results = []
        self.batch_results = []
        self.start_time = datetime.now()
        self.platform_stats = defaultdict(int)
        self.sequential_base = None
        self.sequential_counter = 0
        
        bot_config.scan_status = 'running'
        bot_config.pattern_type = pattern_type
        bot_config.username_length = length
        bot_config.active_platforms = platforms
        bot_config.scan_start_time = self.start_time.isoformat()
        bot_config.save()
        
        self.bot.send_message(f"""
<b>🚀 بدء المسح المتقدم</b>
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>📏 النمط:</b> {pattern_type}
<b>📏 الطول:</b> {length}
<b>🌐 المنصات:</b> {', '.join(platforms)}
<b>🧵 الخيوط:</b> {threads}
<b>⏱️ الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
<b>⏱️ المؤقت:</b> {bot_config.scan_timer} ثانية ({'لا نهائي' if bot_config.scan_timer == 0 else f'{bot_config.scan_timer//60} دقيقة'})
<b>🔄 الاكتشاف المتسلسل:</b> {'✅ مفعل' if bot_config.sequential_mode else '❌ معطل'}
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
        """)
        
        print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}🚀 WORMGPT - المسح المتقدم{C.CYAN}          ║
{C.CYAN}╠══════════════════════════════════════════════════════╣
{C.CYAN}║  {C.YELLOW}المنصات  : {C.GREEN}{', '.join(platforms)}{C.CYAN}
{C.CYAN}║  {C.YELLOW}النمط     : {C.GREEN}{pattern_type}{C.CYAN}
{C.CYAN}║  {C.YELLOW}الطول     : {C.GREEN}{length}{C.CYAN}
{C.CYAN}║  {C.YELLOW}المسارات : {C.GREEN}{threads}{C.CYAN}
{C.CYAN}║  {C.YELLOW}المؤقت    : {C.GREEN}{bot_config.scan_timer} ثانية{C.CYAN}
{C.CYAN}║  {C.YELLOW}التسلسل   : {C.GREEN}{'مفعل' if bot_config.sequential_mode else 'معطل'}{C.CYAN}
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
        """)
        
        cycle = 0
        with ThreadPoolExecutor(max_workers=threads) as executor:
            while self.running and (max_cycles == 0 or cycle < max_cycles):
                if bot_config.scan_timer > 0:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    if elapsed >= bot_config.scan_timer:
                        logger.info(f"انتهى الوقت المحدد ({bot_config.scan_timer} ثانية)")
                        self.running = False
                        break
                cycle += 1
                usernames = self.generate_usernames(pattern_type, length)
                futures = []
                for username in usernames:
                    if not self.running:
                        break
                    futures.append(executor.submit(self.scan_single, username, platforms))
                    delay = random.uniform(0.5, 2.0)
                    time.sleep(delay)
                
                for future in as_completed(futures):
                    if not self.running:
                        break
                    results = future.result()
                    for item in results:
                        with self.lock:
                            self.found.append(item)
                            self.results.append(item)
                            self.batch_results.append(item)
                            self.platform_stats[item['platform']] += 1
                            platform_count = self.platform_stats[item['platform']]
                            print(f"{C.GREEN}[✓] @{item['username']} متاح على {item['platform']} (جودة: {item['quality']}/20) - رقم المتاح للمنصة: #{platform_count}{C.RESET}")
                            # ===== استخدم الدالة الجديدة هنا =====
                            self.bot.send_username_found(item['username'], item['platform'], item['quality'])
                            
                            if bot_config.sequential_mode:
                                sequential_usernames = self.generate_sequential_usernames(item['username'], bot_config.sequential_limit)
                                for seq_user in sequential_usernames:
                                    if not self.running:
                                        break
                                    seq_results = self.scan_single(seq_user, platforms)
                                    for seq_item in seq_results:
                                        with self.lock:
                                            self.found.append(seq_item)
                                            self.results.append(seq_item)
                                            self.batch_results.append(seq_item)
                                            self.platform_stats[seq_item['platform']] += 1
                                            seq_platform_count = self.platform_stats[seq_item['platform']]
                                            print(f"{C.GREEN}[✓] @{seq_item['username']} متاح على {seq_item['platform']} (جودة: {seq_item['quality']}/20) - رقم المتاح للمنصة: #{seq_platform_count}{C.RESET}")
                                            self.bot.send_username_found(seq_item['username'], seq_item['platform'], seq_item['quality'])
                                    time.sleep(random.uniform(0.3, 1.0))
                    
                    with self.lock:
                        self.checked += 1
                    
                    if len(self.batch_results) >= self.summary_interval:
                        self.bot.send_summary(self.batch_results)
                        self.batch_results = []
                
                print(f"\r{C.CYAN}[*] تم فحص: {self.checked} | تم العثور: {len(self.found)}{C.RESET}", end="")
        
        if self.batch_results:
            self.bot.send_summary(self.batch_results)
        
        bot_config.total_checked = self.checked
        bot_config.total_found = len(self.found)
        bot_config.scan_status = 'stopped'
        bot_config.platform_stats = dict(self.platform_stats)
        bot_config.save()
        
        print(f"\n\n{C.GREEN}[✓] انتهى المسح! تم العثور على {len(self.found)} اسم{C.RESET}")
        
        if self.found:
            json_filename = f"wormgpt_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.found, f, indent=2, ensure_ascii=False)
            print(f"{C.GREEN}[✓] تم حفظ النتائج في {json_filename}{C.RESET}")
            
            txt_filename = f"wormgpt_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(txt_filename, 'w', encoding='utf-8') as f:
                for item in self.found:
                    f.write(f"@{item['username']} ({item['platform']}) - جودة: {item['quality']}/20\n")
            print(f"{C.GREEN}[✓] تم حفظ النتائج النصية في {txt_filename}{C.RESET}")
            
            html_filename = f"wormgpt_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            self.export_html(self.found, html_filename)
            print(f"{C.GREEN}[✓] تم حفظ التقرير HTML في {html_filename}{C.RESET}")
            
            bot_config.last_report_file = json_filename
            bot_config.save()
        
        platform_summary = '\n'.join([f"  • {p}: {c}" for p, c in self.platform_stats.items()])
        self.bot.send_message(f"""
<b>✅ انتهى المسح!</b>
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
<b>📊 النتائج:</b>
• تم التحقق: {self.checked}
• تم العثور: {len(self.found)}
• المدة: {str(datetime.now() - self.start_time).split('.')[0]}
<b>📊 إحصائيات المنصات:</b>
{platform_summary}
<b>📁 الملفات:</b>
• JSON: {json_filename if self.found else 'لا يوجد'}
• TXT: {txt_filename if self.found else 'لا يوجد'}
• HTML: {html_filename if self.found else 'لا يوجد'}
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
        """)
    
    def stop_scan(self):
        self.running = False
        bot_config.scan_status = 'stopped'
        bot_config.save()
        logger.info("تم إيقاف المسح بواسطة المستخدم")

# ================================================================
# الوظائف المساعدة للواجهة
# ================================================================

def show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
{C.PURPLE}╔══════════════════════════════════════════════════════════════╗
{C.PURPLE}║{C.GOLD}██████████████████████████████████████████████████████████{C.PURPLE}║
{C.PURPLE}║{C.GOLD}██{C.WHITE}  ██╗    ██╗ ██████╗ ██████╗ ███╗   ███╗ {C.GOLD}████████{C.PURPLE}██║
{C.PURPLE}║{C.GOLD}██{C.WHITE}  ██║    ██║██╔═══██╗██╔══██╗████╗ ████║ {C.GOLD}██╔════╝{C.PURPLE}██║
{C.PURPLE}║{C.GOLD}██{C.WHITE}  ██║ █╗ ██║██║   ██║██████╔╝██╔████╔██║ {C.GOLD}█████╗  {C.PURPLE}██║
{C.PURPLE}║{C.GOLD}██{C.WHITE}  ██║███╗██║██║   ██║██╔══██╗██║╚██╔╝██║ {C.GOLD}██╔══╝  {C.PURPLE}██║
{C.PURPLE}║{C.GOLD}██{C.WHITE}  ╚███╔███╔╝╚██████╔╝██║  ██║██║ ╚═╝ ██║ {C.GOLD}████████{C.PURPLE}██║
{C.PURPLE}║{C.GOLD}██{C.WHITE}   ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ {C.GOLD}╚══════╝{C.PURPLE}██║
{C.PURPLE}║{C.GOLD}██████████████████████████████████████████████████████████{C.PURPLE}║
{C.PURPLE}║{C.GOLD}              𝖂𝕺𝕽𝕸𝕲𝕻𝕿 - 𝖀𝖑𝖙𝖎𝖒𝖆𝖙𝖊 𝕾𝖈𝖆𝖓𝖓𝖊𝖗{C.PURPLE}║
{C.PURPLE}║{C.SILVER}                   𝖛𝖊𝖗𝖘𝖎𝖔𝖓 7.0 (Black Edition){C.PURPLE}      ║
{C.PURPLE}║{C.YELLOW}                 𝕭𝖞 : @W4_M4 {C.PINK}| {C.YELLOW}𝕮𝖍 : @pytho2n{C.PURPLE}          ║
{C.PURPLE}╚══════════════════════════════════════════════════════════════╝
{C.RESET}
    """)

def show_main_menu():
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║                 {C.GOLD}🎯 القائمة الرئيسية{C.CYAN}                ║
{C.CYAN}╠══════════════════════════════════════════════════════╣
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  🔍  مسح الأسماء المتاحة
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  ⚙️  إعدادات البوت المتقدمة
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  📱  معلومات رقم هاتف
{C.CYAN}║  {C.GREEN}[4]{C.CYAN}  💬  جلب كود واتساب
{C.CYAN}║  {C.GREEN}[5]{C.CYAN}  📊  عرض النتائج المحفوظة
{C.CYAN}║  {C.GREEN}[6]{C.CYAN}  📈  تحليل الكلمات الأكثر شيوعاً
{C.CYAN}║  {C.GREEN}[7]{C.CYAN}  🛡️  إدارة القائمة السوداء
{C.CYAN}║  {C.GREEN}[8]{C.CYAN}  🔄  تحديث الإعدادات
{C.CYAN}║  {C.GREEN}[9]{C.CYAN}  🔑  إدارة توكنات المنصات
{C.CYAN}║  {C.GREEN}[0]{C.CYAN}  🚪  خروج
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)

def show_platforms_menu():
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}🌐 اختر المنصات{C.CYAN}                    ║
{C.CYAN}╠══════════════════════════════════════════════════════╣
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  Instagram    {C.PINK}[5]{C.CYAN}  Telegram    {C.BLUE}[9]{C.CYAN}  GitHub
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  Twitter      {C.PINK}[6]{C.CYAN}  YouTube     {C.BLUE}[10]{C.CYAN} Reddit
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  TikTok       {C.PINK}[7]{C.CYAN}  Snapchat    {C.BLUE}[11]{C.CYAN} Pinterest
{C.CYAN}║  {C.GREEN}[4]{C.CYAN}  Telegram     {C.PINK}[8]{C.CYAN}  Tumblr      {C.BLUE}[12]{C.CYAN} Spotify
{C.CYAN}║  {C.GREEN}[13]{C.CYAN} جميع المنصات
{C.CYAN}║  {C.GREEN}[14]{C.CYAN} اختيار مخصص
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)

def show_pattern_menu():
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}🎨 اختر نمط اليوزر{C.CYAN}                 ║
{C.CYAN}╠══════════════════════════════════════════════════════╣
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  x_x_x        {C.PINK}[4]{C.CYAN}  xx_xx
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  x_xx         {C.PINK}[5]{C.CYAN}  x_xx
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  xxx_x        {C.PINK}[6]{C.CYAN}  x_x_x_x
{C.CYAN}║  {C.GREEN}[7]{C.CYAN}  كلمة + أرقام
{C.CYAN}║  {C.GREEN}[8]{C.CYAN}  أرقام + كلمة
{C.CYAN}║  {C.GREEN}[9]{C.CYAN}  عشوائي (بدون حدود)
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)

def show_length_menu():
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}📏 اختر طول اليوزر{C.CYAN}                 ║
{C.CYAN}╠══════════════════════════════════════════════════════╣
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  3 أحرف        {C.PINK}[4]{C.CYAN}  6 أحرف
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  4 أحرف        {C.PINK}[5]{C.CYAN}  7 أحرف
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  5 أحرف        {C.PINK}[6]{C.CYAN}  8 أحرف
{C.CYAN}║  {C.GREEN}[7]{C.CYAN}  مخصص (أدخل الطول)
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)

# ================================================================
# وظائف القائمة الإضافية
# ================================================================

def phone_info():
    show_banner()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}📱 معلومات الرقم{C.CYAN}                   ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)
    phone = input(f"{C.YELLOW}[?] أدخل رقم الهاتف مع رمز الدولة: {C.GREEN}")
    try:
        if phonenumbers:
            num = phonenumbers.parse(phone)
            if phonenumbers.is_valid_number(num):
                country = geocoder.description_for_number(num, "ar")
                carrier_name = carrier.name_for_number(num, "ar")
                print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║                    {C.GOLD}النتيجة{C.CYAN}                        ║
{C.CYAN}╠══════════════════════════════════════════════════════╣
{C.CYAN}║  {C.GREEN}الدولة  : {country}
{C.CYAN}║  {C.GREEN}المشغل  : {carrier_name}
{C.CYAN}║  {C.GREEN}الرقم   : {phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
                """)
            else:
                print(f"{C.RED}[✗] رقم غير صالح{C.RESET}")
        else:
            print(f"{C.YELLOW}[!] مكتبة phonenumbers غير مثبتة{C.RESET}")
    except:
        print(f"{C.RED}[✗] خطأ في التحقق{C.RESET}")
    input(f"\n{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")

def get_whatsapp_code():
    show_banner()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}💬 كود واتساب{C.CYAN}                     ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)
    try:
        url = "https://receive-smss.com/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        numbers = [a.text.strip() for a in soup.select('a[href*="/sms/"]') if a.text.strip().startswith('+')]
        if not numbers:
            numbers = ["+13322568356", "+447931081957", "+4915210947617"]
        phone = random.choice(numbers)
        print(f"\n{C.GREEN}[✓] الرقم: {phone}{C.RESET}")
        print(f"{C.YELLOW}[!] روح سجله في الواتساب{C.RESET}")
        input(f"{C.YELLOW}[!] اضغط Enter للحصول على الكود...{C.RESET}")
        code = None
        for _ in range(10):
            try:
                code_url = f"https://receive-smss.com/sms/{re.sub(r'\D', '', phone)}/"
                r = requests.get(code_url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.text, 'html.parser')
                for text in soup.find_all(text=re.compile(r'whatsapp', re.I)):
                    match = re.search(r'\b(\d{3})\s?(\d{3})\b', text) or re.search(r'\b(\d{6})\b', text)
                    if match:
                        code = match.group(1) + match.group(2) if len(match.groups()) == 2 else match.group(1)
                        break
                if code:
                    break
                time.sleep(5)
            except:
                time.sleep(5)
        if code:
            print(f"\n{C.GREEN}[✓] الكود: {code}{C.RESET}")
        else:
            print(f"\n{C.RED}[✗] لم يتم العثور على كود{C.RESET}")
    except Exception as e:
        print(f"{C.RED}[✗] خطأ: {e}{C.RESET}")
    input(f"\n{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")

def show_saved_results():
    show_banner()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}📊 النتائج المحفوظة{C.CYAN}                ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)
    files = [f for f in os.listdir('.') if f.startswith('wormgpt_results_') and f.endswith('.json')]
    if not files:
        print(f"{C.YELLOW}[!] لا توجد نتائج محفوظة{C.RESET}")
        input(f"{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")
        return
    print(f"{C.CYAN}الملفات المتاحة:{C.RESET}")
    for i, f in enumerate(files, 1):
        size = os.path.getsize(f)
        print(f"  {C.GREEN}[{i}]{C.CYAN} {f} ({size/1024:.1f} KB){C.RESET}")
    try:
        choice = int(input(f"{C.YELLOW}[?] اختر ملفاً لعرضه (0 للخروج): {C.GREEN}"))
        if choice == 0:
            return
        if 1 <= choice <= len(files):
            filename = files[choice-1]
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            platform_summary = Counter(item['platform'] for item in data)
            print(f"\n{C.CYAN}╔══════════════════════════════════════════════════════╗")
            print(f"{C.CYAN}║                    {C.GOLD}النتائج{C.CYAN}                        ║")
            print(f"{C.CYAN}╠══════════════════════════════════════════════════════╣")
            print(f"{C.CYAN}║  {C.YELLOW}إجمالي المتاحات: {len(data)}{C.CYAN}")
            print(f"{C.CYAN}║  {C.YELLOW}إحصائيات المنصات:{C.CYAN}")
            for p, c in platform_summary.items():
                print(f"{C.CYAN}║    {C.GREEN}{p}: {c}{C.CYAN}")
            print(f"{C.CYAN}╠══════════════════════════════════════════════════════╣")
            for i, item in enumerate(data[:20], 1):
                print(f"{C.CYAN}║  {C.GREEN}{i}. @{item['username']} ({item['platform']}) - جودة: {item['quality']}/20{C.CYAN}")
            if len(data) > 20:
                print(f"{C.CYAN}║  ... وعرض {len(data)-20} اسم آخر{C.CYAN}")
            print(f"{C.CYAN}╚══════════════════════════════════════════════════════╝")
    except:
        pass
    input(f"\n{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")

def analyze_common_words():
    show_banner()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}📈 تحليل الكلمات{C.CYAN}                   ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)
    files = [f for f in os.listdir('.') if f.startswith('wormgpt_results_') and f.endswith('.json')]
    if not files:
        print(f"{C.YELLOW}[!] لا توجد نتائج للتحليل{C.RESET}")
        input(f"{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")
        return
    print(f"{C.CYAN}الملفات المتاحة:{C.RESET}")
    for i, f in enumerate(files, 1):
        size = os.path.getsize(f)
        print(f"  {C.GREEN}[{i}]{C.CYAN} {f} ({size/1024:.1f} KB){C.RESET}")
    try:
        choice = int(input(f"{C.YELLOW}[?] اختر ملفاً للتحليل (0 للخروج): {C.GREEN}"))
        if choice == 0:
            return
        if 1 <= choice <= len(files):
            filename = files[choice-1]
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            usernames = [item['username'] for item in data]
            words = []
            for username in usernames:
                parts = username.split('_')
                words.extend(parts)
            counter = Counter(words)
            print(f"\n{C.CYAN}╔══════════════════════════════════════════════════════╗")
            print(f"{C.CYAN}║                    {C.GOLD}تحليل الكلمات{C.CYAN}                  ║")
            print(f"{C.CYAN}╠══════════════════════════════════════════════════════╣")
            print(f"{C.CYAN}║  {C.YELLOW}إجمالي الأسماء: {len(usernames)}{C.CYAN}")
            print(f"{C.CYAN}║  {C.YELLOW}إجمالي الكلمات: {len(words)}{C.CYAN}")
            print(f"{C.CYAN}╠══════════════════════════════════════════════════════╣")
            for word, count in counter.most_common(10):
                print(f"{C.CYAN}║  {C.GREEN}{word}: {count} مرة{C.CYAN}")
            print(f"{C.CYAN}╚══════════════════════════════════════════════════════╝")
    except:
        pass
    input(f"\n{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")

def manage_blacklist():
    show_banner()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}🛡️ إدارة القائمة السوداء{C.CYAN}            ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)
    while True:
        print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  عرض القائمة
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  إضافة كلمة
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  حذف كلمة
{C.CYAN}║  {C.GREEN}[4]{C.CYAN}  تفريغ القائمة
{C.CYAN}║  {C.GREEN}[0]{C.CYAN}  العودة
{C.CYAN}╚══════════════════════════════════════════════════════╝
        """)
        choice = input(f"{C.YELLOW}[?] اختر: {C.GREEN}").strip()
        if choice == '1':
            if not bot_config.blacklist:
                print(f"{C.YELLOW}📋 القائمة السوداء فارغة{C.RESET}")
            else:
                print(f"{C.GREEN}📋 القائمة السوداء:{C.RESET}")
                for i, word in enumerate(bot_config.blacklist, 1):
                    print(f"  {i}. {word}")
        elif choice == '2':
            word = input(f"{C.YELLOW}أدخل الكلمة الممنوعة: {C.GREEN}").strip().lower()
            if word:
                if word not in bot_config.blacklist:
                    bot_config.blacklist.append(word)
                    bot_config.save()
                    print(f"{C.GREEN}[✓] تم إضافة '{word}'{C.RESET}")
                else:
                    print(f"{C.YELLOW}[!] '{word}' موجود بالفعل{C.RESET}")
            else:
                print(f"{C.RED}[✗] الكلمة غير صالحة{C.RESET}")
        elif choice == '3':
            if not bot_config.blacklist:
                print(f"{C.YELLOW}📋 القائمة السوداء فارغة{C.RESET}")
            else:
                for i, word in enumerate(bot_config.blacklist, 1):
                    print(f"  {i}. {word}")
                try:
                    idx = int(input(f"{C.YELLOW}رقم الكلمة للحذف: {C.GREEN}")) - 1
                    if 0 <= idx < len(bot_config.blacklist):
                        removed = bot_config.blacklist.pop(idx)
                        bot_config.save()
                        print(f"{C.GREEN}[✓] تم حذف '{removed}'{C.RESET}")
                    else:
                        print(f"{C.RED}[✗] رقم غير صحيح{C.RESET}")
                except:
                    print(f"{C.RED}[✗] أدخل رقماً صحيحاً{C.RESET}")
        elif choice == '4':
            confirm = input(f"{C.RED}هل أنت متأكد من تفريغ القائمة؟ (y/n): {C.GREEN}")
            if confirm.lower() == 'y':
                bot_config.blacklist = []
                bot_config.save()
                print(f"{C.GREEN}[✓] تم تفريغ القائمة{C.RESET}")
        elif choice == '0':
            break
        time.sleep(1)

def export_results():
    show_banner()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}📤 تصدير النتائج{C.CYAN}                  ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)
    files = [f for f in os.listdir('.') if f.startswith('wormgpt_results_') and f.endswith('.json')]
    if not files:
        print(f"{C.YELLOW}[!] لا توجد نتائج للتصدير{C.RESET}")
        input(f"{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")
        return
    print(f"{C.CYAN}الملفات المتاحة:{C.RESET}")
    for i, f in enumerate(files, 1):
        size = os.path.getsize(f)
        print(f"  {C.GREEN}[{i}]{C.CYAN} {f} ({size/1024:.1f} KB){C.RESET}")
    try:
        choice = int(input(f"{C.YELLOW}[?] اختر ملفاً للتصدير (0 للخروج): {C.GREEN}"))
        if choice == 0:
            return
        if 1 <= choice <= len(files):
            filename = files[choice-1]
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            csv_filename = filename.replace('.json', '.csv')
            with open(csv_filename, 'w', encoding='utf-8') as f:
                f.write("Username,Platform,Quality,Timestamp\n")
                for item in data:
                    f.write(f"{item['username']},{item['platform']},{item['quality']},{item['timestamp']}\n")
            print(f"{C.GREEN}[✓] تم تصدير النتائج إلى {csv_filename}{C.RESET}")
    except:
        pass
    input(f"\n{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")

def manage_platform_tokens():
    show_banner()
    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}🔑 إدارة توكنات المنصات{C.CYAN}            ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
    """)
    while True:
        print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  عرض التوكنات الحالية
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  إضافة توكن لمنصة
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  حذف توكن منصة
{C.CYAN}║  {C.GREEN}[4]{C.CYAN}  تفعيل/تعطيل الاكتشاف المتسلسل
{C.CYAN}║  {C.GREEN}[5]{C.CYAN}  تعيين حد الاكتشاف المتسلسل
{C.CYAN}║  {C.GREEN}[0]{C.CYAN}  العودة
{C.CYAN}╚══════════════════════════════════════════════════════╝
        """)
        choice = input(f"{C.YELLOW}[?] اختر: {C.GREEN}").strip()
        if choice == '1':
            if not bot_config.platform_tokens:
                print(f"{C.YELLOW}📋 لا توجد توكنات مخصصة للمنصات{C.RESET}")
            else:
                print(f"{C.GREEN}📋 توكنات المنصات:{C.RESET}")
                for platform, data in bot_config.platform_tokens.items():
                    print(f"  • {platform}: 🆔 {data['chat_id'][:10]}...")
        elif choice == '2':
            platform = input(f"{C.YELLOW}أدخل اسم المنصة (مثل Instagram): {C.GREEN}").strip()
            token = input(f"{C.YELLOW}🔑 توكن البوت: {C.GREEN}").strip()
            chat_id = input(f"{C.YELLOW}🆔 معرف الشات: {C.GREEN}").strip()
            if platform and token and chat_id:
                try:
                    url = f"https://api.telegram.org/bot{token}/getMe"
                    r = requests.get(url, timeout=5)
                    if r.status_code == 200:
                        bot_config.platform_tokens[platform] = {'token': token, 'chat_id': chat_id}
                        bot_config.save()
                        print(f"{C.GREEN}[✓] تم إضافة توكن لمنصة {platform}{C.RESET}")
                    else:
                        print(f"{C.RED}[✗] فشل الاتصال بالبوت{C.RESET}")
                except:
                    print(f"{C.RED}[✗] خطأ في الاتصال{C.RESET}")
            else:
                print(f"{C.RED}[✗] جميع الحقول مطلوبة{C.RESET}")
        elif choice == '3':
            if not bot_config.platform_tokens:
                print(f"{C.YELLOW}📋 لا توجد توكنات للحذف{C.RESET}")
            else:
                platforms = list(bot_config.platform_tokens.keys())
                for i, p in enumerate(platforms, 1):
                    print(f"  {i}. {p}")
                try:
                    idx = int(input(f"{C.YELLOW}رقم المنصة للحذف: {C.GREEN}")) - 1
                    if 0 <= idx < len(platforms):
                        removed = platforms[idx]
                        del bot_config.platform_tokens[removed]
                        bot_config.save()
                        print(f"{C.GREEN}[✓] تم حذف توكن منصة {removed}{C.RESET}")
                    else:
                        print(f"{C.RED}[✗] رقم غير صحيح{C.RESET}")
                except:
                    print(f"{C.RED}[✗] أدخل رقماً صحيحاً{C.RESET}")
        elif choice == '4':
            bot_config.sequential_mode = not bot_config.sequential_mode
            bot_config.save()
            print(f"{C.GREEN}[✓] تم {'تفعيل' if bot_config.sequential_mode else 'تعطيل'} الاكتشاف المتسلسل{C.RESET}")
        elif choice == '5':
            try:
                limit = int(input(f"{C.YELLOW}أدخل حد الاكتشاف المتسلسل (عدد المشتقات): {C.GREEN}"))
                if limit > 0:
                    bot_config.sequential_limit = limit
                    bot_config.save()
                    print(f"{C.GREEN}[✓] تم تعيين الحد إلى {limit}{C.RESET}")
                else:
                    print(f"{C.RED}[✗] يجب أن يكون الرقم أكبر من 0{C.RESET}")
            except:
                print(f"{C.RED}[✗] أدخل رقماً صحيحاً{C.RESET}")
        elif choice == '0':
            break
        input(f"\n{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")

# ================================================================
# تشغيل البوت في الخلفية (مع معالجة الأخطاء المتسلسلة)
# ================================================================

def run_bot_polling():
    """تشغيل البوت باستخدام Polling مع تجاهل الأخطاء المؤقتة"""
    if not bot_config.enabled:
        return
    offset = 0
    bot = WormBot()
    consecutive_failures = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{bot_config.token}/getUpdates"
            r = requests.get(url, params={'offset': offset, 'timeout': 30}, timeout=35)
            
            if r.status_code == 200:
                consecutive_failures = 0
                data = r.json()
                if data.get('ok'):
                    for update in data.get('result', []):
                        offset = update['update_id'] + 1
                        if 'message' in update:
                            msg = update['message']
                            text = msg.get('text', '')
                            if text.startswith('/'):
                                parts = text.split()
                                command = parts[0]
                                args = parts[1:]
                                response = bot.handle_command(command, args)
                                chat_id = msg.get('chat', {}).get('id')
                                if chat_id:
                                    try:
                                        send_url = f"https://api.telegram.org/bot{bot_config.token}/sendMessage"
                                        send_data = {'chat_id': chat_id, 'text': response, 'parse_mode': 'HTML'}
                                        requests.post(send_url, data=send_data, timeout=10)
                                    except:
                                        pass
            else:
                consecutive_failures += 1
                logger.warning(f"فشل الاتصال بالبوت (المحاولة {consecutive_failures})")
                
            if consecutive_failures >= 5:
                logger.warning("توقف مؤقت لمدة 30 ثانية بسبب فشل متكرر")
                time.sleep(30)
                consecutive_failures = 0
            else:
                time.sleep(1)
                
        except requests.exceptions.ConnectionError:
            consecutive_failures += 1
            logger.warning(f"خطأ اتصال (المحاولة {consecutive_failures})")
            time.sleep(5)
        except requests.exceptions.Timeout:
            consecutive_failures += 1
            logger.warning(f"انتهاء المهلة (المحاولة {consecutive_failures})")
            time.sleep(5)
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"خطأ غير متوقع: {str(e)[:60]}")
            time.sleep(5)

# ================================================================
# الوظيفة الرئيسية
# ================================================================

def main():
    global bot_config
    bot_config.load()
    setup_bot_config()
    scanner = UsernameScanner()
    if bot_config.enabled:
        bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
        bot_thread.start()
        logger.success("تم تشغيل البوت في الخلفية")
    while True:
        show_banner()
        show_main_menu()
        choice = input(f"{C.YELLOW}[?] اختر رقم: {C.GREEN}").strip()
        if choice == '1':
            show_banner()
            show_platforms_menu()
            platform_choice = input(f"{C.YELLOW}[?] اختر المنصة: {C.GREEN}").strip()
            platform_map = {
                '1': ['Instagram'],
                '2': ['Twitter'],
                '3': ['TikTok'],
                '4': ['Telegram'],
                '5': ['YouTube'],
                '6': ['Snapchat'],
                '7': ['Tumblr'],
                '8': ['GitHub'],
                '9': ['Reddit'],
                '10': ['Pinterest'],
                '11': ['Spotify'],
                '12': ['Instagram', 'Twitter', 'TikTok', 'Telegram', 'YouTube', 'Snapchat', 'Tumblr', 'GitHub', 'Reddit', 'Pinterest', 'Spotify'],
                '13': None
            }
            if platform_choice == '0':
                continue
            if platform_choice not in platform_map:
                print(f"{C.RED}[✗] اختيار غير صحيح{C.RESET}")
                time.sleep(1)
                continue
            platforms = platform_map[platform_choice]
            if platforms is None:
                print(f"{C.YELLOW}أدخل المنصات مفصولة بفاصلة (Instagram,Twitter,TikTok): {C.RESET}")
                custom = input(f"{C.CYAN}▶ {C.GREEN}").strip()
                platforms = [p.strip() for p in custom.split(',') if p.strip()]
                if not platforms:
                    platforms = ['Instagram', 'Twitter', 'TikTok', 'Telegram', 'YouTube']
            show_banner()
            show_pattern_menu()
            pattern_choice = input(f"{C.YELLOW}[?] اختر النمط: {C.GREEN}").strip()
            if pattern_choice not in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                print(f"{C.RED}[✗] اختيار غير صحيح{C.RESET}")
                time.sleep(1)
                continue
            pattern_type = int(pattern_choice)
            length = 4
            if pattern_type in [1, 2, 3, 4, 5, 6]:
                show_banner()
                show_length_menu()
                length_choice = input(f"{C.YELLOW}[?] اختر الطول: {C.GREEN}").strip()
                length_map = {'1': 3, '2': 4, '3': 5, '4': 6, '5': 7, '6': 8}
                if length_choice == '7':
                    try:
                        length = int(input(f"{C.YELLOW}أدخل الطول المطلوب: {C.GREEN}"))
                        if length < 3 or length > 20:
                            print(f"{C.RED}[✗] الطول يجب أن بين 3 و 20{C.RESET}")
                            time.sleep(1)
                            continue
                    except:
                        print(f"{C.RED}[✗] أدخل رقماً صحيحاً{C.RESET}")
                        time.sleep(1)
                        continue
                else:
                    length = length_map.get(length_choice, 4)
            elif pattern_type in [7, 8]:
                try:
                    length = int(input(f"{C.YELLOW}أدخل الطول المطلوب (4-10): {C.GREEN}"))
                    if length < 4 or length > 10:
                        print(f"{C.RED}[✗] الطول يجب أن بين 4 و 10{C.RESET}")
                        time.sleep(1)
                        continue
                except:
                    print(f"{C.RED}[✗] أدخل رقماً صحيحاً{C.RESET}")
                    time.sleep(1)
                    continue
            else:
                try:
                    length = int(input(f"{C.YELLOW}أدخل الطول المطلوب (3-15): {C.GREEN}"))
                    if length < 3 or length > 15:
                        print(f"{C.RED}[✗] الطول يجب أن بين 3 و 15{C.RESET}")
                        time.sleep(1)
                        continue
                except:
                    print(f"{C.RED}[✗] أدخل رقماً صحيحاً{C.RESET}")
                    time.sleep(1)
                    continue
            try:
                threads = int(input(f"{C.YELLOW}[?] عدد الخيوط (1-50, افتراضي 20): {C.GREEN}") or 20)
                threads = max(1, min(threads, 50))
            except:
                threads = 20
            try:
                cycles = int(input(f"{C.YELLOW}[?] عدد الدورات (0 = لا نهائي, افتراضي 0): {C.GREEN}") or 0)
                cycles = max(0, cycles)
            except:
                cycles = 0
            scanner.advanced_scan(pattern_type, length, platforms, threads, cycles)
            input(f"\n{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")
        elif choice == '2':
            show_banner()
            print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║              {C.GOLD}⚙️ إعدادات البوت{C.CYAN}                   ║
{C.CYAN}╚══════════════════════════════════════════════════════╝
{C.RESET}
            """)
            print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  📝 إدخال توكن البوت الرئيسي ومعرف الشات
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  🔄 تفعيل/تعطيل البوت
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  👁️ عرض الإعدادات الحالية
{C.CYAN}║  {C.GREEN}[4]{C.CYAN}  🤖 إدارة البوتات الاحتياطية
{C.CYAN}║  {C.GREEN}[5]{C.CYAN}  🌐 إدارة البروكسيات
{C.CYAN}║  {C.GREEN}[6]{C.CYAN}  🧪 اختبار البوت
{C.CYAN}║  {C.GREEN}[0]{C.CYAN}  🔙 العودة
{C.CYAN}╚══════════════════════════════════════════════════════╝
            """)
            settings_choice = input(f"{C.YELLOW}[?] اختر: {C.GREEN}").strip()
            if settings_choice == '1':
                token = input(f"{C.YELLOW}🔑 توكن البوت الرئيسي: {C.GREEN}").strip()
                chat_id = input(f"{C.YELLOW}🆔 معرف الشات الرئيسي: {C.GREEN}").strip()
                if token and chat_id:
                    bot_config.token = token
                    bot_config.chat_id = chat_id
                    bot_config.enabled = True
                    bot_config.save()
                    logger.success("تم حفظ إعدادات البوت الرئيسي")
                else:
                    logger.error("التوكن والمعرف مطلوبين")
                time.sleep(1)
            elif settings_choice == '2':
                bot_config.enabled = not bot_config.enabled
                bot_config.save()
                logger.success(f"تم {'تفعيل' if bot_config.enabled else 'تعطيل'} البوت")
                time.sleep(1)
            elif settings_choice == '3':
                bot = WormBot()
                print(bot.cmd_settings([]))
                input(f"{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")
            elif settings_choice == '4':
                while True:
                    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  عرض البوتات الاحتياطية
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  إضافة بوت احتياطي
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  حذف بوت احتياطي
{C.CYAN}║  {C.GREEN}[0]{C.CYAN}  العودة
{C.CYAN}╚══════════════════════════════════════════════════════╝
                    """)
                    sub_choice = input(f"{C.YELLOW}[?] اختر: {C.GREEN}").strip()
                    if sub_choice == '1':
                        bot = WormBot()
                        print(bot.cmd_list_bots([]))
                    elif sub_choice == '2':
                        token = input(f"{C.YELLOW}🔑 توكن البوت الاحتياطي: {C.GREEN}").strip()
                        chat_id = input(f"{C.YELLOW}🆔 معرف الشات الاحتياطي: {C.GREEN}").strip()
                        if token and chat_id:
                            bot_config.backup_bots.append({'token': token, 'chat_id': chat_id})
                            bot_config.save()
                            logger.success("تم إضافة البوت الاحتياطي")
                        else:
                            logger.error("التوكن والمعرف مطلوبين")
                    elif sub_choice == '3':
                        if bot_config.backup_bots:
                            for i, b in enumerate(bot_config.backup_bots, 1):
                                print(f"{i}. {b['chat_id']}")
                            try:
                                idx = int(input(f"{C.YELLOW}رقم البوت للحذف: {C.GREEN}")) - 1
                                if 0 <= idx < len(bot_config.backup_bots):
                                    bot_config.backup_bots.pop(idx)
                                    bot_config.save()
                                    logger.success("تم حذف البوت الاحتياطي")
                            except:
                                logger.error("رقم غير صحيح")
                        else:
                            logger.warning("لا توجد بوتات احتياطية")
                    elif sub_choice == '0':
                        break
                    input(f"{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")
            elif settings_choice == '5':
                while True:
                    print(f"""
{C.CYAN}╔══════════════════════════════════════════════════════╗
{C.CYAN}║  {C.GREEN}[1]{C.CYAN}  عرض البروكسيات
{C.CYAN}║  {C.GREEN}[2]{C.CYAN}  إضافة بروكسي
{C.CYAN}║  {C.GREEN}[3]{C.CYAN}  حذف بروكسي
{C.CYAN}║  {C.GREEN}[4]{C.CYAN}  تفعيل/تعطيل البروكسيات
{C.CYAN}║  {C.GREEN}[0]{C.CYAN}  العودة
{C.CYAN}╚══════════════════════════════════════════════════════╝
                    """)
                    sub_choice = input(f"{C.YELLOW}[?] اختر: {C.GREEN}").strip()
                    if sub_choice == '1':
                        if bot_config.proxies:
                            for i, p in enumerate(bot_config.proxies, 1):
                                print(f"{i}. {p}")
                        else:
                            logger.warning("لا توجد بروكسيات")
                    elif sub_choice == '2':
                        proxy = input(f"{C.YELLOW}أدخل البروكسي (http://ip:port): {C.GREEN}").strip()
                        if proxy:
                            bot_config.proxies.append(proxy)
                            bot_config.save()
                            logger.success("تم إضافة البروكسي")
                        else:
                            logger.error("بروكسي غير صالح")
                    elif sub_choice == '3':
                        if bot_config.proxies:
                            for i, p in enumerate(bot_config.proxies, 1):
                                print(f"{i}. {p}")
                            try:
                                idx = int(input(f"{C.YELLOW}رقم البروكسي للحذف: {C.GREEN}")) - 1
                                if 0 <= idx < len(bot_config.proxies):
                                    bot_config.proxies.pop(idx)
                                    bot_config.save()
                                    logger.success("تم حذف البروكسي")
                            except:
                                logger.error("رقم غير صحيح")
                        else:
                            logger.warning("لا توجد بروكسيات")
                    elif sub_choice == '4':
                        bot_config.use_proxy = not bot_config.use_proxy
                        bot_config.save()
                        logger.success(f"تم {'تفعيل' if bot_config.use_proxy else 'تعطيل'} البروكسيات")
                    elif sub_choice == '0':
                        break
                    input(f"{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")
            elif settings_choice == '6':
                bot = WormBot()
                if bot.send_message("🧪 <b>اختبار البوت</b>\n\n✅ تم الاتصال بنجاح!"):
                    logger.success("تم إرسال رسالة اختبار")
                else:
                    logger.error("فشل إرسال رسالة الاختبار")
                input(f"{C.YELLOW}[!] اضغط Enter للمتابعة...{C.RESET}")
            elif settings_choice == '0':
                continue
        elif choice == '3':
            phone_info()
        elif choice == '4':
            get_whatsapp_code()
        elif choice == '5':
            show_saved_results()
        elif choice == '6':
            analyze_common_words()
        elif choice == '7':
            manage_blacklist()
        elif choice == '8':
            export_results()
        elif choice == '9':
            manage_platform_tokens()
        elif choice == '0':
            print(f"\n{C.GREEN}[✓] مع السلامة!{C.RESET}")
            break
        else:
            print(f"{C.RED}[✗] اختيار غير صحيح{C.RESET}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C.GREEN}[✓] تم الإيقاف بواسطتك{C.RESET}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        time.sleep(3)