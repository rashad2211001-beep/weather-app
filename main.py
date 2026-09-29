
import subprocess
import sys
import os

REQUIRED_LIBRARIES = [
    ("telegram", "python-telegram-bot[job-queue]>=20,<23"),
    ("psutil", "psutil>=5.9.0"),
    ("flask", "Flask>=2.2.0"),
]

def _telegram_package_ok() -> bool:
    try:
        import telegram
        from telegram import Update, Chat
        from telegram.ext import Application, filters
        return bool(getattr(telegram, "__version__", "")) and Update is not None and Chat is not None
    except Exception:
        return False

def install_missing_libraries():
    print("📦 جاري التحقق من المكتبات المطلوبة...")
    installed, failed = [], []

    for import_name, pip_spec in REQUIRED_LIBRARIES:
        lib_name = pip_spec.split(">=")[0].split("==")[0].split("[")[0]
        if import_name == "telegram":
            ok = _telegram_package_ok()
        else:
            try:
                __import__(import_name)
                ok = True
            except Exception:
                ok = False

        if ok:
            print(f"   ✅ {lib_name} — مثبتة وسليمة")
            installed.append(lib_name)
            continue

        print(f"   ⏳ {lib_name} — جاري الإصلاح/التثبيت...")
        try:
            if import_name == "telegram":
                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", "telegram"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                )
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall",
                 "--no-cache-dir", pip_spec],
                timeout=600,
            )
            if import_name == "telegram" and not _telegram_package_ok():
                raise RuntimeError("اختبار telegram.Update/Chat فشل بعد التثبيت")
            print(f"   ✅ {lib_name} — تم الإصلاح بنجاح")
            installed.append(lib_name)
        except Exception as e:
            print(f"   ❌ {lib_name} — فشل التثبيت: {e}")
            failed.append(lib_name)

    if failed:
        print(f"⚠️ فشل تثبيت: {', '.join(failed)}")
        raise SystemExit(1)
    print("✅ جميع المكتبات الأساسية جاهزة.")
    return installed, failed

INSTALLED, FAILED = install_missing_libraries()
print("🚀 بدء تشغيل البوت...\n")

# ═══════════════════════════════════════════════════════════════════════════════
# 📦  الاستيرادات
# ═══════════════════════════════════════════════════════════════════════════════
import os, re, io, sys, ast, json, time, math, uuid, html, base64, shutil
import signal, random, hashlib, zipfile, asyncio, logging, platform, tempfile
import threading, subprocess, traceback, urllib.parse, copy, struct, shlex
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any, Tuple, Set, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import wraps, lru_cache
from collections import defaultdict, Counter, deque
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup as TelegramInlineKeyboardMarkup,
    InputFile, BotCommand, BotCommandScopeDefault,
    ChatMember, LabeledPrice, ReplyKeyboardRemove, Message, Chat,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
    PreCheckoutQueryHandler, JobQueue,
)
from telegram.constants import ParseMode, ChatAction, ChatMemberStatus
from telegram.error import TelegramError, BadRequest, Forbidden, Conflict

# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️  الإعدادات الأساسية
# ═══════════════════════════════════════════════════════════════════════════════

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8245634624:AAE3sVyg_ynNcLoUxjgznpmJCtu5k9jaOPE").strip()

_admin_env = os.getenv("ADMIN_IDS", "8868615222")
ADMIN_IDS: List[int] = []
for _x in _admin_env.split(","):
    _x = _x.strip()
    if _x.lstrip("-").isdigit():
        ADMIN_IDS.append(int(_x))
if not ADMIN_IDS:
    ADMIN_IDS = [8868615222]

DEFAULT_STARS_PER_10_POINTS: int = 15

DEVELOPER_USERNAME: str = "A_b_d_TbA"
DEVELOPER_LINK: str = f"https://t.me/{DEVELOPER_USERNAME}"

# ═══════════════════════════════════════════════════════════════════════════════
# 🆔  معرف فريد لكل نسخة
# ═══════════════════════════════════════════════════════════════════════════════

def get_instance_id() -> str:
    port = os.getenv("PORT", "")
    if port and port.isdigit():
        return f"port_{port}"
    return f"pid_{os.getpid()}"

INSTANCE_ID = get_instance_id()
print(f"🆔 معرف هذه النسخة: {INSTANCE_ID}")

DATABASE_FILE: str = os.getenv("DATABASE_FILE", f"bot_database_{INSTANCE_ID}.json")
FILES_DIR: str   = os.getenv("FILES_DIR",   f"hosted_files_{INSTANCE_ID}")
LOGS_DIR: str    = os.getenv("LOGS_DIR",    f"bot_logs_{INSTANCE_ID}")
BACKUP_DIR: str  = os.getenv("BACKUP_DIR",  f"backups_{INSTANCE_ID}")
TEMP_DIR: str    = os.getenv("TEMP_DIR",    f"temp_work_{INSTANCE_ID}")

MAX_FILE_SIZE_MB: int        = int(os.getenv("MAX_FILE_SIZE_MB",        "50"))
MAX_PROCESSES_PER_USER: int  = int(os.getenv("MAX_PROCESSES_PER_USER",  "3"))
RUN_TIMEOUT_SECONDS: int     = int(os.getenv("RUN_TIMEOUT_SECONDS",     "0"))
INSTALL_TIMEOUT_SECONDS: int = int(os.getenv("INSTALL_TIMEOUT_SECONDS", "600"))
RATE_LIMIT_MESSAGES: int     = int(os.getenv("RATE_LIMIT_MESSAGES",     "10"))
RATE_LIMIT_WINDOW: int       = int(os.getenv("RATE_LIMIT_WINDOW",       "10"))

BOT_VERSION: str      = "7.0.0-AI-SHIELD"
BOT_NAME: str         = f"PyHost Pro Ultra [{INSTANCE_ID}]"
SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "A_b_d_Tb")
PAYMENT_PROVIDER_TOKEN: str = ""

for _d in (FILES_DIR, LOGS_DIR, BACKUP_DIR, TEMP_DIR):
    os.makedirs(_d, exist_ok=True)

STICKERS: Dict[str, str] = {
    "upload_success":   "",
    "login_success":    "CAACAgQAAxkBAxvcqmoHqBAYg1w5e-KMgCVC-Lh8WK_uAAIWAANf_gYhgW1qULu_b787BA",
    "hosting_started":  "",
    "installing_libs":  "AAMCBAADGQEDG92sageqByBwwcqhgeL2o9qY_Ej1AT8AAhoGAAItglRSvVvA4nVI0vcBAAdtAAM7BA",
    "share_link":       "",
    "points_added":     "",
    "security_blocked": "",
    "support_error":    "",
    "admin_action":     "",
    "subscription_ok":  "AAMCBAADGQEDHEtaaghlSir59abfiRa7xzqQzphFgOkAAvECAAKMI1xTvn9SAAGq3m0oAQAHbQADOwQ",
    "premium_granted":  "",
    "leaderboard":      "",
    "new_user":         "",
    "ai_analysis":      "",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 📝  السجلات
# ═══════════════════════════════════════════════════════════════════════════════
_log_path = os.path.join(LOGS_DIR, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_log_path, encoding="utf-8"),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(f"PyHostBot_{INSTANCE_ID}")

logger.info("🚀 بدء تشغيل النسخة %s", INSTANCE_ID)
logger.info("📂 قاعدة البيانات: %s", DATABASE_FILE)
logger.info("📂 مجلد الملفات: %s", FILES_DIR)
logger.info("👑 المطور: @%s", DEVELOPER_USERNAME)

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨  الأيقونات
# ═══════════════════════════════════════════════════════════════════════════════
class Icon:
    BOT="🤖"; FIRE="🔥"; STAR="⭐"; DIAMOND="💎"; ROCKET="🚀"
    LOCK="🔒"; UNLOCK="🔓"; KEY="🔑"; CHECK="✅"; CROSS="❌"
    WARN="⚠️"; INFO="ℹ️"; GIFT="🎁"; CROWN="👑"; USER="👤"
    USERS="👥"; SETTINGS="⚙️"; STATS="📊"; FILE="📄"; FOLDER="📁"
    UPLOAD="📤"; DOWNLOAD="📥"; PLAY="▶️"; STOP="⏹"; RESTART="🔄"
    DELETE="🗑"; EDIT="✏️"; SEARCH="🔍"; BELL="🔔"; BROADCAST="📢"
    LINK="🔗"; BACK="⬅️"; NEXT="➡️"; PREV="◀️"; HOME="🏠"
    SUPPORT="💬"; HEART="❤️"; CHANNEL="📣"; PIN="📌"; CLOCK="⏰"
    NOTE="📝"; TASK="✔️"; TOOLS="🛠"; LIGHT="💡"; SHIELD="🛡"
    BAN="🚫"; UNBAN="🟢"; CODE="💻"; TERMINAL="📺"; INBOX="📬"
    PLUS="➕"; MINUS="➖"; LIST="📋"; REFRESH="🔁"; CHART="📈"
    TROPHY="🏆"; MEDAL="🥇"; PREMIUM="💫"; SERVER="🖥"; MEMORY="🧠"
    CPU="⚡"; DISK="💽"; NETWORK="🌐"; TIMER="⏱"; CALENDAR="📅"
    ALERT="🚨"; SUCCESS="🟢"; PRIMARY="🔵"; DANGER="🔴"; WARNING="🟡"
    FLASH="⚡"; MAGIC="✨"; POWER="💪"; FAST="🚀"; NEW="🆕"
    ZIP="🗜"; LOG="📋"; EXPORT="📤"; IMPORT="📥"; COPY="📋"
    TAG="🏷"; CATEGORY="📂"; WORLD="🌍"; PUBLIC="🌐"; PRIVATE="🔏"
    AI="🧠"; ANALYZE="🔬"; SCAN="🔭"; QUALITY="⭐"; BUG="🐛"
    API_PROTECT="🔐"; TOKEN_SAFE="🛡"; CLEAN="✨"; RISK="⚠️"
    APPROVAL="✅"; REJECT="❌"; PENDING="⏳"; REVIEW="📋"

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨  نظام أزرار Inline Keyboard المحترف — style ملزم على كل زر
# ═══════════════════════════════════════════════════════════════════════════════

BUTTON_STYLES = ("success", "primary", "danger")

_DANGER_HINTS = (
    "حذف", "إيقاف", "ايقاف", "حظر", "إلغاء", "الغاء", "خصم", "محظور",
    "خطر", "إزالة", "مسح", "رفض", "stop", "del", "delete", "ban", "remove",
    "cancel", "danger", "kill", "block", "bwords", "stop_all",
)
_SUCCESS_HINTS = (
    "تشغيل", "تفعيل", "تأكيد", "نعم", "إضافة", "اضافة", "رفع", "شراء",
    "دعوة", "ادع", "تحققت", "نسخة احتياطية", "مشاركة", "استرداد", "حفظ",
    "قبول", "منح", "فك الحظر", "run", "play", "add", "buy", "invite", "backup",
    "share", "confirm", "redeem", "save", "unban", "upload", "grant", "تحليل",
    "موافقة", "approve",
)
_PRIMARY_HINTS = (
    "رجوع", "الرئيسية", "القائمة", "لوحة", "تفاصيل", "معلومات", "إحصائيات",
    "احصائيات", "الملفات", "ملفاتي", "الإعدادات", "الاعدادات", "الدعم",
    "السجل", "تحديث", "بحث", "عرض", "تحميل", "التالي", "السابق", "page",
    "menu", "stats", "settings", "support", "log", "refresh", "search", "open",
    "download", "files", "user", "info", "about", "noop", "analyze", "ai",
)

_FALLBACK_LABELS = {
    "del": "حذف", "delete": "حذف", "stop": "إيقاف", "restart": "إعادة تشغيل",
    "run": "تشغيل", "play": "تشغيل", "log": "السجل", "download": "تحميل",
    "zip": "تحميل ZIP", "user": "المستخدم", "open": "عرض",
    "back": "رجوع", "cancel": "إلغاء", "noop": "عرض", "analyze": "تحليل AI",
    "approve": "موافقة", "reject": "رفض",
}


def _normalize_style(style: str) -> str:
    style = (style or "primary").lower().strip()
    return style if style in BUTTON_STYLES else "primary"


def _clean_button_label(label: str) -> str:
    label = str(label or "")
    label = re.sub(r"\s+", " ", label).strip(" ·|-–—")
    return label.strip() or "زر"


def _label_from_context(context_key: str) -> str:
    key = str(context_key or "").lower()
    for hint, fallback in _FALLBACK_LABELS.items():
        if hint in key:
            return fallback
    return "إجراء"


def _style_from_context(label: str, context_key: str = "", preferred: str = "primary") -> str:
    haystack = f"{label} {context_key}".lower()
    if any(h in haystack for h in _DANGER_HINTS):
        return "danger"
    if any(h in haystack for h in _SUCCESS_HINTS):
        return "success"
    if any(h in haystack for h in _PRIMARY_HINTS):
        return "primary"
    return _normalize_style(preferred)


def _styled_button(label: str, style: str = "primary", *,
                   callback_data: Optional[str] = None,
                   url: Optional[str] = None) -> InlineKeyboardButton:
    clean_label = _clean_button_label(label)
    if clean_label == "زر":
        clean_label = _label_from_context(callback_data or url or "")
    final_style = _normalize_style(style)
    kwargs: Dict[str, Any] = {"api_kwargs": {"style": final_style}}
    if url is not None:
        kwargs["url"] = url
    else:
        kwargs["callback_data"] = callback_data or "noop"
    return InlineKeyboardButton(clean_label, **kwargs)


def _button_style(button: InlineKeyboardButton) -> str:
    try:
        return _normalize_style((button.to_dict() or {}).get("style", "primary"))
    except Exception:
        return "primary"


def _ensure_button_style(button: InlineKeyboardButton, index: int) -> InlineKeyboardButton:
    try:
        existing_api = dict(getattr(button, "api_kwargs", None) or {})
        if existing_api.get("style") in BUTTON_STYLES:
            return button
        data = button.to_dict() or {}
    except Exception:
        return button
    if data.get("style") in BUTTON_STYLES:
        return button
    text = _clean_button_label(data.get("text", ""))
    cb   = str(data.get("callback_data") or data.get("url") or "")
    style = _style_from_context(text, cb, BUTTON_STYLES[index % len(BUTTON_STYLES)])
    data.pop("text", None)
    data.pop("style", None)
    existing_api["style"] = style
    try:
        return InlineKeyboardButton(text, api_kwargs=existing_api, **data)
    except Exception:
        return _styled_button(text, style, callback_data=cb or "noop")


def _reshape_keyboard_rows(buttons: List[InlineKeyboardButton]) -> List[List[InlineKeyboardButton]]:
    total = len(buttons)
    if total < 6:
        return [buttons] if buttons else []
    per_row = 5 if total >= 15 else 4 if total >= 8 else 3
    rows: List[List[InlineKeyboardButton]] = []
    for i in range(0, total, per_row):
        rows.append(buttons[i:i + per_row])
    if len(rows) > 1 and len(rows[-1]) < 3 and len(rows[-2]) + len(rows[-1]) <= 5:
        rows[-2].extend(rows[-1])
        rows.pop()
    return rows


def _normalize_keyboard_layout(rows: List[List[InlineKeyboardButton]]) -> List[List[InlineKeyboardButton]]:
    result: List[List[InlineKeyboardButton]] = []
    idx = 0
    for row in rows or []:
        new_row: List[InlineKeyboardButton] = []
        for button in row or []:
            new_row.append(_ensure_button_style(button, idx))
            idx += 1
        if new_row:
            result.append(new_row)
    return result


class InlineKeyboardMarkup(TelegramInlineKeyboardMarkup):
    def __init__(self, inline_keyboard: List[List[InlineKeyboardButton]], *args, **kwargs):
        super().__init__(_normalize_keyboard_layout(inline_keyboard), *args, **kwargs)


def btn_success(label: str, cb: str)  -> InlineKeyboardButton: return _styled_button(label, "success", callback_data=cb)
def btn_primary(label: str, cb: str)  -> InlineKeyboardButton: return _styled_button(label, "primary", callback_data=cb)
def btn_danger(label: str, cb: str)   -> InlineKeyboardButton: return _styled_button(label, "danger",  callback_data=cb)
def btn_warning(label: str, cb: str)  -> InlineKeyboardButton: return _styled_button(label, "primary", callback_data=cb)
def btn_secondary(label: str, cb: str)-> InlineKeyboardButton: return _styled_button(label, "primary", callback_data=cb)
def btn_url_success(label: str, url: str)-> InlineKeyboardButton: return _styled_button(label, "success", url=url)
def btn_url_primary(label: str, url: str)-> InlineKeyboardButton: return _styled_button(label, "primary", url=url)
def btn_url_danger(label: str, url: str) -> InlineKeyboardButton: return _styled_button(label, "danger",  url=url)
def btn_toggle(label: str, cb: str, active: bool) -> InlineKeyboardButton:
    return _styled_button(label, "success" if active else "danger", callback_data=cb)
def btn_noop(label: str) -> InlineKeyboardButton: return _styled_button(label, "primary", callback_data="noop")


# ═══════════════════════════════════════════════════════════════════════════════
# 💾  نماذج البيانات
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class User:
    user_id: int
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    points: int = 0
    free_uploads: int = 1
    total_uploads: int = 0
    total_downloads: int = 0
    total_runs: int = 0
    invited_users: List[int] = field(default_factory=list)
    invited_by: Optional[int] = None
    invite_reward_given_for: List[int] = field(default_factory=list)
    is_banned: bool = False
    ban_reason: str = ""
    ban_until: str = ""
    is_premium: bool = False
    premium_until: str = ""
    premium_granted_by: int = 0
    join_date: str = ""
    last_active: str = ""
    files: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    language: str = "ar"
    purchases_total_stars: int = 0
    notifications_enabled: bool = True
    is_admin: bool = False
    login_count: int = 0
    last_ip: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    rate_violations: int = 0
    total_points_earned: int = 0
    scheduled_runs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class HostedFile:
    file_id: str
    file_name: str
    owner_id: int
    upload_date: str
    size: int = 0
    downloads: int = 0
    libraries: List[str] = field(default_factory=list)
    is_active: bool = True
    description: str = ""
    category: str = "general"
    process_id: Optional[int] = None
    run_count: int = 0
    last_run: str = ""
    last_stop: str = ""
    auto_restart: bool = False
    is_public: bool = False
    install_log: str = ""
    runtime_log: str = ""
    stored_path: str = ""
    entry_file: str = ""
    is_zip: bool = False
    tags: List[str] = field(default_factory=list)
    version: int = 1
    start_time: str = ""
    total_runtime_seconds: int = 0
    ai_analysis: str = ""
    pending_approval: bool = False
    approval_status: str = "pending"


@dataclass
class Channel:
    chat_id: str
    title: str = ""
    invite_link: str = ""
    added_by: int = 0
    added_at: str = ""
    enabled: bool = True


@dataclass
class ScheduledTask:
    task_id: str
    file_id: str
    owner_id: int
    run_at: str
    repeat: str = "once"
    enabled: bool = True
    created_at: str = ""
    last_triggered: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# 💾  قاعدة البيانات
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    DEFAULT_SETTINGS: Dict[str, Any] = {
        "maintenance_mode": False,
        "require_subscription": True,
        "points_per_invite": 2,
        "upload_cost": 1,
        "stars_per_10_points": DEFAULT_STARS_PER_10_POINTS,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "allowed_extensions": [".py", ".zip"],
        "welcome_message": "أهلاً بك في PyHost Pro Ultra — أقوى بوت استضافة!",
        "bot_active": True,
        "auto_install_libs": True,
        "auto_run_after_upload": True,
        "auto_restart_default": False,
        "send_zip_if_run_fails": True,
        "strict_hosting_security": True,
        "ban_on_confirmed_danger": True,
        "max_processes_per_user": MAX_PROCESSES_PER_USER,
        "run_timeout_seconds": RUN_TIMEOUT_SECONDS,
        "first_upload_free": True,
        "broadcast_throttle_ms": 50,
        "log_runtime_lines": 300,
        "public_files_enabled": True,
        "support_username": SUPPORT_USERNAME,
        "stickers": dict(STICKERS),
        "notify_admin_on_join": True,
        "notify_admin_on_upload": True,
        "notify_admin_on_ban": True,
        "premium_upload_free": True,
        "premium_max_processes": 10,
        "rate_limit_enabled": True,
        "rate_limit_messages": RATE_LIMIT_MESSAGES,
        "rate_limit_window": RATE_LIMIT_WINDOW,
        "auto_cleanup_days": 30,
        "leaderboard_enabled": True,
        "schedule_enabled": True,
        "admin_immortal": True,
        "ai_analysis_enabled": True,
        "api_protection_enabled": True,
        "require_approval": False,
        "security_enabled": False,
    }

    def __init__(self):
        self._lock = threading.RLock()
        self.users: Dict[int, User] = {}
        self.files: Dict[str, HostedFile] = {}
        self.channels: Dict[str, Channel] = {}
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.stats: Dict[str, Any] = {
            "total_users": 0, "total_files": 0, "total_downloads": 0,
            "total_points_given": 0, "total_stars_received": 0,
            "total_runs": 0, "total_bans": 0, "total_broadcasts": 0,
            "created_at": datetime.now().isoformat(), "daily_active": {},
        }
        self.settings: Dict[str, Any] = dict(self.DEFAULT_SETTINGS)
        self.pending_payments: Dict[int, Dict[str, Any]] = {}
        self.banned_words: List[str] = []
        self.broadcast_history: List[Dict[str, Any]] = []
        self.promo_codes: Dict[str, Dict[str, Any]] = {}
        self.security_events: List[Dict[str, Any]] = []
        self.activity_log: List[Dict[str, Any]] = []
        self.pending_uploads: Dict[str, Dict[str, Any]] = {}
        self._dirty: bool = False
        self._last_save: float = 0.0
        self.load()

    def load(self) -> None:
        with self._lock:
            try:
                if not os.path.exists(DATABASE_FILE):
                    self.save(force=True)
                    return
                with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for uid, udata in data.get("users", {}).items():
                    udata.pop("user_id", None)
                    valid = {k: v for k, v in udata.items() if k in User.__annotations__}
                    self.users[int(uid)] = User(user_id=int(uid), **valid)
                for fid, fdata in data.get("files", {}).items():
                    fdata.pop("file_id", None)
                    valid = {k: v for k, v in fdata.items() if k in HostedFile.__annotations__}
                    self.files[fid] = HostedFile(file_id=fid, **valid)
                for cid, cdata in data.get("channels", {}).items():
                    cdata.pop("chat_id", None)
                    valid = {k: v for k, v in cdata.items() if k in Channel.__annotations__}
                    self.channels[cid] = Channel(chat_id=cid, **valid)
                for tid, tdata in data.get("scheduled_tasks", {}).items():
                    tdata.pop("task_id", None)
                    valid = {k: v for k, v in tdata.items() if k in ScheduledTask.__annotations__}
                    self.scheduled_tasks[tid] = ScheduledTask(task_id=tid, **valid)
                self.stats.update(data.get("stats", {}))
                self.settings.update(data.get("settings", {}))
                self.banned_words      = data.get("banned_words", [])
                self.broadcast_history = data.get("broadcast_history", [])
                self.promo_codes       = data.get("promo_codes", {})
                self.security_events   = data.get("security_events", [])[-500:]
                self.activity_log      = data.get("activity_log", [])[-500:]
                self.pending_uploads   = data.get("pending_uploads", {})
                logger.info("تحميل: %d مستخدم، %d ملف، %d قناة",
                            len(self.users), len(self.files), len(self.channels))
            except Exception as e:
                logger.exception("خطأ في تحميل قاعدة البيانات: %s", e)

    def save(self, force: bool = False) -> None:
        with self._lock:
            try:
                now = time.time()
                if not force and (now - self._last_save) < 0.5 and not self._dirty:
                    return
                payload = {
                    "users":    {str(uid): asdict(u) for uid, u in self.users.items()},
                    "files":    {fid: asdict(f)       for fid, f in self.files.items()},
                    "channels": {cid: asdict(c)       for cid, c in self.channels.items()},
                    "scheduled_tasks": {tid: asdict(t) for tid, t in self.scheduled_tasks.items()},
                    "stats":    self.stats,
                    "settings": self.settings,
                    "banned_words":     self.banned_words,
                    "broadcast_history": self.broadcast_history[-200:],
                    "promo_codes":      self.promo_codes,
                    "security_events":  self.security_events[-500:],
                    "activity_log":     self.activity_log[-500:],
                    "pending_uploads":  self.pending_uploads,
                    "saved_at": datetime.now().isoformat(),
                }
                tmp = DATABASE_FILE + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                os.replace(tmp, DATABASE_FILE)
                self._last_save = now
                self._dirty = False
            except Exception as e:
                logger.exception("خطأ في حفظ قاعدة البيانات: %s", e)

    def mark_dirty(self) -> None: self._dirty = True

    def log_activity(self, action: str, user_id: int = 0, detail: str = "") -> None:
        self.activity_log.append({
            "action": action, "user_id": user_id,
            "detail": detail, "at": now_iso(),
        })
        self.mark_dirty()

    def get_user(self, user_id: int, **kwargs) -> "User":
        with self._lock:
            is_new = user_id not in self.users
            if is_new:
                now_iso_val = datetime.now().isoformat()
                self.users[user_id] = User(
                    user_id=user_id,
                    join_date=now_iso_val,
                    last_active=now_iso_val,
                    free_uploads=1 if self.settings.get("first_upload_free", True) else 0,
                    is_admin=(user_id in ADMIN_IDS),
                    **{k: v for k, v in kwargs.items() if k in User.__annotations__},
                )
                self.stats["total_users"] = len(self.users)
                self.save(force=True)
            else:
                u = self.users[user_id]
                for k, v in kwargs.items():
                    if k in User.__annotations__ and k not in ("user_id", "join_date"):
                        setattr(u, k, v)
            return self.users[user_id]

    def update_user(self, user: "User", save: bool = True) -> None:
        with self._lock:
            user.last_active = datetime.now().isoformat()
            if user.user_id in ADMIN_IDS:
                user.is_banned = False
                user.ban_reason = ""
                user.ban_until = ""
                user.is_admin = True
            self.users[user.user_id] = user
            if save:
                self.save()
            else:
                self.mark_dirty()

    def all_users(self) -> List["User"]: return list(self.users.values())

    def search_users(self, query: str) -> List["User"]:
        q = query.strip().lower()
        return [u for u in self.all_users() if
                q in str(u.user_id) or q in (u.username or "").lower()
                or q in (u.first_name or "").lower() or q in (u.last_name or "").lower()
                or q in (u.notes or "").lower()]

    def get_premium_users(self) -> List["User"]:
        return [u for u in self.all_users() if u.is_premium and not u.is_banned]

    def get_new_users(self, days: int = 7) -> List["User"]:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return [u for u in self.all_users() if u.join_date >= cutoff]

    def top_users_by_points(self, n: int = 10) -> List["User"]:
        return sorted(self.all_users(), key=lambda u: u.points, reverse=True)[:n]

    def top_users_by_uploads(self, n: int = 10) -> List["User"]:
        return sorted(self.all_users(), key=lambda u: u.total_uploads, reverse=True)[:n]

    def top_users_by_invites(self, n: int = 10) -> List["User"]:
        return sorted(self.all_users(), key=lambda u: len(u.invited_users), reverse=True)[:n]

    def add_file(self, hf: "HostedFile") -> None:
        with self._lock:
            self.files[hf.file_id] = hf
            self.stats["total_files"] = len(self.files)
            self.save(force=True)

    def get_file(self, file_id: str) -> Optional["HostedFile"]: return self.files.get(file_id)

    def remove_file(self, file_id: str) -> bool:
        with self._lock:
            hf = self.files.pop(file_id, None)
            if not hf: return False
            owner = self.users.get(hf.owner_id)
            if owner and file_id in owner.files:
                owner.files.remove(file_id)
            self.stats["total_files"] = len(self.files)
            self.save(force=True)
            return True

    def user_files(self, user_id: int) -> List["HostedFile"]:
        return [f for f in self.files.values() if f.owner_id == user_id]

    def all_files_sorted(self) -> List["HostedFile"]:
        return sorted(self.files.values(), key=lambda x: x.upload_date, reverse=True)

    def get_pending_files(self) -> List["HostedFile"]:
        return [f for f in self.files.values() if f.pending_approval and f.approval_status == "pending"]

    def add_channel(self, ch: Channel) -> None:
        with self._lock:
            self.channels[ch.chat_id] = ch
            self.save(force=True)

    def remove_channel(self, chat_id: str) -> bool:
        with self._lock:
            if chat_id in self.channels:
                del self.channels[chat_id]
                self.save(force=True)
                return True
            return False

    def all_channels(self, enabled_only: bool = False) -> List[Channel]:
        chs = list(self.channels.values())
        return [c for c in chs if c.enabled] if enabled_only else chs

    def record_daily_active(self, user_id: int) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        day_data = self.stats.setdefault("daily_active", {})
        day_users = day_data.setdefault(today, [])
        if user_id not in day_users:
            day_users.append(user_id)
            self.mark_dirty()


db = Database()


# ═══════════════════════════════════════════════════════════════════════════════
# ⏱  نظام Rate Limiting
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    def __init__(self):
        self._buckets: Dict[int, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, user_id: int) -> bool:
        if user_id in ADMIN_IDS: return True
        if not db.settings.get("rate_limit_enabled", True): return True
        limit  = int(db.settings.get("rate_limit_messages", RATE_LIMIT_MESSAGES))
        window = int(db.settings.get("rate_limit_window", RATE_LIMIT_WINDOW))
        now    = time.time()
        with self._lock:
            bucket = self._buckets[user_id]
            while bucket and bucket[0] < now - window:
                bucket.popleft()
            if len(bucket) >= limit: return False
            bucket.append(now)
            return True

    def reset(self, user_id: int) -> None:
        with self._lock:
            self._buckets.pop(user_id, None)


rate_limiter = RateLimiter()


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧  دوال مساعدة
# ═══════════════════════════════════════════════════════════════════════════════

def is_admin(user_id: int) -> bool: return user_id in ADMIN_IDS
def is_admin_immortal(user_id: int) -> bool: return user_id in ADMIN_IDS
def escape_html(text: str) -> str: return html.escape(str(text or ""))
def now_iso() -> str: return datetime.now().isoformat()

def format_size(size: int) -> str:
    s = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if s < 1024: return f"{s:.2f} {unit}"
        s /= 1024
    return f"{s:.2f} TB"

def format_dt(iso: str, default: str = "—") -> str:
    if not iso: return default
    try: return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
    except: return iso

def humanize_delta(iso: str) -> str:
    if not iso: return "—"
    try:
        sec = int((datetime.now() - datetime.fromisoformat(iso)).total_seconds())
        if sec < 60: return f"منذ {sec}ث"
        if sec < 3600: return f"منذ {sec // 60}د"
        if sec < 86400: return f"منذ {sec // 3600}س"
        return f"منذ {sec // 86400} يوم"
    except: return iso

def runtime_delta(iso: str) -> str:
    if not iso: return "—"
    try:
        sec = int((datetime.now() - datetime.fromisoformat(iso)).total_seconds())
        h, r = divmod(sec, 3600); m, s = divmod(r, 60)
        return f"{h}س {m}د {s}ث" if h else (f"{m}د {s}ث" if m else f"{s}ث")
    except: return "—"

def generate_file_id() -> str:
    return hashlib.md5(f"{datetime.now().isoformat()}{os.urandom(8).hex()}".encode()).hexdigest()[:12]

def generate_task_id() -> str:
    return "task_" + hashlib.md5(f"{datetime.now().isoformat()}{os.urandom(4).hex()}".encode()).hexdigest()[:8]

def safe_filename(name: str) -> str:
    name = (name or "file").strip().replace("\\", "_").replace("/", "_")
    name = re.sub(r"[^\w.\-+ ()\[\]]+", "_", name, flags=re.U)
    return name[:120] or "file"

def chunk_list(lst: List[Any], n: int) -> List[List[Any]]:
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def shorten(text: str, limit: int = 60) -> str:
    if not text: return ""
    return text if len(text) <= limit else text[:limit - 1] + "…"

def progress_bar(percent: int, width: int = 12) -> str:
    percent = max(0, min(100, int(percent)))
    filled  = round(width * percent / 100)
    return "▰" * filled + "▱" * (width - filled)

def is_safe_ext(name: str) -> bool:
    ext = os.path.splitext(name)[1].lower()
    return ext in db.settings.get("allowed_extensions", [".py", ".zip"])

def sticker_id(name: str) -> str:
    stickers = db.settings.get("stickers") or {}
    return str(stickers.get(name) or STICKERS.get(name) or "").strip()


# ═══════════════════════════════════════════════════════════════════════════════
# 🖥  مراقبة موارد النظام
# ═══════════════════════════════════════════════════════════════════════════════

class ResourceMonitor:
    @staticmethod
    def get_cpu_percent() -> float:
        try:
            import psutil; return psutil.cpu_percent(interval=0.5)
        except:
            try:
                with open("/proc/loadavg") as f:
                    load = float(f.read().split()[0])
                return min(100.0, (load / (os.cpu_count() or 1)) * 100)
            except: return -1.0

    @staticmethod
    def get_memory() -> Tuple[float, float, float]:
        try:
            import psutil; m = psutil.virtual_memory()
            return m.used / 1024**2, m.total / 1024**2, m.percent
        except:
            try:
                with open("/proc/meminfo") as f:
                    info = {}
                    for line in f:
                        k, v = line.split(":")
                        info[k.strip()] = int(v.split()[0])
                total = info.get("MemTotal", 0)
                free  = info.get("MemFree", 0) + info.get("Buffers", 0) + info.get("Cached", 0)
                used  = total - free
                return used / 1024, total / 1024, (used / total * 100) if total else 0
            except: return -1, -1, -1

    @staticmethod
    def get_disk() -> Tuple[float, float, float]:
        try:
            import psutil; d = psutil.disk_usage(".")
            return d.used / 1024**3, d.total / 1024**3, d.percent
        except:
            try:
                stat  = os.statvfs(".")
                total = stat.f_blocks * stat.f_frsize
                free  = stat.f_bfree  * stat.f_frsize
                used  = total - free
                return used / 1024**3, total / 1024**3, (used / total * 100) if total else 0
            except: return -1, -1, -1

    @classmethod
    def summary_text(cls) -> str:
        cpu = cls.get_cpu_percent()
        mu, mt, mp = cls.get_memory()
        du, dt, dp = cls.get_disk()
        cpu_bar  = progress_bar(int(cpu) if cpu >= 0 else 0, 8)
        mem_bar  = progress_bar(int(mp)  if mp  >= 0 else 0, 8)
        disk_bar = progress_bar(int(dp)  if dp  >= 0 else 0, 8)
        cpu_str  = f"{cpu:.1f}%" if cpu >= 0 else "N/A"
        mem_str  = f"{mu:.0f}/{mt:.0f} MB ({mp:.1f}%)" if mu >= 0 else "N/A"
        disk_str = f"{du:.2f}/{dt:.2f} GB ({dp:.1f}%)" if du >= 0 else "N/A"
        return (
            f"{Icon.CPU} CPU:  {cpu_bar} {cpu_str}\n"
            f"{Icon.MEMORY} RAM:  {mem_bar} {mem_str}\n"
            f"{Icon.DISK} Disk: {disk_bar} {disk_str}"
        )


res_monitor = ResourceMonitor()


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠  محلل الكود بالذكاء الاصطناعي — AI Code Analyzer
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AIAnalysisResult:
    code_type: str = "غير محدد"
    quality_score: int = 0
    complexity: str = "منخفض"
    libraries_count: int = 0
    functions_count: int = 0
    classes_count: int = 0
    lines_of_code: int = 0
    has_main: bool = False
    has_async: bool = False
    has_error_handling: bool = False
    has_logging: bool = False
    has_config: bool = False
    is_bot: bool = False
    bot_framework: str = ""
    api_calls: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    security_notes: List[str] = field(default_factory=list)
    summary: str = ""


class AICodeAnalyzer:
    BOT_FRAMEWORKS: Dict[str, str] = {
        "telegram": "بوت تيليجرام (python-telegram-bot)",
        "telebot":  "بوت تيليجرام (pyTelegramBotAPI)",
        "pyrogram": "بوت تيليجرام (Pyrogram)",
        "telethon": "بوت تيليجرام (Telethon)",
        "aiogram":  "بوت تيليجرام (aiogram)",
        "discord":  "بوت ديسكورد",
        "flask":    "تطبيق ويب (Flask)",
        "fastapi":  "API (FastAPI)",
        "django":   "تطبيق ويب (Django)",
        "sanic":    "تطبيق ويب (Sanic)",
        "aiohttp":  "خادم ويب (aiohttp)",
        "selenium": "تحكم متصفح (Selenium)",
        "scrapy":   "سكرابر (Scrapy)",
        "tweepy":   "بوت تويتر (Tweepy)",
    }

    CODE_TYPES: List[Tuple[List[str], str]] = [
        (["Application", "run_polling", "Dispatcher", "handler", "CommandHandler"],
         "بوت تيليجرام"),
        (["Flask", "route", "app.run", "render_template", "jsonify"],
         "تطبيق ويب Flask"),
        (["FastAPI", "APIRouter", "uvicorn", "@app.get", "@app.post"],
         "API FastAPI"),
        (["selenium", "webdriver", "find_element", "click()"],
         "أتمتة متصفح"),
        (["requests", "BeautifulSoup", "scrapy", "lxml"],
         "كاشط ويب (Scraper)"),
        (["pandas", "numpy", "matplotlib", "seaborn", "sklearn"],
         "تحليل بيانات"),
        (["torch", "tensorflow", "keras", "transformers"],
         "تعلم آلي / ذكاء اصطناعي"),
        (["schedule", "cron", "APScheduler", "asyncio.sleep"],
         "مهام مجدولة"),
        (["asyncio", "aiohttp", "async def", "await"],
         "برنامج غير متزامن"),
    ]

    QUALITY_POSITIVE: List[Tuple[str, int, str]] = [
        (r"try\s*:", 5, "معالجة استثناءات"),
        (r"except\s+\w", 5, "معالجة استثناءات محددة"),
        (r"logging\.", 5, "نظام تسجيل"),
        (r"logger\.", 5, "مسجل مخصص"),
        (r'"""[\s\S]*?"""', 3, "توثيق Docstring"),
        (r"if __name__\s*==\s*[\"']__main__[\"']", 5, "نقطة دخول رئيسية"),
        (r"def\s+\w+\s*\(", 2, "دوال منظمة"),
        (r"class\s+\w+", 3, "برمجة كائنية"),
        (r"@dataclass", 4, "استخدام dataclass"),
        (r"from\s+typing\s+import|:\s+(?:str|int|List|Dict|Optional)", 3, "تلميحات نوع"),
        (r"\.env|os\.getenv|os\.environ", 3, "إدارة متغيرات البيئة"),
        (r"async\s+def\s+\w+", 3, "برمجة غير متزامنة"),
        (r"with\s+open\s*\(", 2, "إدارة سياق جيدة"),
        (r"requirements\.txt|setup\.py|pyproject\.toml", 3, "ملف متطلبات"),
    ]

    QUALITY_NEGATIVE: List[Tuple[str, int, str]] = [
        (r"except\s*:", -3, "catch-all بدون نوع"),
        (r"pass\s*$", -1, "pass فارغ"),
        (r"time\.sleep\(\s*[5-9]\d+", -2, "نوم طويل يعطّل البرنامج"),
        (r"global\s+\w+", -2, "متغيرات global"),
        (r"eval\s*\(", -5, "استخدام eval - خطر"),
        (r"exec\s*\(", -5, "استخدام exec - خطر"),
        (r"print\s*\(", -1, "print بدلاً من logging"),
        (r"#\s*TODO|#\s*FIXME|#\s*HACK", -1, "مهام غير مكتملة"),
        (r"input\s*\(", -3, "input تفاعلي يعطّل التشغيل التلقائي"),
    ]

    API_PATTERNS: List[Tuple[str, str]] = [
        (r"requests\.(get|post|put|delete|patch)", "HTTP Requests"),
        (r"aiohttp\.ClientSession", "aiohttp Async HTTP"),
        (r"httpx\.", "httpx HTTP"),
        (r"openai\.", "OpenAI API"),
        (r"anthropic\.", "Anthropic API"),
        (r"boto3\.", "AWS API"),
        (r"googleapiclient\.", "Google API"),
        (r"tweepy\.", "Twitter API"),
        (r"pymongo\.|MongoClient", "MongoDB"),
        (r"redis\.", "Redis"),
        (r"psycopg2\.|asyncpg\.", "PostgreSQL"),
        (r"aiosqlite\.|sqlite3\.", "SQLite"),
        (r"sqlalchemy\.", "SQLAlchemy ORM"),
        (r"smtplib\.|email\.mime", "بريد إلكتروني"),
    ]

    @classmethod
    def _detect_code_type(cls, source: str, imports: Set[str]) -> Tuple[str, str]:
        for keywords, code_type in cls.CODE_TYPES:
            if any(kw in source for kw in keywords):
                return code_type, ""
        for lib, desc in cls.BOT_FRAMEWORKS.items():
            if lib in imports:
                return desc, lib
        if imports:
            return "سكريبت Python", ""
        return "كود Python", ""

    @classmethod
    def _extract_imports(cls, tree: ast.AST) -> Set[str]:
        names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    names.add(node.module.split(".")[0])
        return names

    @classmethod
    def analyze_source(cls, source: str, filename: str = "file.py") -> AIAnalysisResult:
        result = AIAnalysisResult()
        lines  = source.splitlines()
        result.lines_of_code = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

        try:
            tree = ast.parse(source)
            imports = cls._extract_imports(tree)
            result.libraries_count = len(imports)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result.functions_count += 1
                    if isinstance(node, ast.AsyncFunctionDef):
                        result.has_async = True
                elif isinstance(node, ast.ClassDef):
                    result.classes_count += 1

            code_type, bot_fw = cls._detect_code_type(source, imports)
            result.code_type     = code_type
            result.bot_framework = bot_fw
            result.is_bot = any(fw in imports for fw in cls.BOT_FRAMEWORKS)

        except SyntaxError as e:
            result.potential_issues.append(f"خطأ في بناء الجملة: {e}")
        except Exception:
            pass

        score = 50
        for pattern, pts, label in cls.QUALITY_POSITIVE:
            if re.search(pattern, source, re.M):
                score += pts
                if pts >= 3:
                    result.recommendations.append(f"ممتاز: {label}")
        for pattern, pts, label in cls.QUALITY_NEGATIVE:
            if re.search(pattern, source, re.M):
                score += pts
                result.potential_issues.append(label)

        result.has_main          = bool(re.search(r"if __name__\s*==\s*[\"']__main__[\"']", source))
        result.has_error_handling= bool(re.search(r"try\s*:", source))
        result.has_logging       = bool(re.search(r"logging\.|logger\.", source))
        result.has_config        = bool(re.search(r"os\.getenv|os\.environ|\.env", source))

        for pattern, name in cls.API_PATTERNS:
            if re.search(pattern, source):
                result.api_calls.append(name)

        if result.lines_of_code < 50:   result.complexity = "بسيط"
        elif result.lines_of_code < 200: result.complexity = "متوسط"
        elif result.lines_of_code < 500: result.complexity = "متقدم"
        else:                             result.complexity = "ضخم"

        score += min(result.functions_count * 2, 15)
        score += min(result.classes_count * 3, 12)
        if result.has_async:    score += 5
        if result.has_logging:  score += 5
        if result.has_config:   score += 3
        if result.has_main:     score += 5

        result.quality_score = max(0, min(100, score))

        if not result.has_error_handling:
            result.recommendations.append("أضف try/except لمعالجة الأخطاء")
        if not result.has_logging:
            result.recommendations.append("استخدم logging بدلاً من print")
        if not result.has_config:
            result.recommendations.append("استخدم os.getenv لمتغيرات الإعداد")
        if not result.has_main and result.lines_of_code > 20:
            result.recommendations.append("أضف if __name__ == '__main__'")
        if result.lines_of_code > 500 and result.classes_count < 3:
            result.recommendations.append("فكر في تقسيم الكود لوحدات منفصلة")

        if re.search(r"eval\s*\(|exec\s*\(", source):
            result.security_notes.append("تجنب eval/exec — خطر أمني")
        if re.search(r"BOT_TOKEN\s*=\s*['\"][0-9A-Za-z:_-]{20,}", source):
            result.security_notes.append("لا تضع التوكن مباشرة في الكود — استخدم .env")
        if re.search(r"os\.system\s*\(", source):
            result.security_notes.append("os.system قد يكون خطراً — استخدم subprocess بأمان")

        quality_label = (
            "ممتاز"    if result.quality_score >= 80 else
            "جيد"      if result.quality_score >= 60 else
            "مقبول"    if result.quality_score >= 40 else
            "يحتاج تحسين"
        )
        result.summary = (
            f"{result.code_type} بجودة {quality_label} ({result.quality_score}/100). "
            f"{result.lines_of_code} سطر، {result.functions_count} دالة، "
            f"{result.classes_count} كلاس، {result.libraries_count} مكتبة."
        )
        return result

    @classmethod
    def analyze_file(cls, path: str) -> AIAnalysisResult:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return cls.analyze_source(f.read(), os.path.basename(path))
        except Exception as e:
            r = AIAnalysisResult()
            r.potential_issues.append(f"تعذر تحليل الملف: {e}")
            return r

    @classmethod
    def analyze_directory(cls, dir_path: str) -> AIAnalysisResult:
        py_files = []
        for root, _, files in os.walk(dir_path):
            for fn in files:
                if fn.endswith(".py"):
                    py_files.append(os.path.join(root, fn))

        if not py_files:
            r = AIAnalysisResult()
            r.code_type = "لا توجد ملفات Python"
            return r

        if len(py_files) == 1:
            return cls.analyze_file(py_files[0])

        results: List[AIAnalysisResult] = [cls.analyze_file(p) for p in py_files[:10]]
        merged = AIAnalysisResult()
        merged.lines_of_code   = sum(r.lines_of_code for r in results)
        merged.functions_count = sum(r.functions_count for r in results)
        merged.classes_count   = sum(r.classes_count for r in results)
        merged.libraries_count = sum(r.libraries_count for r in results)
        merged.has_async       = any(r.has_async for r in results)
        merged.has_error_handling = any(r.has_error_handling for r in results)
        merged.has_logging     = any(r.has_logging for r in results)
        merged.has_config      = any(r.has_config for r in results)
        merged.is_bot          = any(r.is_bot for r in results)
        merged.api_calls = list(set(a for r in results for a in r.api_calls))
        merged.potential_issues = list(set(i for r in results for i in r.potential_issues))[:6]
        merged.recommendations  = list(set(rec for r in results for rec in r.recommendations))[:5]
        merged.security_notes   = list(set(s for r in results for s in r.security_notes))[:4]

        bot_result = next((r for r in results if r.is_bot), None)
        merged.code_type = bot_result.code_type if bot_result else results[0].code_type
        merged.quality_score = int(sum(r.quality_score for r in results) / len(results))

        if merged.lines_of_code < 200:   merged.complexity = "بسيط"
        elif merged.lines_of_code < 800: merged.complexity = "متوسط"
        elif merged.lines_of_code < 2000: merged.complexity = "متقدم"
        else:                              merged.complexity = "ضخم"

        quality_label = (
            "ممتاز" if merged.quality_score >= 80 else
            "جيد"   if merged.quality_score >= 60 else
            "مقبول" if merged.quality_score >= 40 else "يحتاج تحسين"
        )
        merged.summary = (
            f"مشروع {merged.code_type} ({len(py_files)} ملف) بجودة {quality_label} "
            f"({merged.quality_score}/100). {merged.lines_of_code} سطر إجمالاً."
        )
        return merged

    @classmethod
    def format_report(cls, result: AIAnalysisResult, filename: str = "") -> str:
        stars = "⭐" * max(1, min(5, result.quality_score // 20))

        def score_emoji(s: int) -> str:
            if s >= 80: return "🟢"
            if s >= 60: return "🟡"
            if s >= 40: return "🟠"
            return "🔴"

        lines = [
            f"{Icon.AI} <b>تحليل الذكاء الاصطناعي</b>",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        if filename:
            lines.append(f"{Icon.FILE} الملف: <code>{escape_html(filename)}</code>")

        lines += [
            f"{Icon.CODE} النوع: <b>{escape_html(result.code_type)}</b>",
            f"{score_emoji(result.quality_score)} جودة الكود: <b>{result.quality_score}/100</b> {stars}",
            f"{Icon.STATS} التعقيد: <b>{result.complexity}</b>",
            f"",
            f"{Icon.INFO} <b>الإحصائيات:</b>",
            f"  • الأسطر: <b>{result.lines_of_code}</b>",
            f"  • الدوال: <b>{result.functions_count}</b>",
            f"  • الكلاسات: <b>{result.classes_count}</b>",
            f"  • المكتبات: <b>{result.libraries_count}</b>",
        ]

        features = []
        if result.has_async:         features.append("غير متزامن")
        if result.has_error_handling:features.append("معالجة أخطاء")
        if result.has_logging:       features.append("تسجيل أحداث")
        if result.has_config:        features.append("إعدادات بيئة")
        if result.has_main:          features.append("نقطة دخول")
        if features:
            lines.append(f"  • الميزات: {' · '.join(features)}")

        if result.api_calls:
            lines += [
                f"",
                f"{Icon.NETWORK} <b>استدعاءات API:</b>",
            ]
            for api in result.api_calls[:5]:
                lines.append(f"  • {escape_html(api)}")

        if result.security_notes:
            lines += [
                f"",
                f"{Icon.SHIELD} <b>ملاحظات أمنية:</b>",
            ]
            for note in result.security_notes:
                lines.append(f"  {Icon.WARN} {escape_html(note)}")

        if result.potential_issues:
            lines += [
                f"",
                f"{Icon.BUG} <b>نقاط تحسين:</b>",
            ]
            for issue in result.potential_issues[:5]:
                lines.append(f"  • {escape_html(issue)}")

        if result.recommendations:
            lines += [
                f"",
                f"{Icon.LIGHT} <b>توصيات:</b>",
            ]
            for rec in result.recommendations[:4]:
                lines.append(f"  • {escape_html(rec)}")

        lines += [
            f"",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"{Icon.MAGIC} <b>الخلاصة:</b> {escape_html(result.summary)}",
        ]
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 🛡  حماية API والاستضافة — متقدمة جداً
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SecurityScan:
    blocked: bool = False
    ban: bool     = False
    score: int    = 0
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class HostingSecurity:
    CERTAIN_PATTERNS: List[Tuple[str, str]] = [
        (r"(?i)BOT_TOKEN|ADMIN_IDS|SUPPORT_USERNAME|PAYMENT_PROVIDER_TOKEN",
         "محاولة قراءة إعدادات بوت الاستضافة"),
        (r"(?i)bot_database\.json|hosted_files|bot_logs|backups|temp_work",
         "محاولة لمس ملفات الاستضافة الداخلية"),
        (r"(?i)DATABASE_FILE|FILES_DIR|LOGS_DIR|BACKUP_DIR|TEMP_DIR",
         "محاولة الوصول لمتغيرات مسارات الاستضافة"),
        (r"(?i)SUPABASE_SERVICE_ROLE_KEY|SUPABASE_URL|SUPABASE_KEY",
         "محاولة قراءة أسرار Supabase"),
        (r"(?i)AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|AWS_SESSION_TOKEN",
         "محاولة قراءة أسرار AWS"),
        (r"(?i)SECRET_KEY|PRIVATE_KEY|SIGNING_KEY|ENCRYPTION_KEY",
         "محاولة قراءة مفاتيح تشفير سرية"),
        (r"(?i)OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY|STRIPE_SECRET",
         "محاولة سرقة مفاتيح AI/Payment API"),
        (r"(?i)GITHUB_TOKEN|GITLAB_TOKEN|BITBUCKET_TOKEN",
         "محاولة سرقة رمز Git"),
        (r"(?i)MONGODB_URI|POSTGRES_URL|DATABASE_URL|REDIS_URL|MYSQL_PWD",
         "محاولة سرقة بيانات اتصال قاعدة البيانات"),
        (r"rm\s+-rf\s+/(?:\s|$)|shutil\.rmtree\(\s*['\"]\/",
         "محاولة حذف جذر النظام"),
        (r"os\.remove\(\s*DATABASE_FILE|open\(\s*DATABASE_FILE",
         "محاولة تعديل قاعدة بيانات الاستضافة"),
        (r"subprocess\.(?:Popen|run|call).*?(?:curl|wget).*?\|\s*(?:sh|bash)",
         "تحميل وتنفيذ سكربت خارجي"),
        (r"urllib\.request\.urlopen.*?\|\s*exec|requests\.get.*?\|\s*exec",
         "تنفيذ كود محمّل من الإنترنت"),
        (r"(?i)id_rsa|authorized_keys|\.ssh/|known_hosts|\.pem\b",
         "محاولة الوصول لمفاتيح SSH"),
        (r"fork\s*bomb|:\s*\(\s*\)\s*\{.*\|\s*:\s*&\s*\};",
         "Fork bomb مكتشف"),
        (r"while\s+True.*?(?:subprocess|os\.system|os\.popen).*?:",
         "حلقة لا نهائية مع تنفيذ أوامر"),
        (r"requests\.(get|post)\s*\(['\"]https?://(?!api\.telegram\.org).*?(?:token|secret|password|key)",
         "إرسال بيانات سرية لخادم خارجي"),
        (r"socket\.connect\s*\(.*?(?:\d{1,3}\.){3}\d{1,3}.*?\d{4,5}",
         "اتصال مباشر بعنوان IP خارجي"),
        (r"open\s*\(\s*['\"](?:/etc/passwd|/etc/shadow|/proc/|/sys/)",
         "محاولة قراءة ملفات نظام حساسة"),
        (r"(?i)__import__\s*\(\s*['\"]os['\"].*?system\s*\(",
         "تنفيذ أوامر نظام مخفية"),
    ]

    WARN_PATTERNS: List[Tuple[str, str]] = [
        (r"subprocess\.|os\.system\(|os\.popen\(", "يستخدم تنفيذ أوامر نظام"),
        (r"socket\.|requests\.|aiohttp\.|httpx\.", "يتصل بالشبكة"),
        (r"open\s*\(.*['\"]w['\"]", "يكتب ملفات"),
        (r"shutil\.rmtree|os\.remove|os\.unlink", "يحذف ملفات"),
        (r"eval\s*\(|exec\s*\(", "يستخدم eval/exec"),
        (r"ctypes\.|cffi\.", "يستخدم مكتبات ذات مستوى منخفض"),
        (r"importlib\.import_module\s*\(", "يستورد وحدات ديناميكياً"),
        (r"__builtins__|__import__", "يصل لـ builtins مباشرة"),
    ]

    DANGEROUS_EXTENSIONS: Set[str] = {
        ".exe", ".dll", ".so", ".dylib", ".sh", ".bash",
        ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jar",
        ".php", ".asp", ".aspx", ".cgi",
    }

    FORBIDDEN_FILENAMES: Set[str] = {
        ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
        "authorized_keys", "known_hosts", ".htpasswd", "credentials",
        "secret", "secrets.json", "config.secret",
    }

    @classmethod
    def scan_source(cls, source: str, label: str) -> SecurityScan:
        res = SecurityScan()
        for pattern, reason in cls.CERTAIN_PATTERNS:
            if re.search(pattern, source, re.DOTALL | re.IGNORECASE):
                res.score += 120
                res.reasons.append(f"{label}: {reason}")
        for pattern, reason in cls.WARN_PATTERNS:
            if re.search(pattern, source, re.DOTALL):
                res.warnings.append(f"{label}: {reason}")
        if res.score >= 120:
            res.blocked = True
            res.ban     = bool(db.settings.get("ban_on_confirmed_danger", True))
        return res

    @classmethod
    def merge(cls, items: List[SecurityScan]) -> SecurityScan:
        out = SecurityScan()
        for item in items:
            out.score    += item.score
            out.reasons.extend(item.reasons)
            out.warnings.extend(item.warnings)
            out.blocked = out.blocked or item.blocked
            out.ban     = out.ban     or item.ban
        return out

    @classmethod
    def scan_file(cls, path: str, label: Optional[str] = None) -> SecurityScan:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return cls.scan_source(f.read(), label or os.path.basename(path))
        except Exception as e:
            r = SecurityScan()
            r.warnings.append(f"تعذر فحص {label or path}: {e}")
            return r

    @classmethod
    def scan_directory(cls, dir_path: str) -> SecurityScan:
        scans: List[SecurityScan] = []
        for root, _, files in os.walk(dir_path):
            for fn in files:
                full = os.path.join(root, fn)
                rel  = os.path.relpath(full, dir_path)
                fn_lower = fn.lower()

                if fn_lower in cls.FORBIDDEN_FILENAMES:
                    r = SecurityScan(blocked=True, ban=True, score=120,
                                     reasons=[f"{rel}: ملف أسرار/مفاتيح محظور"])
                    scans.append(r)
                    continue

                ext = os.path.splitext(fn_lower)[1]
                if ext in cls.DANGEROUS_EXTENSIONS:
                    r = SecurityScan(blocked=True, ban=False, score=80,
                                     reasons=[f"{rel}: امتداد ملف خطير ({ext})"])
                    scans.append(r)
                    continue

                if fn.endswith(".py"):
                    scans.append(cls.scan_file(full, rel))

        return cls.merge(scans)

    @classmethod
    def validate_zip_members(cls, zf: zipfile.ZipFile) -> SecurityScan:
        res = SecurityScan()
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or "../" in name or name.startswith("../"):
                res.blocked = True
                res.ban     = True
                res.score  += 120
                res.reasons.append(f"مسار ZIP خطر (Zip Slip): {name}")
            fn_lower = os.path.basename(name).lower()
            if fn_lower in cls.FORBIDDEN_FILENAMES:
                res.blocked = True
                res.score  += 80
                res.reasons.append(f"ملف محظور داخل ZIP: {name}")
            ext = os.path.splitext(fn_lower)[1]
            if ext in cls.DANGEROUS_EXTENSIONS:
                res.score += 40
                res.warnings.append(f"امتداد خطير داخل ZIP: {name}")
        return res

    @classmethod
    def api_protection_scan(cls, source: str, label: str) -> SecurityScan:
        res = SecurityScan()
        TOKEN_STEAL_PATTERNS = [
            (r"(?:BOT_TOKEN|bot_token|token)\s*=\s*os\.getenv\(.*?\)\s*\n.*?requests\.(get|post)",
             "قراءة التوكن وإرساله لخادم خارجي"),
            (r"os\.environ(?:\.get)?\s*\(\s*['\"]BOT_TOKEN",
             "محاولة قراءة BOT_TOKEN من البيئة"),
            (r"sys\.argv.*?token|argparse.*?token",
             "قراءة التوكن من معاملات سطر الأوامر"),
            (r"requests\.(get|post)\s*\(.*?bot.*?token",
             "إرسال token في طلب HTTP"),
            (r"open\s*\(\s*['\"][^'\"]*\.env['\"]",
             "قراءة ملف .env مباشرة"),
            (r"telegram\.Bot\s*\(\s*token\s*=\s*['\"][0-9]{8,}:[A-Za-z0-9_-]{35,}['\"]",
             "توكن بوت مكشوف مباشرة في الكود"),
        ]
        for pattern, reason in TOKEN_STEAL_PATTERNS:
            if re.search(pattern, source, re.DOTALL | re.IGNORECASE):
                res.score += 100
                res.reasons.append(f"{label}: {reason}")

        if res.score >= 100:
            res.blocked = True
            res.ban     = bool(db.settings.get("ban_on_confirmed_danger", True))
        return res


def safe_extract_zip(zf: zipfile.ZipFile, target_dir: str) -> None:
    base = os.path.abspath(target_dir)
    for member in zf.infolist():
        dest = os.path.abspath(os.path.join(target_dir, member.filename))
        if not dest.startswith(base + os.sep) and dest != base:
            raise ValueError(f"مسار غير آمن داخل ZIP: {member.filename}")
    zf.extractall(target_dir)


# ═══════════════════════════════════════════════════════════════════════════════
# 📚  كاشف المكتبات التلقائي
# ═══════════════════════════════════════════════════════════════════════════════

class LibraryDetector:
    STDLIB: Set[str] = {
        "os","sys","re","io","ast","json","time","math","uuid","html","base64",
        "shutil","signal","random","hashlib","zipfile","asyncio","logging",
        "platform","tempfile","threading","subprocess","traceback","urllib",
        "datetime","typing","dataclasses","enum","functools","collections",
        "itertools","string","struct","pathlib","csv","sqlite3","socket",
        "ssl","ftplib","smtplib","email","http","queue","multiprocessing",
        "concurrent","abc","argparse","array","bisect","calendar","copy",
        "ctypes","decimal","difflib","fnmatch","fractions","gc","getopt",
        "getpass","glob","gzip","heapq","inspect","ipaddress","keyword",
        "linecache","locale","mmap","operator","pickle","pkgutil","pprint",
        "statistics","tarfile","textwrap","timeit","token","tokenize",
        "trace","types","unicodedata","unittest","warnings","weakref",
        "webbrowser","xml","__future__","bz2","lzma","zlib","hmac",
        "mimetypes","configparser","contextlib","dis","atexit","numbers",
        "cmath","codecs","errno","fcntl","grp","pwd","posix","resource",
        "syslog","readline","code","codeop","compileall","contextvars",
        "dbm","faulthandler","importlib","optparse","pdb","profile",
        "cProfile","pstats","pydoc","stat","venv","zipapp","zipimport",
        "zoneinfo","_thread","builtins","wave","shelve","sched","select",
        "selectors","secrets","reprlib","runpy",
    }

    NAME_MAP: Dict[str, str] = {
        "telegram": "python-telegram-bot[job-queue]",
        "telebot":  "pyTelegramBotAPI",
        "cv2":      "opencv-python",
        "PIL":      "Pillow",
        "yaml":     "PyYAML",
        "bs4":      "beautifulsoup4",
        "sklearn":  "scikit-learn",
        "dotenv":   "python-dotenv",
        "discord":  "discord.py",
        "Crypto":   "pycryptodome",
        "OpenSSL":  "pyOpenSSL",
        "MySQLdb":  "mysqlclient",
        "psycopg2": "psycopg2-binary",
        "googleapiclient": "google-api-python-client",
        "matplotlib": "matplotlib",
        "scipy":    "scipy",
        "numpy":    "numpy",
        "pandas":   "pandas",
        "requests": "requests",
        "aiohttp":  "aiohttp",
        "httpx":    "httpx",
        "flask":    "Flask",
        "django":   "Django",
        "fastapi":  "fastapi",
        "uvicorn":  "uvicorn",
        "selenium": "selenium",
        "pyrogram": "Pyrogram",
        "telethon": "Telethon",
        "schedule": "schedule",
        "redis":    "redis",
        "pymongo":  "pymongo",
        "sqlalchemy": "SQLAlchemy",
        "pydantic": "pydantic",
        "aiogram":  "aiogram",
        "tweepy":   "tweepy",
        "paramiko": "paramiko",
        "cryptography": "cryptography",
        "pygame":   "pygame",
        "aiosqlite":"aiosqlite",
        "motor":    "motor",
        "aiomysql": "aiomysql",
        "tortoise": "tortoise-orm",
        "loguru":   "loguru",
        "rich":     "rich",
        "click":    "click",
        "typer":    "typer",
        "starlette":"starlette",
        "sanic":    "sanic",
        "aiofiles": "aiofiles",
        "anyio":    "anyio",
        "trio":     "trio",
        "psutil":   "psutil",
        "jinja2":   "Jinja2",
        "attrs":    "attrs",
        "celery":   "celery",
        "kombu":    "kombu",
        "pika":     "pika",
        "apscheduler": "APScheduler",
        "boto3":    "boto3",
        "openai":   "openai",
        "anthropic":"anthropic",
        "transformers": "transformers",
        "torch":    "torch",
        "tensorflow":"tensorflow",
        "keras":    "keras",
        "skimage":  "scikit-image",
    }

    @classmethod
    def detect_from_source(cls, source: str) -> List[str]:
        names: Set[str] = set()
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        names.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.level == 0:
                        names.add(node.module.split(".")[0])
        except:
            for line in source.splitlines():
                m1 = re.match(r"\s*import\s+([\w\.]+)", line)
                m2 = re.match(r"\s*from\s+([\w\.]+)\s+import\s+", line)
                if m1: names.add(m1.group(1).split(".")[0])
                elif m2: names.add(m2.group(1).split(".")[0])
        external  = sorted([n for n in names if n and n not in cls.STDLIB])
        pip_names = [cls.NAME_MAP.get(n, n) for n in external]
        seen: Set[str] = set()
        out: List[str] = []
        for n in pip_names:
            if n not in seen:
                seen.add(n)
                out.append(n)
        return out

    @classmethod
    def detect_from_file(cls, path: str) -> List[str]:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return cls.detect_from_source(f.read())
        except: return []

    @classmethod
    def detect_from_directory(cls, dir_path: str) -> List[str]:
        all_libs: Set[str] = set()
        for root, _, files in os.walk(dir_path):
            for fn in files:
                if fn.endswith(".py"):
                    all_libs.update(cls.detect_from_file(os.path.join(root, fn)))
        req = os.path.join(dir_path, "requirements.txt")
        if os.path.exists(req):
            try:
                with open(req, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            pkg = re.split(r"[<>=!~ ]", line)[0]
                            if pkg: all_libs.add(pkg)
            except: pass
        return sorted(all_libs)


def write_requirements(dir_path: str, libs: List[str]) -> str:
    req_path = os.path.join(dir_path, "requirements.txt")
    existing: Set[str] = set()
    if os.path.exists(req_path):
        try:
            with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        existing.add(re.split(r"[<>=!~ ]", line)[0])
        except: pass
    merged = sorted(existing.union(libs))
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated by PyHost Pro Ultra\n")
        for lib in merged: f.write(f"{lib}\n")
    return req_path


def make_zip_of_dir(src_dir: str, out_zip: str) -> str:
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for fn in files:
                full = os.path.join(root, fn)
                rel  = os.path.relpath(full, src_dir)
                zf.write(full, rel)
    return out_zip


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠  مدير العمليات
# ═══════════════════════════════════════════════════════════════════════════════

class ProcessManager:
    def __init__(self) -> None:
        self._procs:   Dict[str, subprocess.Popen] = {}
        self._logs:    Dict[str, deque]             = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._start_times: Dict[str, float]        = {}
        self._lock = threading.RLock()

    def install_libs(self, libs: List[str], cwd: str) -> Tuple[bool, str]:
        if not libs: return True, "لا توجد مكتبات للتثبيت."
        import importlib.util as _il
        filtered: List[str] = []
        skipped:  List[str] = []
        for lib in libs:
            base = re.split(r"[<>=!~\[ ]", lib)[0].strip()
            if not base: continue
            if base in LibraryDetector.STDLIB:
                skipped.append(base); continue
            try:
                import_name = next(
                    (k for k, v in LibraryDetector.NAME_MAP.items()
                     if v.split("[")[0].lower() == base.lower()),
                    base
                )
                if _il.find_spec(import_name) is not None:
                    if import_name == "telegram":
                        try:
                            from telegram import Update, Chat
                        except Exception:
                            filtered.append(lib)
                            continue
                    skipped.append(base)
                    continue
            except Exception:
                pass
            filtered.append(lib)
        if not filtered:
            return True, f"كل المكتبات قياسية/مثبتة. تخطّي: {', '.join(skipped) or '—'}"
        try:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade",
                   "--no-cache-dir", "--disable-pip-version-check", *filtered]
            proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                                  timeout=INSTALL_TIMEOUT_SECONDS, check=False)
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if skipped: out = f"(تخطّي قياسية: {', '.join(skipped)})\n" + out
            return (proc.returncode == 0), out[-4000:]
        except subprocess.TimeoutExpired:
            return False, f"تجاوز مهلة التثبيت ({INSTALL_TIMEOUT_SECONDS}ث)"
        except Exception as e:
            return False, f"خطأ بالتثبيت: {e}"

    def start(self, file_id: str, work_dir: str, entry: str,
              env_extra: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
        with self._lock:
            if file_id in self._procs and self._procs[file_id].poll() is None:
                return False, "العملية تعمل بالفعل."
            entry_path = os.path.join(work_dir, entry)
            if not os.path.exists(entry_path):
                return False, f"ملف الدخول غير موجود: {entry}"
            try:
                env = os.environ.copy()
                if env_extra: env.update(env_extra)
                proc = subprocess.Popen(
                    [sys.executable, "-u", entry], cwd=work_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, env=env,
                )
                self._procs[file_id]       = proc
                self._logs[file_id]        = deque(maxlen=int(db.settings.get("log_runtime_lines", 300)))
                self._start_times[file_id] = time.time()
                t = threading.Thread(target=self._reader, args=(file_id,), daemon=True)
                self._threads[file_id] = t
                t.start()
                return True, f"PID={proc.pid}"
            except Exception as e:
                return False, f"فشل التشغيل: {e}"

    def _reader(self, file_id: str) -> None:
        proc = self._procs.get(file_id)
        if not proc or not proc.stdout: return
        try:
            for line in proc.stdout:
                self._logs[file_id].append(line.rstrip("\n"))
        except Exception as e:
            logger.warning("reader error %s: %s", file_id, e)

    def stop(self, file_id: str) -> Tuple[bool, str]:
        with self._lock:
            proc = self._procs.get(file_id)
            if not proc: return False, "لا توجد عملية."
            if proc.poll() is not None: return False, "العملية متوقفة بالفعل."
            try:
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: proc.kill()
                hf = db.get_file(file_id)
                if hf and file_id in self._start_times:
                    hf.total_runtime_seconds += int(time.time() - self._start_times[file_id])
                    db.add_file(hf)
                self._start_times.pop(file_id, None)
                return True, "تم الإيقاف."
            except Exception as e:
                return False, f"فشل الإيقاف: {e}"

    def stop_all_for_user(self, user_id: int) -> int:
        count = 0
        for fid in list(self._procs.keys()):
            hf = db.get_file(fid)
            if hf and hf.owner_id == user_id and self.is_running(fid):
                self.stop(fid); count += 1
        return count

    def stop_all(self) -> int:
        count = 0
        for fid in list(self._procs.keys()):
            if self.is_running(fid):
                self.stop(fid); count += 1
        return count

    def restart(self, file_id: str) -> Tuple[bool, str]:
        hf = db.get_file(file_id)
        if not hf: return False, "الملف غير موجود."
        self.stop(file_id)
        time.sleep(0.5)
        work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, file_id)
        return self.start(file_id, work_dir, hf.entry_file or hf.file_name)

    def is_running(self, file_id: str) -> bool:
        proc = self._procs.get(file_id)
        return bool(proc and proc.poll() is None)

    def pid(self, file_id: str) -> Optional[int]:
        proc = self._procs.get(file_id)
        return proc.pid if proc else None

    def uptime(self, file_id: str) -> str:
        if not self.is_running(file_id): return "—"
        start = self._start_times.get(file_id)
        if not start: return "—"
        sec = int(time.time() - start)
        h, r = divmod(sec, 3600); m, s = divmod(r, 60)
        return f"{h}س {m}د {s}ث" if h else f"{m}د {s}ث"

    def tail_log(self, file_id: str, n: int = 40) -> str:
        log = self._logs.get(file_id)
        if not log: return "(لا يوجد سجل)"
        lines = list(log)[-n:]
        return "\n".join(lines) if lines else "(سجل فارغ)"

    def export_log(self, file_id: str) -> bytes:
        log = self._logs.get(file_id)
        if not log: return "(لا يوجد سجل)".encode("utf-8")
        return "\n".join(list(log)).encode("utf-8", errors="replace")

    def user_running_count(self, user_id: int) -> int:
        return sum(1 for fid in self._procs
                   if (hf := db.get_file(fid)) and hf.owner_id == user_id and self.is_running(fid))

    def all_running(self) -> List[str]:
        return [fid for fid in self._procs if self.is_running(fid)]

    def running_info(self) -> List[Dict[str, Any]]:
        result = []
        for fid in self.all_running():
            hf = db.get_file(fid)
            result.append({
                "file_id": fid, "file_name": hf.file_name if hf else "—",
                "owner_id": hf.owner_id if hf else 0,
                "pid": self.pid(fid), "uptime": self.uptime(fid),
            })
        return result


pm = ProcessManager()


# ═══════════════════════════════════════════════════════════════════════════════
# 📣  ديكوريترات الحماية
# ═══════════════════════════════════════════════════════════════════════════════

def admin_only(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *a, **kw):
        uid = update.effective_user.id if update.effective_user else 0
        if not is_admin(uid):
            await _reply_anywhere(update, f"{Icon.BAN} هذا الإجراء للمشرفين فقط.")
            return
        return await func(update, context, *a, **kw)
    return wrapper


def check_banned(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *a, **kw):
        uid = update.effective_user.id if update.effective_user else 0
        if not uid: return
        if is_admin_immortal(uid):
            return await func(update, context, *a, **kw)
        u = db.get_user(uid)
        if u.is_banned:
            if u.ban_until:
                try:
                    if datetime.fromisoformat(u.ban_until) < datetime.now():
                        u.is_banned  = False
                        u.ban_reason = ""
                        u.ban_until  = ""
                        db.update_user(u)
                        return await func(update, context, *a, **kw)
                except: pass
            txt = f"{Icon.BAN} أنت محظور من استخدام البوت."
            if u.ban_reason: txt += f"\nالسبب: {escape_html(u.ban_reason)}"
            if u.ban_until:  txt += f"\nيستمر حتى: {format_dt(u.ban_until)}"
            await _reply_anywhere(update, txt)
            return
        return await func(update, context, *a, **kw)
    return wrapper


def maintenance_gate(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *a, **kw):
        uid = update.effective_user.id if update.effective_user else 0
        if db.settings.get("maintenance_mode") and not is_admin(uid):
            await _reply_anywhere(update, f"{Icon.TOOLS} البوت في وضع الصيانة. عُد بعد قليل.")
            return
        return await func(update, context, *a, **kw)
    return wrapper


def rate_limit(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *a, **kw):
        uid = update.effective_user.id if update.effective_user else 0
        if not rate_limiter.is_allowed(uid):
            u = db.users.get(uid)
            if u: u.rate_violations += 1; db.update_user(u, save=False)
            try: await _reply_anywhere(update, f"{Icon.WARN} أنت تُرسل بسرعة كبيرة. انتظر قليلاً.")
            except: pass
            return
        return await func(update, context, *a, **kw)
    return wrapper


async def _reply_anywhere(update: Update, text: str, **kw) -> None:
    try:
        if update.callback_query:
            try: await update.callback_query.answer()
            except: pass
            await update.callback_query.message.reply_text(text, **kw)
        elif update.message:
            await update.message.reply_text(text, **kw)
        elif update.effective_chat:
            await update.effective_chat.send_message(text, **kw)
    except Exception as e:
        logger.warning("reply_anywhere failed: %s", e)


async def _edit_or_send(update: Update, text: str,
                         kb: Optional[InlineKeyboardMarkup] = None) -> None:
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, reply_markup=kb, parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        else:
            await update.message.reply_text(
                text, reply_markup=kb, parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            logger.warning("_edit_or_send error: %s", e)
    except Exception as e:
        logger.warning("_edit_or_send error: %s", e)


async def send_named_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              name: str) -> None:
    sid = sticker_id(name)
    if not sid: return
    try:
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sid)
    except Exception as e:
        logger.debug("sticker %s failed: %s", name, e)


async def edit_progress(msg: Message, title: str, percent: int, detail: str = "") -> None:
    try:
        text = f"{Icon.LIGHT} <b>{escape_html(title)}</b>\n{progress_bar(percent)} <b>{percent}%</b>"
        if detail: text += f"\n{escape_html(detail)}"
        await msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "not modified" not in str(e).lower(): logger.debug("progress edit failed: %s", e)
    except: pass


async def run_blocking_with_progress(msg: Message, title: str,
                                      fn: Callable, *args) -> Any:
    task = asyncio.create_task(asyncio.to_thread(fn, *args))
    pcts = [15, 30, 50, 70, 85]
    idx  = 0
    while not task.done():
        if idx < len(pcts):
            await edit_progress(msg, title, pcts[idx]); idx += 1
        await asyncio.sleep(2)
    return task.result()


# ═══════════════════════════════════════════════════════════════════════════════
# 📣  نظام الاشتراك الإجباري
# ═══════════════════════════════════════════════════════════════════════════════

async def check_subscription(user_id: int, bot) -> Tuple[bool, List[Channel]]:
    if not db.settings.get("require_subscription", False): return True, []
    channels = db.all_channels(enabled_only=True)
    if not channels: return True, []
    missing: List[Channel] = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch.chat_id, user_id=user_id)
            ok_statuses = {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
            if getattr(member, "status", None) not in ok_statuses:
                missing.append(ch)
        except: missing.append(ch)
    return (len(missing) == 0), missing


def subscription_keyboard(missing: List[Channel]) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for ch in missing:
        title = ch.title or ch.chat_id
        url   = ch.invite_link
        if not url and ch.chat_id.startswith("@"):
            url = f"https://t.me/{ch.chat_id[1:]}"
        if url:
            rows.append([btn_url_primary(f"{Icon.CHANNEL} {shorten(title, 28)}", url)])
        else:
            rows.append([btn_noop(f"{Icon.CHANNEL} {shorten(title, 28)}")])
    rows.append([btn_success("تحققت — تابع", "check_sub")])
    return InlineKeyboardMarkup(rows)


async def enforce_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid = update.effective_user.id
    if is_admin(uid): return True
    ok, missing = await check_subscription(uid, context.bot)
    if ok: return True
    text = (
        f"{Icon.LOCK} <b>الاشتراك إجباري</b>\n\n"
        f"للاستمرار يجب الاشتراك في القنوات التالية ثم اضغط «تحققت»:"
    )
    kb = subscription_keyboard(missing)
    if update.callback_query:
        try: await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except: await update.callback_query.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# ⌨️  بناء لوحات الأزرار
# ═══════════════════════════════════════════════════════════════════════════════

def kb_main_menu(user_id: int) -> InlineKeyboardMarkup:
    rows = [
        [btn_success("📤  رفع ملف جديد",                          "menu:upload")],
        [btn_primary("📁  ملفاتي المرفوعة",                       "menu:myfiles")],
        [btn_primary("💎  نقاطي",                                  "menu:points"),
         btn_success("🎁  ادعُ أصدقاءك",                          "menu:invite")],
        [btn_success("⭐  شراء نقاط",                              "menu:buy")],
        [btn_primary("📊  إحصائياتي",                              "menu:stats"),
         btn_success("🏆  المتصدرون",                              "menu:leaderboard")],
        [btn_success("💻  كود نقاط",                               "menu:redeem"),
         btn_primary("💬  الدعم",                                   "menu:support")],
        [btn_primary("⚙️  الإعدادات",                              "menu:settings"),
         btn_success("🛡  الحماية",                                 "menu:security")],
        [btn_primary("ℹ️  عن البوت",                               "menu:about")],
    ]
    if user_id in ADMIN_IDS:
        rows.append([btn_danger("👑  لوحة الإدارة",                "admin:panel")])
    return InlineKeyboardMarkup(rows)


def kb_back(target: str = "menu:main", label: Optional[str] = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[btn_primary(label or "⬅️ رجوع", target)]])


def kb_confirm(yes_cb: str, no_cb: str = "menu:main",
               yes_label: Optional[str] = None, no_label: Optional[str] = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        btn_success(yes_label or "✅ نعم، تأكيد", yes_cb),
        btn_danger (no_label  or "❌ لا، إلغاء",  no_cb),
    ]])


def kb_admin_panel() -> InlineKeyboardMarkup:
    require_approval = db.settings.get("require_approval", False)
    security_enabled = db.settings.get("security_enabled", False)
    pending_count = len(db.get_pending_files())
    
    rows = [
        [btn_toggle("✅ الموافقة", "admin:toggle_approval", require_approval),
         btn_toggle("🛡 الحماية",  "admin:toggle_security", security_enabled)],
        [btn_primary(f"📋 الملفات قيد المراجعة ({pending_count})", "admin:pending")],
        [btn_primary ("📊  إحصائيات البوت",                        "admin:stats")],
        [btn_primary ("👥  المستخدمون",                             "admin:users"),
         btn_success ("🔍  بحث مستخدم",                            "admin:search")],
        [btn_primary ("📁  الملفات",                                "admin:files"),
         btn_primary ("📺  العمليات الجارية",                       "admin:procs")],
        [btn_success ("💎  إضافة نقاط",                            "admin:addpts"),
         btn_danger  ("➖  خصم نقاط",                              "admin:subpts")],
        [btn_success ("💻  أكواد النقاط",                           "admin:codes")],
        [btn_danger  ("🚫  حظر مستخدم",                            "admin:ban"),
         btn_success ("🟢  فك الحظر",                              "admin:unban")],
        [btn_success ("💫  ترقية بريميوم",                          "admin:premium")],
        [btn_primary ("📣  القنوات",                                "admin:channels"),
         btn_success ("📢  إرسال بث جماعي",                        "admin:broadcast")],
        [btn_primary ("📋  سجل البث",                               "admin:bhist"),
         btn_primary ("🏆  المتصدرون",                              "admin:leaderboard")],
        [btn_primary ("⚙️  الإعدادات",                              "admin:settings"),
         btn_primary ("🖥  معلومات النظام",                         "admin:sysinfo")],
        [btn_success ("📅  الجدولة",                                "admin:schedule"),
         btn_success ("🧠  تقارير AI",                              "admin:ai_reports")],
        [btn_success ("📥  نسخة احتياطية",                          "admin:backup"),
         btn_primary ("📤  استعادة نسخة",                           "admin:restore")],
        [btn_success ("🛡  مركز الحماية",                            "admin:security"),
         btn_danger  ("🔇  كلمات محظورة",                           "admin:bwords")],
        [btn_primary ("🚨  سجل النشاط",                             "admin:activity"),
         btn_danger  ("🛠  وضع الصيانة",                            "admin:maint")],
        [btn_danger  ("⏹  إيقاف جميع العمليات",                    "admin:stop_all")],
        [btn_primary ("🏠  القائمة الرئيسية",                       "menu:main")],
    ]
    return InlineKeyboardMarkup(rows)


def kb_buy_points() -> InlineKeyboardMarkup:
    packs = [(10, 15), (25, 35), (50, 65), (100, 120), (250, 280), (500, 540)]
    styles = [btn_primary, btn_success, btn_primary, btn_success, btn_danger, btn_danger]
    emojis = ["🔹", "⭐", "🔷", "💎", "🔥", "👑"]
    rows: List[List[InlineKeyboardButton]] = []
    row:  List[InlineKeyboardButton]       = []
    for i, (pts, stars) in enumerate(packs):
        fn  = styles[i % len(styles)]
        em  = emojis[i % len(emojis)]
        row.append(fn(f"{em} {pts} نقطة · {stars} ⭐", f"buy:{pts}:{stars}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([btn_primary("⬅️ رجوع", "menu:main")])
    return InlineKeyboardMarkup(rows)


def kb_file_actions(file_id: str, is_owner: bool, running: bool,
                    is_admin_view: bool = False) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    if is_owner or is_admin_view:
        if running:
            rows.append([
                btn_danger ("⏹  إيقاف",                   f"file:stop:{file_id}"),
                btn_primary("🔄  إعادة تشغيل",             f"file:restart:{file_id}"),
            ])
        else:
            rows.append([
                btn_success("▶️  تشغيل الملف",             f"file:run:{file_id}"),
                btn_primary("📥  تحميل ZIP",               f"file:zip:{file_id}"),
            ])
        rows.append([
            btn_primary ("📺  السجل المباشر",              f"file:log:{file_id}"),
            btn_success ("💡  تثبيت المكتبات",             f"file:install:{file_id}"),
        ])
        rows.append([
            btn_primary ("🖥️  ترمنال المشروع",             f"file:terminal:{file_id}"),
        ])
        rows.append([
            btn_success ("🧠  تحليل AI",                   f"file:ai:{file_id}"),
            btn_primary ("✏️  تعديل الوصف",               f"file:desc:{file_id}"),
        ])
        rows.append([
            btn_success ("🔁  إقلاع تلقائي",              f"file:auto:{file_id}"),
            btn_primary ("📤  تصدير السجل",                f"file:export_log:{file_id}"),
        ])
        rows.append([
            btn_success ("🔗  رابط مشاركة",               f"file:share:{file_id}"),
            btn_primary ("🌐  تغيير العمومية",             f"file:public:{file_id}"),
        ])
        rows.append([
            btn_danger  ("🗑  حذف الملف",                  f"file:del:{file_id}"),
        ])
        if is_admin_view:
            hf = db.get_file(file_id)
            if hf:
                rows.append([btn_primary("👤  صاحب الملف", f"admin:user:{hf.owner_id}")])
    else:
        rows.append([btn_primary("📥  تحميل ZIP", f"file:zip:{file_id}")])
    rows.append([btn_primary("⬅️  ملفاتي", "menu:myfiles")])
    return InlineKeyboardMarkup(rows)


def kb_paginated(items: List[Tuple[str, str]], page: int, page_size: int,
                 base_cb: str, back_cb: str = "menu:main",
                 item_style: str = "primary") -> InlineKeyboardMarkup:
    total  = len(items)
    pages  = max(1, math.ceil(total / page_size))
    page   = max(0, min(page, pages - 1))
    start  = page * page_size
    end    = min(start + page_size, total)
    rows: List[List[InlineKeyboardButton]] = []
    style_fn = {"primary": btn_primary, "success": btn_success,
                "danger": btn_danger, "warning": btn_warning}.get(item_style, btn_primary)
    for label, cb in items[start:end]:
        rows.append([style_fn(label, cb)])
    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(btn_secondary(f"{Icon.PREV} السابق", f"{base_cb}:{page-1}"))
    nav.append(btn_noop(f"صفحة {page+1}/{pages}"))
    if page < pages - 1:
        nav.append(btn_secondary(f"التالي {Icon.NEXT}", f"{base_cb}:{page+1}"))
    if nav: rows.append(nav)
    rows.append([btn_secondary(f"{Icon.BACK} رجوع", back_cb)])
    return InlineKeyboardMarkup(rows)


def kb_settings_admin() -> InlineKeyboardMarkup:
    s = db.settings
    def btgl(label: str, key: str) -> InlineKeyboardButton:
        return btn_toggle(label, f"adminset:toggle:{key}", bool(s.get(key)))
    rows = [
        [btgl("وضع الصيانة",          "maintenance_mode")],
        [btgl("الاشتراك إجباري",       "require_subscription")],
        [btgl("تثبيت المكتبات تلقائياً", "auto_install_libs")],
        [btgl("تشغيل تلقائي بعد الرفع", "auto_run_after_upload")],
        [btgl("إقلاع تلقائي افتراضياً", "auto_restart_default")],
        [btgl("ZIP عند فشل التشغيل",   "send_zip_if_run_fails")],
        [btgl("حماية الاستضافة",       "strict_hosting_security")],
        [btgl("حماية API متقدمة",      "api_protection_enabled")],
        [btgl("حظر عند خطر مؤكد",      "ban_on_confirmed_danger")],
        [btgl("تحليل AI عند الرفع",    "ai_analysis_enabled")],
        [btgl("الرفع المجاني الأول",   "first_upload_free")],
        [btgl("ملفات عامة مفعّلة",     "public_files_enabled")],
        [btgl("إشعار دخول جديد",       "notify_admin_on_join")],
        [btgl("إشعار رفع جديد",        "notify_admin_on_upload")],
        [btgl("Rate Limit مفعّل",      "rate_limit_enabled")],
        [btgl("Leaderboard مفعّل",     "leaderboard_enabled")],
        [btgl("الجدولة مفعّلة",        "schedule_enabled")],
        [btgl("حماية مطلقة للمشرف",    "admin_immortal")],
        [btn_warning(f"سعر الرفع: {s.get('upload_cost',1)} نقطة",       "adminset:num:upload_cost"),
         btn_warning(f"نقاط الدعوة: {s.get('points_per_invite',2)}",    "adminset:num:points_per_invite")],
        [btn_warning(f"نجوم/10نقاط: {s.get('stars_per_10_points',15)}", "adminset:num:stars_per_10_points"),
         btn_warning(f"حجم/ميجا: {s.get('max_file_size_mb',50)}",       "adminset:num:max_file_size_mb")],
        [btn_warning(f"عمليات/مستخدم: {s.get('max_processes_per_user',3)}", "adminset:num:max_processes_per_user"),
         btn_warning(f"مهلة التشغيل: {s.get('run_timeout_seconds',0)}",     "adminset:num:run_timeout_seconds")],
        [btn_warning(f"حد Rate: {s.get('rate_limit_messages',10)} رسالة",   "adminset:num:rate_limit_messages"),
         btn_warning(f"نافذة Rate: {s.get('rate_limit_window',10)}ث",       "adminset:num:rate_limit_window")],
        [btn_primary(f"{Icon.EDIT} تعديل رسالة الترحيب",     "adminset:text:welcome_message")],
        [btn_primary(f"{Icon.SUPPORT} تعديل يوزر الدعم",     "adminset:text:support_username")],
        [btn_secondary(f"{Icon.BACK} لوحة الإدارة",          "admin:panel")],
    ]
    return InlineKeyboardMarkup(rows)


def kb_channels_admin() -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for ch in db.all_channels():
        title = ch.title or ch.chat_id
        rows.append([
            btn_toggle(shorten(title, 22), f"chan:toggle:{ch.chat_id}", ch.enabled),
            btn_danger(f"🗑 حذف", f"chan:del:{ch.chat_id}"),
        ])
    rows.append([
        btn_success("➕ إضافة قناة", "chan:add"),
        btn_primary("🔄 تحديث",      "admin:channels"),
    ])
    rows.append([btn_primary("⬅️ لوحة الإدارة", "admin:panel")])
    return InlineKeyboardMarkup(rows)


def kb_settings_user(u: User) -> InlineKeyboardMarkup:
    rows = [
        [btn_toggle("🔔 الإشعارات", "userset:toggle:notif", u.notifications_enabled)],
        [btn_primary("🔗 رابط دعوتي",        "menu:invite")],
        [btn_success("📥 تصدير بياناتي",      "userset:export")],
        [btn_primary("🏠 الرئيسية",           "menu:main")],
    ]
    return InlineKeyboardMarkup(rows)


def support_rows(back_cb: str = "menu:main") -> List[List[InlineKeyboardButton]]:
    sup = db.settings.get("support_username") or SUPPORT_USERNAME
    rows: List[List[InlineKeyboardButton]] = []
    if sup:
        rows.append([btn_url_success(f"💬 تكلم مع الدعم", f"https://t.me/{sup}")])
    rows.append([btn_url_primary(f"👑 المطور @{DEVELOPER_USERNAME}", DEVELOPER_LINK)])
    rows.append([btn_primary("⬅️ رجوع", back_cb)])
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# 📜  نصوص العرض
# ═══════════════════════════════════════════════════════════════════════════════

def text_welcome(u: User, bot_username: str) -> str:
    premium_badge = f" {Icon.PREMIUM}" if u.is_premium else ""
    admin_badge   = f" {Icon.CROWN}"   if is_admin(u.user_id) else ""
    return (
        f"{Icon.FIRE} <b>{db.settings.get('welcome_message')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{Icon.USER} الاسم: <b>{escape_html(u.first_name or '—')}</b>{premium_badge}{admin_badge}\n"
        f"المعرّف: <code>{u.user_id}</code>\n"
        f"{Icon.DIAMOND} نقاطك: <b>{u.points}</b>\n"
        f"{Icon.GIFT} رفع مجاني متبقي: <b>{u.free_uploads}</b>\n"
        f"{Icon.UPLOAD} ملفاتك: <b>{len(u.files)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{Icon.LINK} رابط دعوتك:\n"
        f"<code>https://t.me/{bot_username}?start=ref{u.user_id}</code>"
    )


def text_about() -> str:
    py      = sys.version.split()[0]
    running = len(pm.all_running())
    return (
        f"{Icon.BOT} <b>{BOT_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الإصدار: <b>{BOT_VERSION}</b>\n"
        f"Python:  <code>{py}</code>\n"
        f"النظام:  <code>{platform.system()} {platform.release()}</code>\n"
        f"المستخدمون: <b>{len(db.users)}</b>\n"
        f"الملفات:    <b>{len(db.files)}</b>\n"
        f"يعمل الآن:  <b>{running}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{Icon.AI} ذكاء اصطناعي يحلل الكود | {Icon.API_PROTECT} حماية API متقدمة\n"
        f"{Icon.SHIELD} حماية مطلقة للمشرف | Inline Keyboard style | Rate Limit\n"
        f"{Icon.ROCKET} Leaderboard | Premium | جدولة | مراقبة موارد\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{Icon.CROWN} <b>المطور:</b> <a href='{DEVELOPER_LINK}'>{DEVELOPER_USERNAME}</a>"
    )


def text_admin_stats() -> str:
    s       = db.stats
    running = len(pm.all_running())
    premium = len(db.get_premium_users())
    banned  = sum(1 for u in db.all_users() if u.is_banned)
    new7    = len(db.get_new_users(7))
    today   = datetime.now().strftime("%Y-%m-%d")
    daily   = len(db.stats.get("daily_active", {}).get(today, []))
    pending = len(db.get_pending_files())
    return (
        f"{Icon.STATS} <b>إحصائيات البوت</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"المستخدمون:       <b>{len(db.users)}</b>\n"
        f"  نشطون اليوم:    <b>{daily}</b>\n"
        f"  جدد (7 أيام):   <b>{new7}</b>\n"
        f"  بريميوم:        <b>{premium}</b>\n"
        f"  محظورون:        <b>{banned}</b>\n"
        f"الملفات:          <b>{len(db.files)}</b>\n"
        f"  قيد المراجعة:   <b>{pending}</b>\n"
        f"العمليات الحيّة: <b>{running}</b>\n"
        f"إجمالي التشغيل:  <b>{s.get('total_runs',0)}</b>\n"
        f"إجمالي التحميلات:<b>{s.get('total_downloads',0)}</b>\n"
        f"النقاط الممنوحة: <b>{s.get('total_points_given',0)}</b>\n"
        f"نجوم مستلمة:     <b>{s.get('total_stars_received',0)}</b>\n"
        f"إجمالي البث:     <b>{s.get('total_broadcasts',0)}</b>\n"
        f"تاريخ البدء:     <b>{format_dt(s.get('created_at',''))}</b>"
    )


def text_leaderboard(category: str = "points") -> str:
    titles  = {"points": f"{Icon.DIAMOND} ترتيب النقاط",
               "uploads": f"{Icon.UPLOAD} ترتيب الرفع",
               "invites": f"{Icon.GIFT} ترتيب الدعوات"}
    getters = {"points":  lambda u: u.points,
               "uploads": lambda u: u.total_uploads,
               "invites": lambda u: len(u.invited_users)}
    medals  = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    title   = titles.get(category, titles["points"])
    getter  = getters.get(category, getters["points"])
    top     = sorted(db.all_users(), key=getter, reverse=True)[:10]
    lines   = [f"{Icon.TROPHY} <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for i, u in enumerate(top):
        name  = escape_html(u.first_name or str(u.user_id))
        val   = getter(u)
        badge = f" {Icon.PREMIUM}" if u.is_premium else ""
        lines.append(f"{medals[i]}. <b>{name}</b>{badge} — <b>{val}</b>")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 🚪  معالجات الأوامر
# ═══════════════════════════════════════════════════════════════════════════════

ST_AWAIT_UPLOAD       = "awaiting_upload"
ST_AWAIT_BROADCAST    = "awaiting_broadcast"
ST_AWAIT_ADDPTS_ID    = "awaiting_addpts_id"
ST_AWAIT_ADDPTS_AMT   = "awaiting_addpts_amt"
ST_AWAIT_SUBPTS_ID    = "awaiting_subpts_id"
ST_AWAIT_SUBPTS_AMT   = "awaiting_subpts_amt"
ST_AWAIT_BAN_ID       = "awaiting_ban_id"
ST_AWAIT_BAN_REASON   = "awaiting_ban_reason"
ST_AWAIT_UNBAN_ID     = "awaiting_unban_id"
ST_AWAIT_SEARCH       = "awaiting_search"
ST_AWAIT_CHAN_ADD      = "awaiting_channel"
ST_AWAIT_BWORD        = "awaiting_bword"
ST_AWAIT_SET_NUM      = "awaiting_set_num"
ST_AWAIT_SET_TEXT     = "awaiting_set_text"
ST_AWAIT_FILE_DESC    = "awaiting_file_desc"
ST_AWAIT_CODE_REDEEM  = "awaiting_code_redeem"
ST_AWAIT_CODE_CREATE  = "awaiting_code_create"
ST_AWAIT_PREMIUM_UID  = "awaiting_premium_uid"
ST_AWAIT_PREMIUM_DAYS = "awaiting_premium_days"
ST_AWAIT_NOTE         = "awaiting_note_uid"
ST_AWAIT_BAN_DURATION = "awaiting_ban_duration"
ST_AWAIT_SCHEDULE_FID = "awaiting_schedule_fid"
ST_AWAIT_SCHEDULE_TIME= "awaiting_schedule_time"
ST_AWAIT_TERMINAL   = "awaiting_terminal_command"


def clear_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    for k in list(context.user_data.keys()):
        if k.startswith("awaiting_") or k.startswith("state_"):
            context.user_data.pop(k, None)


@maintenance_gate
@check_banned
@rate_limit
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new_user = user.id not in db.users
    u = db.get_user(user.id, username=user.username or "",
                    first_name=user.first_name or "", last_name=user.last_name or "")
    u.login_count += 1
    db.record_daily_active(user.id)

    args = context.args or []
    if args and args[0].startswith("ref"):
        try: inviter_id = int(args[0][3:])
        except: inviter_id = 0
        if inviter_id and inviter_id != u.user_id and not u.invited_by:
            inviter = db.users.get(inviter_id)
            if inviter:
                u.invited_by = inviter_id
                if u.user_id not in inviter.invited_users:
                    inviter.invited_users.append(u.user_id)
                if u.user_id not in inviter.invite_reward_given_for:
                    inviter.invite_reward_given_for.append(u.user_id)
                    pts = int(db.settings.get("points_per_invite", 2))
                    grant_points(inviter, pts, "invite", note=f"invited {u.user_id}")
                    try:
                        await context.bot.send_message(
                            inviter_id, f"{Icon.GIFT} مبروك! انضم صديق جديد ← +{pts} نقطة.")
                    except: pass
                db.update_user(inviter)

    if args and args[0].startswith("file_"):
        fid = args[0][5:]
        hf  = db.get_file(fid)
        if hf and hf.is_public:
            await _send_project_zip_direct(update, context, hf, "تحميل عبر رابط")
            db.update_user(u)
            return

    db.update_user(u)
    if not await enforce_subscription(update, context): return
    await send_named_sticker(update, context, "login_success")
    me   = await context.bot.get_me()
    await update.message.reply_text(
        text_welcome(u, me.username),
        reply_markup=kb_main_menu(u.user_id),
        parse_mode=ParseMode.HTML,
    )
    if is_new_user and db.settings.get("notify_admin_on_join", True):
        await _notify_admins_new_user(context, u)


@maintenance_gate
@check_banned
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        f"{Icon.INFO} <b>دليل سريع — {BOT_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• اضغط زر «رفع ملف» وأرسل ملف .py أو .zip\n"
        f"• بعد الرفع: يحلل الذكاء الاصطناعي كودك تلقائياً\n"
        f"• يفحص البوت الملفات أمنياً قبل التشغيل\n"
        f"• شغّل / أوقف / حمّل / احذف من أزرار الملف\n"
        f"• اشترِ نقاطاً بالنجوم أو ادعُ أصدقاءك لتربح\n"
        f"• {Icon.CROWN} المشرفون: اضغط «لوحة الإدارة» للتحكم الكامل\n"
    )
    await update.message.reply_text(
        txt, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} الرئيسية", "menu:main")]]),
    )


async def _notify_admins_new_user(context: ContextTypes.DEFAULT_TYPE, u: User) -> None:
    text = (
        f"{Icon.NEW} <b>مستخدم جديد انضم!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"ID:      <code>{u.user_id}</code>\n"
        f"الاسم:   <b>{escape_html(u.first_name or '—')}</b>\n"
        f"اللقب:   {escape_html(u.last_name or '—')}\n"
        f"يوزرنيم: @{escape_html(u.username or '—')}\n"
        f"الانضمام: {format_dt(u.join_date)}\n"
        f"دُعي بواسطة: <code>{u.invited_by or '—'}</code>"
    )
    kb = InlineKeyboardMarkup([
        [btn_primary(f"{Icon.USER} تفاصيله",    f"admin:user:{u.user_id}"),
         btn_primary(f"{Icon.FOLDER} ملفاته",   f"admin:user_files:{u.user_id}")],
        [btn_success(f"{Icon.DIAMOND} أضف نقاط", f"admin:addpts_user:{u.user_id}"),
         btn_danger (f"{Icon.BAN} حظر",          f"admin:ban_user:{u.user_id}")],
    ])
    for adm in ADMIN_IDS:
        try:
            await context.bot.send_message(adm, text, parse_mode=ParseMode.HTML, reply_markup=kb)
        except: pass


# ═══════════════════════════════════════════════════════════════════════════════
# 💎  محرك النقاط
# ═══════════════════════════════════════════════════════════════════════════════

ALLOWED_POINT_SOURCES = {"invite", "purchase", "admin"}


def grant_points(user: User, amount: int, source: str, note: str = "") -> bool:
    if amount <= 0: return False
    if source not in ALLOWED_POINT_SOURCES:
        logger.warning("مصدر نقاط غير مسموح: %s", source)
        return False
    user.points             += amount
    user.total_points_earned += amount
    db.stats["total_points_given"] = db.stats.get("total_points_given", 0) + amount
    db.update_user(user, save=False)
    db.log_activity("grant_points", user.user_id, f"+{amount} ({source}) {note}")
    return True


def consume_points(user: User, amount: int) -> bool:
    if amount <= 0: return True
    if user.points < amount: return False
    user.points -= amount
    db.update_user(user, save=False)
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 💎  شراء النقاط
# ═══════════════════════════════════════════════════════════════════════════════

async def show_buy_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = db.get_user(update.effective_user.id)
    text = (
        f"{Icon.STAR} <b>شراء نقاط بنجوم تيليجرام</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"رصيدك الحالي: <b>{u.points}</b> نقطة\n\n"
        f"اختر الباقة المناسبة:"
    )
    await _edit_or_send(update, text, kb_buy_points())


async def initiate_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              points: int, stars: int) -> None:
    user = update.effective_user
    chat = update.effective_chat
    try:
        prices  = [LabeledPrice(label=f"{points} نقطة", amount=stars)]
        payload = f"pts_{user.id}_{points}_{int(time.time())}"
        db.pending_payments[user.id] = {
            "payload": payload, "points": points, "stars": stars, "created": now_iso(),
        }
        await context.bot.send_invoice(
            chat_id=chat.id,
            title=f"{points} نقطة",
            description=f"شراء {points} نقطة لاستخدامها في رفع الملفات.",
            payload=payload,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="XTR",
            prices=prices,
            start_parameter=f"buy{points}",
        )
    except Exception as e:
        await _reply_anywhere(update, f"{Icon.CROSS} تعذر إنشاء الفاتورة: {e}")


async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q       = update.pre_checkout_query
    pending = db.pending_payments.get(q.from_user.id)
    if not pending or pending.get("payload") != q.invoice_payload:
        await q.answer(ok=False, error_message="انتهت صلاحية الفاتورة. أعد المحاولة.")
        return
    await q.answer(ok=True)


async def successful_payment_handler(update: Update,
                                      context: ContextTypes.DEFAULT_TYPE) -> None:
    msg     = update.message
    payment = msg.successful_payment
    user    = update.effective_user
    pending = db.pending_payments.pop(user.id, None) or {}
    points  = int(pending.get("points") or 0)
    stars   = int(payment.total_amount or pending.get("stars") or 0)
    u       = db.get_user(user.id)
    if points <= 0:
        m = re.match(r"pts_(\d+)_(\d+)_", payment.invoice_payload or "")
        if m: points = int(m.group(2))
    if points > 0:
        grant_points(u, points, "purchase", note=f"stars={stars}")
        u.purchases_total_stars += stars
        db.stats["total_stars_received"] = db.stats.get("total_stars_received", 0) + stars
        db.update_user(u)
    await msg.reply_text(
        f"{Icon.CHECK} تم الدفع! أُضيفت <b>{points}</b> نقطة.\nرصيدك: <b>{u.points}</b>",
        reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.DIAMOND} نقاطي", "menu:points")]]),
        parse_mode=ParseMode.HTML,
    )
    for adm in ADMIN_IDS:
        try:
            await context.bot.send_message(
                adm,
                f"{Icon.STAR} <b>دفعة جديدة</b>\n"
                f"ID: <code>{user.id}</code> ({escape_html(user.first_name or '')})\n"
                f"النقاط: <b>{points}</b> | النجوم: <b>{stars}</b>",
                parse_mode=ParseMode.HTML,
            )
        except: pass


async def redeem_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_CODE_REDEEM] = True
    await _edit_or_send(
        update, f"{Icon.CODE} أرسل كود النقاط:",
        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "menu:points")]]),
    )


async def redeem_code_do(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          raw: str) -> None:
    context.user_data.pop(ST_AWAIT_CODE_REDEEM, None)
    code  = raw.strip().upper()
    promo = db.promo_codes.get(code)
    u     = db.get_user(update.effective_user.id)
    if not promo or not promo.get("active", True):
        await update.message.reply_text(f"{Icon.CROSS} الكود غير صحيح أو متوقف.")
        return
    used_by = promo.setdefault("used_by", [])
    limit   = int(promo.get("limit", 1))
    if u.user_id in used_by:
        await update.message.reply_text(f"{Icon.INFO} استخدمت هذا الكود من قبل.")
        return
    if len(used_by) >= limit:
        await update.message.reply_text(f"{Icon.WARN} انتهى حد استخدام هذا الكود.")
        return
    points = int(promo.get("points", 0))
    if points <= 0:
        await update.message.reply_text(f"{Icon.CROSS} الكود لا يحتوي نقاطاً.")
        return
    used_by.append(u.user_id)
    grant_points(u, points, "admin", note=f"promo:{code}")
    db.update_user(u, save=False)
    db.save(force=True)
    await send_named_sticker(update, context, "points_added")
    await update.message.reply_text(
        f"{Icon.CHECK} تم تفعيل الكود <code>{escape_html(code)}</code>\n"
        f"+<b>{points}</b> نقطة · رصيدك الآن <b>{u.points}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.DIAMOND} نقاطي", "menu:points")]]),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 📤  استقبال الملفات ورفعها
# ═══════════════════════════════════════════════════════════════════════════════

async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    u    = db.get_user(user.id)
    if not await enforce_subscription(update, context): return
    cost = db.settings.get("upload_cost", 1)
    is_premium_free = u.is_premium and db.settings.get("premium_upload_free", True)
    if not is_premium_free and u.free_uploads <= 0 and u.points < cost:
        text = (
            f"{Icon.WARN} <b>لا توجد نقاط كافية</b>\n"
            f"كل رفع يكلف <b>{cost}</b> نقطة، رصيدك: <b>{u.points}</b>."
        )
        kb = InlineKeyboardMarkup([
            [btn_warning(f"{Icon.STAR} شراء نقاط", "menu:buy"),
             btn_success(f"{Icon.GIFT} الدعوة",    "menu:invite")],
            [btn_secondary(f"{Icon.BACK} رجوع", "menu:main")],
        ])
        await _edit_or_send(update, text, kb)
        return
    context.user_data[ST_AWAIT_UPLOAD] = True
    text = (
        f"{Icon.UPLOAD} <b>رفع ملف Python أو ZIP</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{Icon.AI} سيتم تحليل كودك بالذكاء الاصطناعي تلقائياً\n"
        f"{Icon.SHIELD} يُفحص أمنياً قبل التشغيل\n\n"
        f"{Icon.INFO} أرسل الآن:\n"
        f"  • ملف .py واحد، أو\n"
        f"  • ملف .zip يحتوي مشروعك\n\n"
        f"{Icon.WARN} الحد الأقصى: <b>{db.settings.get('max_file_size_mb', 50)} MB</b>"
    )
    await _edit_or_send(
        update, text,
        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "menu:main")]]),
    )


@maintenance_gate
@check_banned
@rate_limit
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get(ST_AWAIT_UPLOAD):
        if context.user_data.get("awaiting_restore") and is_admin(update.effective_user.id):
            await _do_restore(update, context)
            return
        await update.message.reply_text(
            f"{Icon.INFO} لرفع ملف اضغط الزر:",
            reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.UPLOAD} رفع ملف", "menu:upload")]]),
        )
        return

    user = update.effective_user
    u    = db.get_user(user.id)
    if not await enforce_subscription(update, context): return

    doc = update.message.document
    if not doc:
        await update.message.reply_text(f"{Icon.WARN} أرسل ملفاً وليس وسيلة أخرى.")
        return

    max_bytes = int(db.settings.get("max_file_size_mb", 50)) * 1024 * 1024
    if doc.file_size and doc.file_size > max_bytes:
        await update.message.reply_text(
            f"{Icon.CROSS} الحجم يتجاوز الحد ({db.settings.get('max_file_size_mb',50)} MB).")
        return

    fname = safe_filename(doc.file_name or "uploaded")
    ext   = os.path.splitext(fname)[1].lower()
    allowed = db.settings.get("allowed_extensions", [".py", ".zip"])
    if ext not in allowed:
        await update.message.reply_text(
            f"{Icon.CROSS} الامتداد <code>{ext}</code> غير مسموح.\n"
            f"المسموح: <code>{', '.join(allowed)}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    cost            = int(db.settings.get("upload_cost", 1))
    used_free       = False
    is_premium_free = u.is_premium and db.settings.get("premium_upload_free", True)
    if is_premium_free:
        pass
    elif u.free_uploads > 0:
        u.free_uploads -= 1; used_free = True
    else:
        if not consume_points(u, cost):
            await update.message.reply_text(f"{Icon.WARN} نقاطك غير كافية.")
            return

    file_id  = generate_file_id()
    work_dir = os.path.join(FILES_DIR, file_id)
    os.makedirs(work_dir, exist_ok=True)

    await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    try:
        tg_file    = await context.bot.get_file(doc.file_id)
        saved_path = os.path.join(work_dir, fname)
        await tg_file.download_to_drive(saved_path)
    except Exception as e:
        await update.message.reply_text(f"{Icon.CROSS} فشل التحميل: {e}")
        shutil.rmtree(work_dir, ignore_errors=True)
        if used_free: u.free_uploads += 1
        elif not is_premium_free: u.points += cost
        db.update_user(u)
        return

    is_zip = ext == ".zip"
    entry  = fname
    libs: List[str] = []

    if is_zip:
        try:
            with zipfile.ZipFile(saved_path, "r") as zf:
                zip_scan = HostingSecurity.validate_zip_members(zf)
                if zip_scan.blocked:
                    await _reject_dangerous_upload(update, context, u, zip_scan, fname, work_dir)
                    context.user_data.pop(ST_AWAIT_UPLOAD, None)
                    return
                safe_extract_zip(zf, work_dir)
        except Exception as e:
            await update.message.reply_text(f"{Icon.CROSS} ZIP تالف أو غير آمن: {e}")
            shutil.rmtree(work_dir, ignore_errors=True)
            return
        candidates = ["bot.py", "main.py", "app.py", "run.py", "start.py", "index.py"]
        entry = ""
        for c in candidates:
            if os.path.exists(os.path.join(work_dir, c)):
                entry = c; break
        if not entry:
            for fn in os.listdir(work_dir):
                if fn.endswith(".py"): entry = fn; break
        if not entry:
            await update.message.reply_text(f"{Icon.WARN} لم أجد ملف Python داخل ZIP.")
        libs = LibraryDetector.detect_from_directory(work_dir)
    else:
        libs = LibraryDetector.detect_from_file(saved_path)

    # ─── فحص الأمان ──────────────────────────────────────────────
    security_enabled = db.settings.get("security_enabled", False)
    
    if security_enabled:
        if db.settings.get("strict_hosting_security", True):
            scan = (HostingSecurity.scan_directory(work_dir)
                    if is_zip else HostingSecurity.scan_file(saved_path, fname))
            if scan.blocked:
                await _reject_dangerous_upload(update, context, u, scan, fname, work_dir)
                context.user_data.pop(ST_AWAIT_UPLOAD, None)
                return

        if db.settings.get("api_protection_enabled", True):
            api_scan_result = SecurityScan()
            if is_zip:
                for root, _, files in os.walk(work_dir):
                    for fn in files:
                        if fn.endswith(".py"):
                            with open(os.path.join(root, fn), "r", encoding="utf-8", errors="ignore") as f:
                                src = f.read()
                            partial = HostingSecurity.api_protection_scan(src, fn)
                            if partial.blocked:
                                api_scan_result = partial; break
            else:
                with open(saved_path, "r", encoding="utf-8", errors="ignore") as f:
                    api_scan_result = HostingSecurity.api_protection_scan(f.read(), fname)

            if api_scan_result.blocked:
                await _reject_dangerous_upload(update, context, u, api_scan_result, fname, work_dir)
                context.user_data.pop(ST_AWAIT_UPLOAD, None)
                return
    else:
        logger.info(f"الحماية معطلة — تم تخطي فحص الملف {fname} من المستخدم {u.user_id}")

    # ─── نظام الموافقة ──────────────────────────────────────────
    require_approval = db.settings.get("require_approval", False)
    
    if require_approval:
        hf = HostedFile(
            file_id=file_id, file_name=fname, owner_id=u.user_id,
            upload_date=now_iso(), size=doc.file_size or os.path.getsize(saved_path),
            libraries=libs, stored_path=saved_path, entry_file=entry,
            is_zip=is_zip,
            auto_restart=bool(db.settings.get("auto_restart_default", False)),
            pending_approval=True,
            approval_status="pending"
        )
        db.add_file(hf)
        if file_id not in u.files: u.files.append(file_id)
        u.total_uploads += 1
        db.update_user(u)
        
        me = await context.bot.get_me()
        for adm in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    adm,
                    f"{Icon.PENDING} <b>طلب موافقة على ملف جديد</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{Icon.USER} المستخدم: <code>{u.user_id}</code> @{escape_html(u.username or '—')}\n"
                    f"{Icon.FILE} الملف: <code>{escape_html(fname)}</code>\n"
                    f"{Icon.STATS} الحجم: <b>{format_size(hf.size)}</b>\n"
                    f"{Icon.LIBRARIES} المكتبات: {len(libs)}\n"
                    f"{Icon.LINK} الرابط:\n<code>https://t.me/{me.username}?start=file_{file_id}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"اختر الإجراء:",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [btn_success(f"{Icon.APPROVAL} موافقة", f"approve:{file_id}"),
                         btn_danger (f"{Icon.REJECT} رفض",     f"reject:{file_id}")],
                        [btn_primary(f"{Icon.USER} المستخدم", f"admin:user:{u.user_id}")],
                    ]),
                )
            except Exception as e:
                logger.error(f"فشل إرسال طلب الموافقة للمشرف {adm}: {e}")
        
        await update.message.reply_text(
            f"{Icon.PENDING} <b>تم استلام ملفك</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"الملف: <code>{escape_html(fname)}</code>\n"
            f"{Icon.CLOCK} في انتظار موافقة المشرف.\n"
            f"ستصلك رسالة عند الموافقة أو الرفض.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [btn_primary(f"{Icon.FOLDER} ملفاتي", "menu:myfiles")]
            ]),
        )
        context.user_data.pop(ST_AWAIT_UPLOAD, None)
        return

    # ─── بدون موافقة ────────────────────────────────────────────
    hf = HostedFile(
        file_id    =file_id, file_name=fname, owner_id=u.user_id,
        upload_date=now_iso(), size=doc.file_size or os.path.getsize(saved_path),
        libraries  =libs, stored_path=saved_path, entry_file=entry,
        is_zip     =is_zip,
        auto_restart=bool(db.settings.get("auto_restart_default", False)),
        pending_approval=False,
        approval_status="approved"
    )
    db.add_file(hf)
    if file_id not in u.files: u.files.append(file_id)
    u.total_uploads += 1
    db.update_user(u)

    if libs: write_requirements(work_dir, libs)

    await send_named_sticker(update, context,
                              "installing_libs" if libs else "upload_success")
    progress = await update.message.reply_text(
        f"{Icon.LIGHT} <b>جاري تجهيز الاستضافة</b>\n{progress_bar(8)} <b>8%</b>",
        parse_mode=ParseMode.HTML,
    )

    install_msg = ""
    install_ok  = True
    if libs and db.settings.get("auto_install_libs", True):
        ok, out = await run_blocking_with_progress(
            progress, "تثبيت المكتبات", pm.install_libs, libs, work_dir)
        install_ok = bool(ok)
        hf.install_log = out
        install_msg = (f"\n{Icon.CHECK} تثبيت المكتبات: ناجح"
                       if ok else f"\n{Icon.WARN} تثبيت المكتبات: تعثر")
        db.add_file(hf)
    else:
        await edit_progress(progress, "لا مكتبات مطلوبة", 75)

    auto_run_msg = ""
    if (install_ok and entry and entry.endswith(".py")
            and db.settings.get("auto_run_after_upload", True)):
        await edit_progress(progress, "تشغيل الملف تلقائياً", 90)
        ok_run, run_info = pm.start(file_id, work_dir, entry)
        if ok_run:
            hf.run_count += 1; hf.last_run = now_iso(); hf.start_time = now_iso()
            u.total_runs += 1
            db.stats["total_runs"] = db.stats.get("total_runs", 0) + 1
            db.add_file(hf); db.update_user(u)
            auto_run_msg = f"\n{Icon.ROCKET} يعمل الآن (<code>{escape_html(run_info)}</code>)"
            await send_named_sticker(update, context, "hosting_started")
        else:
            auto_run_msg = f"\n{Icon.WARN} تعذر التشغيل: <code>{escape_html(run_info)}</code>"

    await edit_progress(progress, "تمت الاستضافة بنجاح", 100)

    ai_report = ""
    ai_result = None
    if db.settings.get("ai_analysis_enabled", True) and security_enabled:
        try:
            def _do_ai():
                if is_zip: return AICodeAnalyzer.analyze_directory(work_dir)
                return AICodeAnalyzer.analyze_file(saved_path)
            ai_result = await asyncio.to_thread(_do_ai)
            hf.ai_analysis = ai_result.summary
            db.add_file(hf)
            ai_report = f"\n\n{Icon.AI} <b>تحليل AI:</b> {escape_html(ai_result.summary)}"
        except Exception as e:
            logger.warning("AI analysis failed: %s", e)

    if is_premium_free:
        cost_line = f"{Icon.PREMIUM} رفع مجاني (بريميوم)"
    elif used_free:
        cost_line = f"{Icon.GIFT} رفع مجاني مستخدم"
    else:
        cost_line = f"{Icon.DIAMOND} خُصم {cost} نقطة"

    libs_text = "، ".join(libs[:6]) + ("…" if len(libs) > 6 else "") if libs else "لا توجد"
    me        = await context.bot.get_me()
    share_link= f"https://t.me/{me.username}?start=file_{file_id}"
    msg = (
        f"{Icon.CHECK} <b>تمت الاستضافة بنجاح!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{Icon.FILE} <code>{escape_html(fname)}</code> · {format_size(hf.size)}\n"
        f"معرّف الملف: <code>{file_id}</code>\n"
        f"{Icon.LINK} رابط المشاركة:\n<code>{share_link}</code>\n"
        f"تشغيل {hf.run_count} · تحميل {hf.downloads} · مكتبات {len(libs)}\n"
        f"{Icon.LIGHT} المكتبات: {escape_html(libs_text)}{install_msg}{auto_run_msg}\n"
        f"{Icon.API_PROTECT} فحص API: {'آمن' if security_enabled else 'معطل'}\n"
        f"{Icon.SHIELD} فحص الأمان: {'اجتاز' if security_enabled else 'معطل'}\n"
        f"{cost_line}{ai_report}"
    )
    await update.message.reply_text(
        msg,
        reply_markup=kb_file_actions(file_id, True, pm.is_running(file_id)),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    if ai_result and (ai_result.potential_issues or ai_result.recommendations or ai_result.security_notes):
        try:
            report_text = AICodeAnalyzer.format_report(ai_result, fname)
            await update.message.reply_text(report_text, parse_mode=ParseMode.HTML,
                                             reply_markup=InlineKeyboardMarkup([[
                                                 btn_primary(f"{Icon.FOLDER} ملفاتي", "menu:myfiles")
                                             ]]))
        except: pass

    if db.settings.get("notify_admin_on_upload", True):
        for adm in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    adm,
                    f"{Icon.UPLOAD} <b>رفع جديد</b>\n"
                    f"ID: <code>{u.user_id}</code> @{escape_html(u.username or '—')}\n"
                    f"الملف: <code>{escape_html(fname)}</code>\n"
                    f"الحجم: <b>{format_size(hf.size)}</b> | مكتبات: {len(libs)}\n"
                    + (f"{Icon.AI} AI: {escape_html(hf.ai_analysis[:100])}\n" if hf.ai_analysis else ""),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([[
                        btn_primary(f"{Icon.FILE} الملف",    f"file:open:{file_id}"),
                        btn_primary(f"{Icon.USER} المستخدم", f"admin:user:{u.user_id}"),
                    ]]),
                )
            except: pass

    context.user_data.pop(ST_AWAIT_UPLOAD, None)
    db.log_activity("upload", u.user_id, fname)


async def _reject_dangerous_upload(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    u: User, scan: SecurityScan,
                                    fname: str, work_dir: str) -> None:
    shutil.rmtree(work_dir, ignore_errors=True)
    if not is_admin_immortal(u.user_id):
        u.is_banned  = bool(scan.ban)
        u.ban_reason = "ملف خطر مؤكد يستهدف ملفات/أسرار الاستضافة أو API"
    db.update_user(u)
    db.security_events.append({
        "user_id": u.user_id, "file": fname, "score": scan.score,
        "reasons": scan.reasons[:8], "at": now_iso(),
        "banned": bool(scan.ban) and not is_admin_immortal(u.user_id),
    })
    db.save(force=True)
    await send_named_sticker(update, context, "security_blocked")
    text = (
        f"{Icon.API_PROTECT} <b>تم رفض الملف — حماية API</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الملف: <code>{escape_html(fname)}</code>\n"
        f"السبب: محاولة مؤكدة للمساس بالاستضافة أو سرقة بيانات API.\n"
        f"الإجراء: {'حظر المستخدم' if scan.ban and not is_admin_immortal(u.user_id) else 'رفض الملف فقط'}"
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(support_rows()),
    )
    for adm in ADMIN_IDS:
        try:
            await context.bot.send_message(
                adm,
                f"{Icon.API_PROTECT} <b>خطر مؤكد مرفوض!</b>\n"
                f"ID: <code>{u.user_id}</code> @{escape_html(u.username or '—')}\n"
                f"الملف: <code>{escape_html(fname)}</code>\n"
                + "\n".join(f"• {escape_html(x)}" for x in scan.reasons[:8]),
                parse_mode=ParseMode.HTML,
            )
        except: pass


# ═══════════════════════════════════════════════════════════════════════════════
# 📁  إدارة الملفات
# ═══════════════════════════════════════════════════════════════════════════════

async def show_my_files(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         page: int = 0) -> None:
    u     = db.get_user(update.effective_user.id)
    files = db.user_files(u.user_id)
    if not files:
        text = (f"{Icon.FOLDER} <b>ملفاتي</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"لم ترفع أي ملف بعد.")
        kb = InlineKeyboardMarkup([
            [btn_success(f"{Icon.UPLOAD} رفع ملف", "menu:upload")],
            [btn_secondary(f"{Icon.BACK} الرئيسية", "menu:main")],
        ])
        await _edit_or_send(update, text, kb)
        return
    items: List[Tuple[str, str]] = []
    for f in sorted(files, key=lambda x: x.upload_date, reverse=True):
        flag  = "●" if pm.is_running(f.file_id) else "○"
        pending_flag = " ⏳" if f.pending_approval and f.approval_status == "pending" else ""
        ai_tag = " [AI]" if f.ai_analysis else ""
        label = f"{flag}{pending_flag} {shorten(f.file_name, 26)} · {format_size(f.size)}{ai_tag}"
        items.append((label, f"file:open:{f.file_id}"))
    kb   = kb_paginated(items, page, 7, "myfiles:page", "menu:main")
    text = (
        f"{Icon.FOLDER} <b>ملفاتي ({len(files)})</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"● = يعمل   ○ = متوقف   ⏳ = ينتظر الموافقة   [AI] = تم تحليله\n"
        f"اضغط أي ملف لإدارته."
    )
    await _edit_or_send(update, text, kb)


async def open_file(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     file_id: str) -> None:
    u   = db.get_user(update.effective_user.id)
    hf  = db.get_file(file_id)
    if not hf:
        await _edit_or_send(update, f"{Icon.CROSS} الملف غير موجود.", kb_back("menu:myfiles"))
        return
    is_owner = (hf.owner_id == u.user_id) or is_admin(u.user_id)
    running  = pm.is_running(file_id)
    pid      = pm.pid(file_id) if running else None
    uptime   = pm.uptime(file_id) if running else "—"
    public_label = "عام" if hf.is_public else "خاص"
    pending_label = ""
    if hf.pending_approval and hf.approval_status == "pending":
        pending_label = f"\n{Icon.PENDING} <b>في انتظار موافقة المشرف</b>"
    ai_tag   = f"\n{Icon.AI} AI: {escape_html(hf.ai_analysis[:80])}" if hf.ai_analysis else ""
    text = (
        f"{Icon.FILE} <b>{escape_html(hf.file_name)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"المعرّف:      <code>{hf.file_id}</code>\n"
        f"الحجم:        <b>{format_size(hf.size)}</b>\n"
        f"الرفع:        <b>{format_dt(hf.upload_date)}</b>\n"
        f"ملف الدخول:   <code>{escape_html(hf.entry_file or '—')}</code>\n"
        f"المكتبات:     {escape_html('، '.join(hf.libraries[:5]) or '—')}\n"
        f"الحالة:       {'يعمل PID=' + str(pid) + ' (' + uptime + ')' if running else 'متوقف'}\n"
        f"إقلاع تلقائي: {'مفعّل' if hf.auto_restart else 'معطّل'}\n"
        f"العمومية:     {public_label}\n"
        f"مرات التشغيل: <b>{hf.run_count}</b>\n"
        f"التحميلات:    <b>{hf.downloads}</b>\n"
        f"إجمالي التشغيل: <b>{hf.total_runtime_seconds // 60} د</b>\n"
        f"الوصف: {escape_html(hf.description) or '—'}{pending_label}{ai_tag}"
    )
    kb = kb_file_actions(file_id, is_owner, running, is_admin_view=is_admin(u.user_id))
    await _edit_or_send(update, text, kb)


async def file_ai_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return

    work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, file_id)
    msg = None
    if update.callback_query:
        msg = await update.callback_query.message.reply_text(
            f"{Icon.AI} جاري التحليل بالذكاء الاصطناعي…", parse_mode=ParseMode.HTML)
    else:
        msg = await update.message.reply_text(
            f"{Icon.AI} جاري التحليل بالذكاء الاصطناعي…", parse_mode=ParseMode.HTML)

    try:
        def _do_analysis():
            if hf.is_zip:
                return AICodeAnalyzer.analyze_directory(work_dir)
            return AICodeAnalyzer.analyze_file(hf.stored_path or os.path.join(work_dir, hf.file_name))

        result = await asyncio.to_thread(_do_analysis)
        hf.ai_analysis = result.summary
        db.add_file(hf)
        report = AICodeAnalyzer.format_report(result, hf.file_name)
        await msg.edit_text(
            report, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [btn_primary(f"{Icon.REFRESH} إعادة التحليل", f"file:ai:{file_id}"),
                 btn_secondary(f"{Icon.BACK} رجوع",           f"file:open:{file_id}")],
            ]),
        )
    except Exception as e:
        await msg.edit_text(
            f"{Icon.CROSS} فشل التحليل: {escape_html(str(e))}",
            reply_markup=kb_back(f"file:open:{file_id}"),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 🖥️ ترمنال آمن للمشروع
# ═══════════════════════════════════════════════════════════════════════════════

TERMINAL_ALLOWED = {
    "pwd", "ls", "pip", "pip3", "python", "python3",
    "df", "free", "uname", "whoami", "du", "ps"
}

def _terminal_command_allowed(command: str) -> bool:
    if not command or len(command) > 500:
        return False
    forbidden_tokens = (";", "|", "&&", "||", ">", "<", "`", "$(", "\n", "\r")
    if any(token in command for token in forbidden_tokens):
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    return bool(parts) and parts[0].lower() in TERMINAL_ALLOWED

async def file_terminal_start(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              file_id: str) -> None:
    u = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك استخدام ترمنال هذا الملف.",
                            kb_back("menu:myfiles"))
        return

    work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, file_id)
    if not os.path.isdir(work_dir):
        await _edit_or_send(update, f"{Icon.CROSS} مجلد المشروع غير موجود.",
                            kb_back(f"file:open:{file_id}"))
        return

    context.user_data[ST_AWAIT_TERMINAL] = file_id
    text = (
        f"{Icon.TERMINAL} <b>ترمنال المشروع</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 <code>{escape_html(hf.file_name)}</code>\n\n"
        f"المسموح: <code>pwd</code> · <code>ls</code> · <code>pip list</code> · "
        f"<code>pip install PACKAGE</code> · <code>python --version</code> · "
        f"<code>df -h</code> · <code>free -h</code> · <code>ps</code>\n\n"
        f"✍️ أرسل الأمر الآن، واكتب <code>خروج</code> للعودة."
    )
    await _edit_or_send(update, text, kb_back(f"file:open:{file_id}"))

async def file_terminal_exec(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             file_id: str, command: str) -> None:
    u = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        context.user_data.pop(ST_AWAIT_TERMINAL, None)
        await update.message.reply_text(f"{Icon.BAN} لا يمكنك استخدام هذا الترمنال.")
        return

    command = command.strip()
    if not _terminal_command_allowed(command):
        await update.message.reply_text(
            f"{Icon.CROSS} الأمر غير مسموح. استخدم الأوامر المعروضة في صفحة الترمنال."
        )
        return

    work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, file_id)
    try:
        parts = shlex.split(command)
        proc = await asyncio.to_thread(
            subprocess.run, parts, cwd=work_dir, capture_output=True,
            text=True, timeout=30, check=False,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        output = ((proc.stdout or "") + (proc.stderr or "")).strip() or "(بدون مخرجات)"
        output = output[-3500:]
        status = "✅ نجح" if proc.returncode == 0 else f"❌ فشل ({proc.returncode})"
        await update.message.reply_text(
            f"{Icon.TERMINAL} <b>{status}</b>\n"
            f"📁 <code>{escape_html(hf.file_name)}</code>\n"
            f"💻 <code>{escape_html(command)}</code>\n\n"
            f"<pre>{escape_html(output)}</pre>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [btn_primary("🖥️ ترمنال مرة أخرى", f"file:terminal:{file_id}")],
                [btn_primary("⬅️ الملف", f"file:open:{file_id}")],
            ]),
        )
    except subprocess.TimeoutExpired:
        await update.message.reply_text(
            f"{Icon.CROSS} انتهت مهلة الأمر (30 ثانية).",
            reply_markup=InlineKeyboardMarkup([
                [btn_primary("🖥️ ترمنال", f"file:terminal:{file_id}")],
                [btn_primary("⬅️ الملف", f"file:open:{file_id}")],
            ]),
        )
    except Exception as e:
        await update.message.reply_text(
            f"{Icon.CROSS} خطأ: {escape_html(str(e)[:500])}",
            parse_mode=ParseMode.HTML,
        )

async def file_run(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf:
        await _edit_or_send(update, f"{Icon.CROSS} الملف غير موجود.", kb_back("menu:myfiles"))
        return
    if hf.owner_id != u.user_id and not is_admin(u.user_id):
        await _edit_or_send(update, f"{Icon.BAN} هذا الملف ليس لك.", kb_back("menu:myfiles"))
        return
    if hf.pending_approval and hf.approval_status == "pending":
        await _edit_or_send(update, f"{Icon.PENDING} الملف في انتظار موافقة المشرف.", kb_back(f"file:open:{file_id}"))
        return
    if pm.is_running(file_id):
        await _edit_or_send(update, f"{Icon.INFO} العملية تعمل بالفعل.", kb_back(f"file:open:{file_id}"))
        return
    max_procs = int(db.settings.get(
        "premium_max_processes" if u.is_premium else "max_processes_per_user",
        MAX_PROCESSES_PER_USER))
    if not is_admin(u.user_id) and pm.user_running_count(u.user_id) >= max_procs:
        await _edit_or_send(
            update, f"{Icon.WARN} تجاوزت الحد ({max_procs} عمليات). أوقف ملفاً أولاً.",
            kb_back(f"file:open:{file_id}"))
        return
    work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, file_id)
    ok, info = pm.start(file_id, work_dir, hf.entry_file or hf.file_name)
    if ok:
        hf.run_count += 1; hf.last_run = now_iso(); hf.start_time = now_iso()
        u.total_runs += 1
        db.stats["total_runs"] = db.stats.get("total_runs", 0) + 1
        db.add_file(hf); db.update_user(u)
        text = f"{Icon.PLAY} <b>تم التشغيل!</b>\nPID: <code>{escape_html(info)}</code>"
    else:
        text = f"{Icon.CROSS} فشل التشغيل: {escape_html(info)}"
        if db.settings.get("send_zip_if_run_fails", True):
            await _send_project_zip_direct(update, context, hf, "فشل التشغيل")
    await _edit_or_send(update, text, kb_back(f"file:open:{file_id}"))


async def file_stop(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    ok, info = pm.stop(file_id)
    if ok: hf.last_stop = now_iso(); db.add_file(hf)
    await _edit_or_send(update, f"{Icon.STOP} {escape_html(info)}", kb_back(f"file:open:{file_id}"))


async def file_restart(update: Update, context: ContextTypes.DEFAULT_TYPE,
                        file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    if hf.pending_approval and hf.approval_status == "pending":
        await _edit_or_send(update, f"{Icon.PENDING} الملف في انتظار موافقة المشرف.", kb_back(f"file:open:{file_id}"))
        return
    ok, info = pm.restart(file_id)
    if ok:
        hf.run_count += 1; hf.last_run = now_iso(); hf.start_time = now_iso()
        db.add_file(hf)
    text = (f"{Icon.RESTART} <b>تم إعادة التشغيل!</b>\n<code>{escape_html(info)}</code>"
            if ok else f"{Icon.CROSS} فشل: {escape_html(info)}")
    await _edit_or_send(update, text, kb_back(f"file:open:{file_id}"))


async def file_log(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    tail    = pm.tail_log(file_id, 50)
    if len(tail) > 3500: tail = "…" + tail[-3500:]
    running = pm.is_running(file_id)
    text    = (
        f"{Icon.TERMINAL} <b>سجل التشغيل — آخر 50 سطر</b>\n"
        f"الحالة: {'يعمل · ' + pm.uptime(file_id) if running else 'متوقف'}\n"
        f"<pre>{escape_html(tail)}</pre>"
    )
    kb = InlineKeyboardMarkup([
        [btn_primary(f"{Icon.REFRESH} تحديث",  f"file:log:{file_id}"),
         btn_primary(f"{Icon.EXPORT} تصدير",   f"file:export_log:{file_id}")],
        [btn_secondary(f"{Icon.BACK} رجوع", f"file:open:{file_id}")],
    ])
    await _edit_or_send(update, text, kb)


async def file_export_log(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    log_bytes = pm.export_log(file_id)
    fname     = f"log_{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=InputFile(io.BytesIO(log_bytes), filename=fname),
            caption=f"{Icon.EXPORT} سجل تشغيل: <code>{escape_html(hf.file_name)}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await _reply_anywhere(update, f"{Icon.CROSS} فشل التصدير: {e}")


async def file_install(update: Update, context: ContextTypes.DEFAULT_TYPE,
                        file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, file_id)
    libs     = LibraryDetector.detect_from_directory(work_dir)
    hf.libraries = libs
    if libs: write_requirements(work_dir, libs)
    if not libs:
        await _edit_or_send(update, f"{Icon.INFO} لا توجد مكتبات خارجية.",
                            kb_back(f"file:open:{file_id}"))
        return
    if update.callback_query:
        msg = await update.callback_query.message.reply_text(
            f"{Icon.LIGHT} جاري تثبيت {len(libs)} مكتبة…", parse_mode=ParseMode.HTML)
    else:
        msg = await update.message.reply_text(
            f"{Icon.LIGHT} جاري تثبيت {len(libs)} مكتبة…", parse_mode=ParseMode.HTML)
    await send_named_sticker(update, context, "installing_libs")
    ok, out = await run_blocking_with_progress(msg, "تثبيت المكتبات", pm.install_libs, libs, work_dir)
    hf.install_log = out
    db.add_file(hf)
    snippet = out[-2000:] if out else ""
    text = (
        f"{'تم التثبيت بنجاح' if ok else 'فشل التثبيت'}\n"
        f"المكتبات: {escape_html(', '.join(libs[:10]))}\n"
        f"<pre>{escape_html(snippet)}</pre>"
    )
    await _edit_or_send(update, text, kb_back(f"file:open:{file_id}"))


async def file_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    text = (f"{Icon.WARN} <b>تأكيد الحذف</b>\n"
            f"سيُحذف <code>{escape_html(hf.file_name)}</code> نهائياً.")
    await _edit_or_send(update, text, kb_confirm(f"file:del_yes:{file_id}", f"file:open:{file_id}"))


async def file_delete_do(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf:
        await _edit_or_send(update, f"{Icon.CROSS} الملف غير موجود.", kb_back("menu:myfiles"))
        return
    if hf.owner_id != u.user_id and not is_admin(u.user_id):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    pm.stop(file_id)
    work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, file_id)
    shutil.rmtree(work_dir, ignore_errors=True)
    db.remove_file(file_id)
    db.log_activity("delete_file", u.user_id, hf.file_name)
    await _edit_or_send(update, f"{Icon.CHECK} تم الحذف بنجاح.", kb_back("menu:myfiles"))


async def file_zip(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    file_id: str) -> None:
    hf = db.get_file(file_id)
    if not hf:
        await _edit_or_send(update, f"{Icon.CROSS} الملف غير موجود.", kb_back("menu:myfiles"))
        return
    await _send_project_zip_direct(update, context, hf, "طلب تحميل")


async def _send_project_zip_direct(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    hf: HostedFile, reason: str = "") -> None:
    work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, hf.file_id)
    if hf.libraries: write_requirements(work_dir, hf.libraries)
    out_zip  = os.path.join(TEMP_DIR, f"{hf.file_id}_{int(time.time())}.zip")
    try:
        make_zip_of_dir(work_dir, out_zip)
    except Exception as e:
        await _reply_anywhere(update, f"{Icon.CROSS} تعذر إنشاء ZIP: {e}")
        return
    caption = (
        f"{Icon.DOWNLOAD} <b>ملف المشروع</b>\n"
        f"الاسم: <code>{escape_html(hf.file_name)}</code>\n"
        f"السبب: {escape_html(reason or 'تحميل')}"
    )
    try:
        chat = update.effective_chat
        await chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        with open(out_zip, "rb") as f:
            await context.bot.send_document(
                chat_id=chat.id,
                document=InputFile(f, filename=f"{os.path.splitext(hf.file_name)[0]}.zip"),
                caption=caption, parse_mode=ParseMode.HTML,
            )
        hf.downloads += 1
        db.stats["total_downloads"] = db.stats.get("total_downloads", 0) + 1
        owner = db.users.get(hf.owner_id)
        if owner: owner.total_downloads += 1; db.update_user(owner, save=False)
        db.add_file(hf)
    except Exception as e:
        await _reply_anywhere(update, f"{Icon.CROSS} فشل إرسال الملف: {e}")
    finally:
        try: os.remove(out_zip)
        except: pass


async def file_toggle_auto(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    hf.auto_restart = not hf.auto_restart
    db.add_file(hf)
    await open_file(update, context, file_id)


async def file_toggle_public(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              file_id: str) -> None:
    u  = db.get_user(update.effective_user.id)
    hf = db.get_file(file_id)
    if not hf or (hf.owner_id != u.user_id and not is_admin(u.user_id)):
        await _edit_or_send(update, f"{Icon.BAN} لا يمكنك.", kb_back("menu:myfiles"))
        return
    if not db.settings.get("public_files_enabled", True) and not is_admin(u.user_id):
        await _edit_or_send(update, f"{Icon.WARN} الملفات العامة معطّلة.",
                            kb_back(f"file:open:{file_id}"))
        return
    hf.is_public = not hf.is_public
    db.add_file(hf)
    await open_file(update, context, file_id)


async def file_share(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      file_id: str) -> None:
    hf = db.get_file(file_id)
    if not hf:
        await _edit_or_send(update, f"{Icon.CROSS} الملف غير موجود.", kb_back("menu:myfiles"))
        return
    me   = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start=file_{file_id}"
    text = (
        f"{Icon.LINK} <b>رابط مشاركة الملف</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>{link}</code>\n\n"
        f"{'الملف عام — يمكن لأي شخص تحميله.' if hf.is_public else 'الملف خاص — فقط أنت تستطيع تحميله.'}"
    )
    share_text = urllib.parse.quote(f"استخدم هذا الرابط لتحميل ملفي: {link}")
    kb = InlineKeyboardMarkup([
        [btn_url_primary(f"{Icon.LINK} مشاركة عبر تيليجرام",
                         f"https://t.me/share/url?url={urllib.parse.quote(link)}&text={share_text}")],
        [btn_secondary(f"{Icon.BACK} رجوع", f"file:open:{file_id}")],
    ])
    await _edit_or_send(update, text, kb)


async def file_desc_start(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           file_id: str) -> None:
    context.user_data[ST_AWAIT_FILE_DESC] = file_id
    await _edit_or_send(
        update, f"{Icon.EDIT} أرسل وصفاً جديداً للملف:",
        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", f"file:open:{file_id}")]]),
    )


async def _do_restore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_restore", None)
    doc = update.message.document
    if not doc or not (doc.file_name or "").startswith("backup_"):
        await update.message.reply_text(f"{Icon.WARN} يجب أن يكون الملف backup_*.zip")
        return
    tmp_path = os.path.join(TEMP_DIR, f"restore_{int(time.time())}.zip")
    try:
        tg_file = await context.bot.get_file(doc.file_id)
        await tg_file.download_to_drive(tmp_path)
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(".")
        db.load()
        await update.message.reply_text(
            f"{Icon.CHECK} تمت الاستعادة بنجاح!",
            reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.CROWN} لوحة الإدارة", "admin:panel")]]),
        )
    except Exception as e:
        await update.message.reply_text(f"{Icon.CROSS} فشلت الاستعادة: {e}")
    finally:
        try: os.remove(tmp_path)
        except: pass


# ═══════════════════════════════════════════════════════════════════════════════
# 👑  لوحة الإدارة
# ═══════════════════════════════════════════════════════════════════════════════

@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"{Icon.CROWN} <b>لوحة الإدارة</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"المستخدمون: <b>{len(db.users)}</b> | الملفات: <b>{len(db.files)}</b>\n"
        f"الملفات قيد المراجعة: <b>{len(db.get_pending_files())}</b>\n"
        f"يعمل الآن: <b>{len(pm.all_running())}</b>\n"
        f"{res_monitor.summary_text()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{Icon.APPROVAL} الموافقة: <b>{'مفعّلة' if db.settings.get('require_approval') else 'معطّلة'}</b>\n"
        f"{Icon.SHIELD} الحماية: <b>{'مفعّلة' if db.settings.get('security_enabled') else 'معطّلة'}</b>"
    )
    await _edit_or_send(update, text, kb_admin_panel())


@admin_only
async def admin_toggle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = db.settings.get("require_approval", False)
    db.settings["require_approval"] = not current
    db.save(force=True)
    state = "مفعّلة ✅" if not current else "معطّلة ❌"
    await update.callback_query.answer(f"الموافقة: {state}", show_alert=True)
    await admin_panel(update, context)


@admin_only
async def admin_toggle_security(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = db.settings.get("security_enabled", False)
    db.settings["security_enabled"] = not current
    db.save(force=True)
    state = "مفعّلة ✅" if not current else "معطّلة ❌"
    await update.callback_query.answer(f"الحماية: {state}", show_alert=True)
    await admin_panel(update, context)


@admin_only
async def admin_pending_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending = db.get_pending_files()
    if not pending:
        await _edit_or_send(update, f"{Icon.REVIEW} <b>الملفات قيد المراجعة</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nلا توجد ملفات في انتظار الموافقة.",
                            kb_back("admin:panel"))
        return

    text = f"{Icon.REVIEW} <b>الملفات قيد المراجعة ({len(pending)})</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    rows = []
    for hf in pending:
        owner = db.users.get(hf.owner_id)
        owner_name = f"@{owner.username}" if owner and owner.username else str(hf.owner_id)
        text += f"• <code>{shorten(hf.file_name, 20)}</code> — {owner_name}\n"
        rows.append([
            btn_success(f"✅ موافقة: {shorten(hf.file_name, 12)}", f"approve:{hf.file_id}"),
            btn_danger(f"❌ رفض: {shorten(hf.file_name, 12)}", f"reject:{hf.file_id}"),
        ])

    rows.append([btn_primary("⬅️ رجوع للوحة", "admin:panel")])
    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))


@admin_only
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _edit_or_send(
        update, text_admin_stats(),
        InlineKeyboardMarkup([
            [btn_primary(f"{Icon.REFRESH} تحديث", "admin:stats")],
            [btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")],
        ]),
    )


@admin_only
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE,
                       page: int = 0) -> None:
    users = sorted(db.all_users(), key=lambda x: x.last_active, reverse=True)
    items: List[Tuple[str, str]] = []
    for u in users:
        flag  = (Icon.CROWN if is_admin(u.user_id) else
                 Icon.PREMIUM if u.is_premium else
                 Icon.BAN if u.is_banned else Icon.USER)
        label = f"{flag} [{u.user_id}] {shorten(u.first_name or str(u.user_id), 18)} · {u.points}pts"
        items.append((label, f"admin:user:{u.user_id}"))
    kb   = kb_paginated(items, page, 8, "admin:users:page", "admin:panel")
    text = f"{Icon.USERS} <b>المستخدمون ({len(users)})</b>"
    await _edit_or_send(update, text, kb)


@admin_only
async def admin_user_details(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              uid: int) -> None:
    u = db.users.get(uid)
    if not u:
        await _edit_or_send(update, f"{Icon.CROSS} مستخدم غير موجود.", kb_back("admin:panel"))
        return
    files_list = db.user_files(uid)
    running    = sum(1 for f in files_list if pm.is_running(f.file_id))
    badges     = []
    if is_admin(uid):  badges.append("مشرف")
    if u.is_premium:   badges.append("بريميوم")
    if u.is_banned:    badges.append("محظور")
    badge_str  = " | ".join(badges) if badges else "عادي"
    text = (
        f"{Icon.USER} <b>تفاصيل المستخدم</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"ID:        <code>{u.user_id}</code>\n"
        f"الاسم:     <b>{escape_html(u.first_name or '—')}</b>\n"
        f"يوزرنيم:   @{escape_html(u.username or '—')}\n"
        f"الحالة:    {badge_str}\n"
        f"نقاط:      <b>{u.points}</b>\n"
        f"دعوات:     <b>{len(u.invited_users)}</b>\n"
        f"رفع:       <b>{u.total_uploads}</b>\n"
        f"ملفات:     <b>{len(files_list)}</b> (يعمل: {running})\n"
        f"انضمام:    {format_dt(u.join_date)}\n"
        f"آخر نشاط:  {humanize_delta(u.last_active)}\n"
        f"ملاحظة:    {escape_html(u.notes or '—')}"
    )
    rows = [
        [btn_success(f"{Icon.PLUS} +نقاط",          f"admin:addpts_user:{uid}"),
         btn_danger (f"{Icon.MINUS} -نقاط",          f"admin:subpts_user:{uid}")],
        [btn_danger (f"{Icon.BAN} حظر",              f"admin:ban_user:{uid}"),
         btn_success(f"{Icon.UNBAN} فك الحظر",       f"admin:unban_user:{uid}")],
        [btn_success(f"{Icon.PREMIUM} منح بريميوم",  f"admin:grant_premium:{uid}"),
         btn_danger (f"{Icon.CROSS} سحب بريميوم",    f"admin:revoke_premium:{uid}")],
        [btn_primary(f"{Icon.FOLDER} ملفاته ({len(files_list)})", f"admin:user_files:{uid}"),
         btn_primary(f"{Icon.NOTE} ملاحظة",          f"admin:note_user:{uid}")],
        [btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")],
    ]
    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))


@admin_only
async def admin_files(update: Update, context: ContextTypes.DEFAULT_TYPE,
                       page: int = 0) -> None:
    files = db.all_files_sorted()
    items: List[Tuple[str, str]] = []
    for f in files:
        flag  = "●" if pm.is_running(f.file_id) else "○"
        pending_flag = " ⏳" if f.pending_approval and f.approval_status == "pending" else ""
        owner = db.users.get(f.owner_id)
        ownr  = f"@{owner.username}" if owner and owner.username else str(f.owner_id)
        items.append((f"{flag}{pending_flag} {shorten(f.file_name, 22)} · {format_size(f.size)} · {ownr}",
                      f"file:open:{f.file_id}"))
    kb   = kb_paginated(items, page, 8, "admin:files:page", "admin:panel")
    await _edit_or_send(update, f"{Icon.FOLDER} <b>كل الملفات ({len(files)})</b>", kb)


@admin_only
async def admin_user_files_list(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 uid: int, page: int = 0) -> None:
    files = db.user_files(uid)
    u     = db.users.get(uid)
    uname = escape_html(u.first_name or str(uid)) if u else str(uid)
    if not files:
        await _edit_or_send(
            update, f"{Icon.FOLDER} <b>ملفات {uname}</b>\nلا توجد ملفات.",
            InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} رجوع", f"admin:user:{uid}")]]),
        )
        return
    items: List[Tuple[str, str]] = []
    for f in sorted(files, key=lambda x: x.upload_date, reverse=True):
        flag  = "●" if pm.is_running(f.file_id) else "○"
        pending_flag = " ⏳" if f.pending_approval and f.approval_status == "pending" else ""
        items.append((f"{flag}{pending_flag} {shorten(f.file_name, 28)} · {format_size(f.size)}", f"file:open:{f.file_id}"))
    kb   = kb_paginated(items, page, 8, f"admin:user_files_page:{uid}", f"admin:user:{uid}")
    total_size = sum(f.size for f in files)
    text = (
        f"{Icon.FOLDER} <b>ملفات {uname}</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"ID: <code>{uid}</code>\n"
        f"العدد: <b>{len(files)}</b> | الحجم: <b>{format_size(total_size)}</b>"
    )
    await _edit_or_send(update, text, kb)


@admin_only
async def admin_ai_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    files_with_ai = [(fid, hf) for fid, hf in db.files.items() if hf.ai_analysis]
    text = (
        f"{Icon.AI} <b>تقارير الذكاء الاصطناعي</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"ملفات تم تحليلها: <b>{len(files_with_ai)}</b> / {len(db.files)}\n\n"
    )
    for fid, hf in files_with_ai[-10:]:
        owner = db.users.get(hf.owner_id)
        ownr  = f"@{owner.username}" if owner and owner.username else str(hf.owner_id)
        text += f"• <code>{shorten(hf.file_name, 20)}</code> ({ownr}): {escape_html(hf.ai_analysis[:60])}\n"
    await _edit_or_send(
        update, text,
        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} لوحة الإدارة", "admin:panel")]]),
    )


@admin_only
async def admin_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"{Icon.CHANNEL} <b>إدارة قنوات الاشتراك الإجباري</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الكلي: <b>{len(db.channels)}</b> | المفعّل: <b>{len(db.all_channels(True))}</b>"
    )
    await _edit_or_send(update, text, kb_channels_admin())


@admin_only
async def admin_channel_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_CHAN_ADD] = True
    text = (
        f"{Icon.CHANNEL} أرسل القناة:\n"
        f"• <code>@channel_username</code>\n"
        f"• معرّف رقمي مثل <code>-1001234567890</code>"
    )
    await _edit_or_send(
        update, text,
        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:channels")]]),
    )


async def admin_channel_add_save(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  raw: str) -> None:
    raw = raw.strip()
    if not (raw.startswith("@") or raw.lstrip("-").isdigit()):
        await update.message.reply_text(f"{Icon.CROSS} صيغة غير صحيحة.")
        return
    chat_id = raw; title = raw; invite = ""
    try:
        chat    = await context.bot.get_chat(chat_id)
        title   = chat.title or chat.username or raw
        try: invite = await context.bot.export_chat_invite_link(chat.id)
        except: invite = f"https://t.me/{chat.username}" if chat.username else ""
        chat_id = f"@{chat.username}" if chat.username else str(chat.id)
    except Exception as e:
        await update.message.reply_text(f"{Icon.WARN} لم أستطع جلب القناة: {e}")
    ch = Channel(chat_id=chat_id, title=title, invite_link=invite,
                 added_by=update.effective_user.id, added_at=now_iso(), enabled=True)
    db.add_channel(ch)
    context.user_data.pop(ST_AWAIT_CHAN_ADD, None)
    await update.message.reply_text(
        f"{Icon.CHECK} أضيفت القناة: <b>{escape_html(title)}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.CHANNEL} القنوات", "admin:channels")]]),
    )


@admin_only
async def admin_channel_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                chat_id: str) -> None:
    ch = db.channels.get(chat_id)
    if ch: ch.enabled = not ch.enabled; db.save(force=True)
    await admin_channels(update, context)


@admin_only
async def admin_channel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                chat_id: str) -> None:
    db.remove_channel(chat_id)
    await admin_channels(update, context)


@admin_only
async def admin_settings_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _edit_or_send(
        update,
        f"{Icon.SETTINGS} <b>إعدادات البوت</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nاضغط أي زر لتعديله.",
        kb_settings_admin(),
    )


@admin_only
async def admin_settings_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 key: str) -> None:
    if key in db.settings and isinstance(db.settings[key], bool):
        db.settings[key] = not db.settings[key]
        db.save(force=True)
    await admin_settings_view(update, context)


@admin_only
async def admin_settings_num_start(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    key: str) -> None:
    context.user_data[ST_AWAIT_SET_NUM] = key
    await _edit_or_send(
        update, f"{Icon.EDIT} أرسل القيمة الرقمية الجديدة لـ <b>{escape_html(key)}</b>:",
        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:settings")]]),
    )


@admin_only
async def admin_settings_text_start(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     key: str) -> None:
    context.user_data[ST_AWAIT_SET_TEXT] = key
    await _edit_or_send(
        update, f"{Icon.EDIT} أرسل النص الجديد لـ <b>{escape_html(key)}</b>:",
        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:settings")]]),
    )


@admin_only
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_BROADCAST] = "all"
    text = f"{Icon.BROADCAST} <b>إرسال بث</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nأرسل الرسالة الآن."
    kb = InlineKeyboardMarkup([
        [btn_success(f"{Icon.USERS} كل المستخدمين",   "broadcast:target:all"),
         btn_primary(f"{Icon.PREMIUM} البريميوم فقط", "broadcast:target:premium")],
        [btn_primary(f"{Icon.NEW} الجدد (7 أيام)",    "broadcast:target:new")],
        [btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")],
    ])
    await _edit_or_send(update, text, kb)


async def admin_broadcast_do(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = context.user_data.pop(ST_AWAIT_BROADCAST, "all")
    msg    = update.message
    if target == "premium": recipients = db.get_premium_users()
    elif target == "new":   recipients = db.get_new_users(7)
    else:                   recipients = db.all_users()
    sent = 0; failed = 0
    throttle = max(1, int(db.settings.get("broadcast_throttle_ms", 50))) / 1000.0
    progress = await msg.reply_text(f"{Icon.BROADCAST} جاري البث لـ {len(recipients)} مستخدم…")
    for u in recipients:
        try: await msg.copy(chat_id=u.user_id); sent += 1
        except: failed += 1
        if (sent + failed) % 25 == 0:
            try:
                await progress.edit_text(
                    f"{Icon.BROADCAST} {progress_bar(int((sent+failed)/len(recipients)*100))} "
                    f"{sent} / {failed}")
            except: pass
        await asyncio.sleep(throttle)
    db.broadcast_history.append({"by": update.effective_user.id, "at": now_iso(),
                                  "sent": sent, "failed": failed, "target": target})
    db.stats["total_broadcasts"] = db.stats.get("total_broadcasts", 0) + 1
    db.save(force=True)
    await progress.edit_text(
        f"{Icon.CHECK} انتهى البث.\nنُجح: <b>{sent}</b> | فشل: <b>{failed}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.CROWN} لوحة الإدارة", "admin:panel")]]),
    )


@admin_only
async def admin_addpts_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_ADDPTS_ID] = True
    await _edit_or_send(update, f"{Icon.PLUS} أرسل آيدي المستخدم:",
                        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")]]))


@admin_only
async def admin_subpts_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_SUBPTS_ID] = True
    await _edit_or_send(update, f"{Icon.MINUS} أرسل آيدي المستخدم:",
                        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")]]))


@admin_only
async def admin_ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_BAN_ID] = True
    await _edit_or_send(update, f"{Icon.BAN} أرسل آيدي المستخدم للحظر:",
                        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")]]))


@admin_only
async def admin_unban_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_UNBAN_ID] = True
    await _edit_or_send(update, f"{Icon.UNBAN} أرسل آيدي المستخدم لفك الحظر:",
                        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")]]))


@admin_only
async def admin_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_SEARCH] = True
    await _edit_or_send(update, f"{Icon.SEARCH} أرسل اسم/يوزر/آيدي للبحث:",
                        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")]]))


@admin_only
async def admin_procs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    running = pm.all_running()
    text    = (
        f"{Icon.TERMINAL} <b>العمليات الحيّة ({len(running)})</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{res_monitor.summary_text()}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    rows: List[List[InlineKeyboardButton]] = []
    if not running:
        text += "لا توجد عمليات قيد التشغيل."
    else:
        for fid in running:
            hf = db.get_file(fid)
            if not hf: continue
            text += f"• <code>{fid}</code> {shorten(hf.file_name, 20)} PID={pm.pid(fid)} {pm.uptime(fid)}\n"
            rows.append([
                btn_danger (f"{Icon.STOP} {shorten(hf.file_name, 15)}", f"file:stop:{fid}"),
                btn_primary(f"{Icon.TERMINAL}", f"file:log:{fid}"),
                btn_warning(f"{Icon.RESTART}", f"file:restart:{fid}"),
            ])
    rows.append([
        btn_success(f"{Icon.DANGER} إيقاف الكل", "admin:stop_all"),
        btn_primary(f"{Icon.REFRESH} تحديث",     "admin:procs"),
    ])
    rows.append([btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")])
    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))


@admin_only
async def admin_stop_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    count = pm.stop_all()
    await _edit_or_send(update, f"{Icon.STOP} تم إيقاف <b>{count}</b> عملية.",
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")]]))


@admin_only
async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.save(force=True)
    bk_path = os.path.join(BACKUP_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
    try:
        with zipfile.ZipFile(bk_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.exists(DATABASE_FILE):
                zf.write(DATABASE_FILE, os.path.basename(DATABASE_FILE))
            for root, _, files in os.walk(FILES_DIR):
                for fn in files:
                    full = os.path.join(root, fn)
                    zf.write(full, os.path.relpath(full, "."))
        with open(bk_path, "rb") as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=InputFile(f, filename=os.path.basename(bk_path)),
                caption=f"{Icon.DOWNLOAD} نسخة احتياطية {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )
    except Exception as e:
        await _reply_anywhere(update, f"{Icon.CROSS} فشل النسخ: {e}")


@admin_only
async def admin_maint_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.settings["maintenance_mode"] = not db.settings.get("maintenance_mode", False)
    db.save(force=True)
    state = "مفعّل" if db.settings["maintenance_mode"] else "معطّل"
    await _edit_or_send(update, f"{Icon.TOOLS} وضع الصيانة: <b>{state}</b>",
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")]]))


@admin_only
async def admin_sysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    py       = sys.version.split()[0]
    uptime_s = int(time.time() - _bot_start_time)
    h, r     = divmod(uptime_s, 3600); m, s = divmod(r, 60)
    text = (
        f"{Icon.SERVER} <b>معلومات النظام</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Python:         <code>{py}</code>\n"
        f"النظام:         <code>{platform.system()} {platform.release()}</code>\n"
        f"المعالج:        <code>{platform.machine()}</code>\n"
        f"مدة تشغيل البوت: <b>{h}س {m}د {s}ث</b>\n"
        f"المسار:         <code>{escape_html(os.getcwd())}</code>\n"
        f"المستخدمون:    <b>{len(db.users)}</b>\n"
        f"الملفات:       <b>{len(db.files)}</b>\n"
        f"العمليات:      <b>{len(pm.all_running())}</b>\n"
        f"الإصدار:       <b>{BOT_VERSION}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{res_monitor.summary_text()}"
    )
    await _edit_or_send(
        update, text,
        InlineKeyboardMarkup([
            [btn_primary(f"{Icon.REFRESH} تحديث", "admin:sysinfo")],
            [btn_secondary(f"{Icon.BACK} رجوع",   "admin:panel")],
        ]),
    )


@admin_only
async def admin_broadcast_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    h    = db.broadcast_history[-20:]
    text = f"{Icon.LIST} <b>سجل البث</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if not h: text += "لا يوجد سجل."
    else:
        for b in reversed(h):
            tgt_l = {"all": "الكل", "premium": "البريميوم", "new": "الجدد"}.get(b.get("target",""), "—")
            text += f"• {format_dt(b.get('at',''))} — {b.get('sent',0)}/{b.get('failed',0)} — [{tgt_l}]\n"
    await _edit_or_send(update, text,
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")]]))


@admin_only
async def admin_bwords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = f"{Icon.SHIELD} <b>الكلمات المحظورة</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += ("\n".join(f"• <code>{escape_html(w)}</code>" for w in db.banned_words[:50])
             if db.banned_words else "لا توجد.")
    rows = [
        [btn_success(f"{Icon.PLUS} إضافة",     "admin:bword_add"),
         btn_danger (f"{Icon.DELETE} مسح الكل", "admin:bword_clear")],
        [btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")],
    ]
    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))


@admin_only
async def admin_bword_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_BWORD] = True
    await _edit_or_send(update, f"{Icon.SHIELD} أرسل الكلمة المراد حظرها:",
                        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:bwords")]]))


@admin_only
async def admin_bword_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.banned_words = []
    db.save(force=True)
    await admin_bwords(update, context)


@admin_only
async def admin_restore_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_restore"] = True
    await _edit_or_send(
        update,
        f"{Icon.UPLOAD} <b>استعادة نسخة احتياطية</b>\nأرسل ملف backup_*.zip",
        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")]]),
    )


@admin_only
async def admin_codes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = f"{Icon.CODE} <b>أكواد النقاط</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if not db.promo_codes: text += "لا توجد أكواد."
    else:
        for code, data in list(db.promo_codes.items())[:25]:
            used  = len(data.get("used_by", []))
            limit = data.get("limit", 1)
            bar   = progress_bar(int(used / max(limit, 1) * 100), 6)
            text += f"• <code>{escape_html(code)}</code> — <b>{data.get('points',0)}</b>pts [{bar} {used}/{limit}]\n"
    rows = [
        [btn_success(f"{Icon.PLUS} إضافة كود",  "code:add"),
         btn_danger (f"{Icon.DELETE} مسح الكل", "code:clear")],
        [btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")],
    ]
    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))


@admin_only
async def admin_code_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[ST_AWAIT_CODE_CREATE] = True
    await _edit_or_send(
        update,
        f"{Icon.CODE} أرسل الكود بهذا الشكل:\n<code>CODE 10 100</code>\nالاسم ← النقاط ← عدد الاستخدام",
        InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:codes")]]),
    )


async def admin_code_add_save(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               raw: str) -> None:
    context.user_data.pop(ST_AWAIT_CODE_CREATE, None)
    parts = raw.strip().split()
    if len(parts) < 2:
        await update.message.reply_text(f"{Icon.CROSS} الصيغة: CODE POINTS LIMIT")
        return
    code   = re.sub(r"[^A-Za-z0-9_-]", "", parts[0]).upper()[:32]
    points = int(parts[1])
    limit  = int(parts[2]) if len(parts) > 2 else 1
    db.promo_codes[code] = {
        "points": points, "limit": max(1, limit), "used_by": [],
        "active": True, "created_by": update.effective_user.id, "created_at": now_iso(),
    }
    db.save(force=True)
    await send_named_sticker(update, context, "admin_action")
    await update.message.reply_text(
        f"{Icon.CHECK} تم إنشاء الكود <code>{escape_html(code)}</code> — <b>{points}</b>pts / <b>{limit}</b>x",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.CODE} الأكواد", "admin:codes")]]),
    )


@admin_only
async def admin_codes_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.promo_codes = {}
    db.save(force=True)
    await admin_codes(update, context)


@admin_only
async def admin_security(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    events = db.security_events[-20:]
    text   = (
        f"{Icon.SHIELD} <b>مركز حماية الاستضافة والـ API</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الحماية:       <b>{'مفعّلة' if db.settings.get('strict_hosting_security') else 'معطّلة'}</b>\n"
        f"حماية API:     <b>{'مفعّلة' if db.settings.get('api_protection_enabled') else 'معطّلة'}</b>\n"
        f"حظر عند الخطر: <b>{'مفعّل' if db.settings.get('ban_on_confirmed_danger') else 'معطّل'}</b>\n"
        f"أحداث أمنية:  <b>{len(db.security_events)}</b>\n"
    )
    if events:
        text += "\nآخر الأحداث:\n"
        for e in events[-10:]:
            banned_str = " [حُظر]" if e.get("banned") else ""
            text += f"• {format_dt(e.get('at',''))} ID={e.get('user_id')} {shorten(e.get('file',''),15)}{banned_str}\n"
    rows = [
        [btn_toggle("حماية الاستضافة", "adminset:toggle:strict_hosting_security",
                    bool(db.settings.get("strict_hosting_security"))),
         btn_toggle("حماية API",       "adminset:toggle:api_protection_enabled",
                    bool(db.settings.get("api_protection_enabled")))],
        [btn_toggle("حظر عند خطر",    "adminset:toggle:ban_on_confirmed_danger",
                    bool(db.settings.get("ban_on_confirmed_danger"))),
         btn_toggle("تحليل AI",        "adminset:toggle:ai_analysis_enabled",
                    bool(db.settings.get("ai_analysis_enabled")))],
        [btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")],
    ]
    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))


@admin_only
async def admin_stickers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stickers = db.settings.get("stickers") or {}
    names = [
        ("login_success", "دخول ناجح"), ("upload_success", "رفع ناجح"),
        ("hosting_started", "تشغيل"), ("installing_libs", "تثبيت مكتبات"),
        ("share_link", "مشاركة"), ("points_added", "نقاط"),
        ("security_blocked", "رفض خطر"), ("support_error", "خطأ"),
        ("admin_action", "إجراء إداري"), ("subscription_ok", "اشتراك"),
        ("premium_granted", "بريميوم"), ("leaderboard", "متصدرون"),
    ]
    text = f"{Icon.TOOLS} <b>الملصقات</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for key, label in names:
        val   = stickers.get(key) or STICKERS.get(key) or ""
        state = f"<code>{escape_html(val[:30])}…</code>" if val else "<i>غير محدد</i>"
        text += f"• <b>{escape_html(label)}</b>: {state}\n"
    await _edit_or_send(update, text,
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")]]))


@admin_only
async def admin_activity_log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log  = db.activity_log[-30:]
    text = f"{Icon.ALERT} <b>سجل النشاط (آخر 30)</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if not log: text += "لا يوجد نشاط."
    else:
        for entry in reversed(log):
            uid_s    = f"<code>{entry.get('user_id', '—')}</code>" if entry.get("user_id") else "—"
            detail_s = escape_html(shorten(entry.get("detail", ""), 30))
            text    += f"• {format_dt(entry.get('at',''))} [{escape_html(entry.get('action',''))}] {uid_s} {detail_s}\n"
    await _edit_or_send(update, text,
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")]]))


@admin_only
async def admin_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prem_users = db.get_premium_users()
    text = (
        f"{Icon.PREMIUM} <b>إدارة البريميوم</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"المستخدمون البريميوم: <b>{len(prem_users)}</b>\n\n"
        + ("\n".join(f"• <code>{u.user_id}</code> @{escape_html(u.username or '—')} حتى {format_dt(u.premium_until)}"
                     for u in prem_users[:15])
           if prem_users else "لا يوجد مستخدمون بريميوم.")
    )
    rows = [
        [btn_success(f"{Icon.PREMIUM} منح بريميوم", "premium:grant"),
         btn_danger (f"{Icon.CROSS} سحب بريميوم",  "premium:revoke")],
        [btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")],
    ]
    await _edit_or_send(update, text, InlineKeyboardMarkup(rows))


@admin_only
async def admin_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = text_leaderboard("points")
    kb   = InlineKeyboardMarkup([
        [btn_primary(f"{Icon.DIAMOND} النقاط",  "leaderboard:points"),
         btn_primary(f"{Icon.UPLOAD} الرفع",    "leaderboard:uploads"),
         btn_primary(f"{Icon.GIFT} الدعوات",    "leaderboard:invites")],
        [btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")],
    ])
    await _edit_or_send(update, text, kb)


@admin_only
async def admin_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tasks = list(db.scheduled_tasks.values())
    text  = f"{Icon.CALENDAR} <b>المهام المجدولة ({len(tasks)})</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if not tasks: text += "لا توجد مهام مجدولة."
    else:
        for t in tasks[:20]:
            hf    = db.get_file(t.file_id)
            fname = hf.file_name if hf else t.file_id
            text += (f"• <code>{t.task_id}</code> {shorten(fname, 20)} "
                     f"{'✅' if t.enabled else '❌'} وقت: {format_dt(t.run_at)}\n")
    await _edit_or_send(update, text,
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")]]))


# ═══════════════════════════════════════════════════════════════════════════════
# 🔁  المهام الدورية
# ═══════════════════════════════════════════════════════════════════════════════

async def auto_restart_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        for fid, hf in list(db.files.items()):
            if hf.auto_restart and not pm.is_running(fid):
                work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, fid)
                ok, _    = pm.start(fid, work_dir, hf.entry_file or hf.file_name)
                if ok:
                    hf.run_count += 1; hf.last_run = now_iso(); hf.start_time = now_iso()
                    db.add_file(hf)
    except Exception as e:
        logger.warning("auto_restart_job: %s", e)


async def auto_backup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        db.save(force=True)
        backups = sorted(f for f in os.listdir(BACKUP_DIR) if f.startswith("auto_"))
        while len(backups) > 10:
            try: os.remove(os.path.join(BACKUP_DIR, backups.pop(0)))
            except: pass
        path = os.path.join(BACKUP_DIR, f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.exists(DATABASE_FILE):
                zf.write(DATABASE_FILE, os.path.basename(DATABASE_FILE))
    except Exception as e:
        logger.warning("auto_backup_job: %s", e)


async def premium_expiry_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        now = datetime.now()
        for u in db.all_users():
            if u.is_premium and u.premium_until:
                try:
                    exp = datetime.fromisoformat(u.premium_until)
                    if exp < now and u.premium_until != "9999-12-31T00:00:00":
                        u.is_premium = False; u.premium_until = ""
                        db.update_user(u, save=False)
                        try:
                            await context.bot.send_message(
                                u.user_id, f"{Icon.WARN} انتهت عضويتك البريميوم.")
                        except: pass
                except: pass
        db.save(force=True)
    except Exception as e:
        logger.warning("premium_expiry_job: %s", e)


async def auto_cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        cleanup_days = int(db.settings.get("auto_cleanup_days", 30))
        if cleanup_days <= 0: return
        cutoff = time.time() - cleanup_days * 86400
        for fn in os.listdir(TEMP_DIR):
            fp = os.path.join(TEMP_DIR, fn)
            if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
                try: os.remove(fp)
                except: pass
    except Exception as e:
        logger.warning("auto_cleanup_job: %s", e)


async def scheduled_tasks_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not db.settings.get("schedule_enabled", True): return
    try:
        now = datetime.now()
        for task_id, task in list(db.scheduled_tasks.items()):
            if not task.enabled: continue
            try: run_at = datetime.fromisoformat(task.run_at)
            except: continue
            if run_at <= now:
                hf = db.get_file(task.file_id)
                if hf:
                    work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, task.file_id)
                    ok, _    = pm.start(task.file_id, work_dir, hf.entry_file or hf.file_name)
                    if ok: hf.run_count += 1; hf.last_run = now_iso(); db.add_file(hf)
                task.last_triggered = now_iso()
                if task.repeat == "once": task.enabled = False
                elif task.repeat == "daily":
                    task.run_at = (datetime.fromisoformat(task.run_at) + timedelta(days=1)).isoformat()
                elif task.repeat == "hourly":
                    task.run_at = (datetime.fromisoformat(task.run_at) + timedelta(hours=1)).isoformat()
                db.scheduled_tasks[task_id] = task
                db.mark_dirty()
    except Exception as e:
        logger.warning("scheduled_tasks_job: %s", e)


# ═══════════════════════════════════════════════════════════════════════════════
# 🌐 Keep-Alive
# ═══════════════════════════════════════════════════════════════════════════════

def keep_alive() -> None:
    try:
        from flask import Flask
    except ImportError:
        logger.warning("Flask غير مثبت — تخطي keep_alive")
        return
    port = int(os.environ.get("PORT", "8080"))
    app  = Flask("keep_alive")

    @app.route("/")
    def _home():
        return (f"<h2>{BOT_NAME} v{BOT_VERSION}</h2>"
                f"<p>Users: {len(db.users)} | Files: {len(db.files)} | Running: {len(pm.all_running())}</p>")

    @app.route("/health")
    def _health():
        return {"ok": True, "bot": BOT_NAME, "version": BOT_VERSION,
                "users": len(db.users), "files": len(db.files),
                "running": len(pm.all_running()), "ts": int(time.time())}

    def _run():
        try: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
        except Exception as e: logger.warning("keep_alive crashed: %s", e)

    threading.Thread(target=_run, daemon=True, name="keep_alive").start()
    logger.info("keep_alive يعمل على المنفذ %s", port)


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀  نقطة الانطلاق
# ═══════════════════════════════════════════════════════════════════════════════

_bot_start_time = time.time()


async def post_init(application: Application) -> None:
    try:
        await application.bot.set_my_commands([
            BotCommand("start", "القائمة الرئيسية"),
            BotCommand("help",  "مساعدة"),
        ])
    except Exception as e:
        logger.warning("set_my_commands: %s", e)
    logger.info("%s v%s جاهز!", BOT_NAME, BOT_VERSION)
    logger.info("👑 المطور: @%s", DEVELOPER_USERNAME)
    for adm in ADMIN_IDS:
        try:
            await application.bot.send_message(
                adm,
                f"{Icon.ROCKET} <b>{BOT_NAME} v{BOT_VERSION}</b> بدأ التشغيل!\n"
                f"المستخدمون: <b>{len(db.users)}</b> | الملفات: <b>{len(db.files)}</b>\n"
                f"{Icon.AI} ذكاء اصطناعي | {Icon.API_PROTECT} حماية API\n"
                f"🆔 معرف النسخة: {INSTANCE_ID}\n"
                f"👑 المطور: @{DEVELOPER_USERNAME}",
                parse_mode=ParseMode.HTML,
            )
        except:
            pass


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    if isinstance(err, Conflict):
        logger.warning("⚠️ تعارض: نسخة أخرى من البوت تعمل بنفس التوكن. هذا طبيعي إذا كنت تشغل نسختين.")
        return
    logger.exception("خطأ غير معالج: %s", err)


def main() -> None:
    global _bot_start_time
    _bot_start_time = time.time()

    if BOT_TOKEN in ("", "ضع_توكن_البوت_هنا"):
        print("\n❌ يجب ضبط BOT_TOKEN في الملف أو كمتغير بيئة BOT_TOKEN.\n")
        sys.exit(1)

    print(f"\n🚀 تشغيل النسخة: {INSTANCE_ID}")
    print(f"📂 قاعدة البيانات: {DATABASE_FILE}")
    print(f"📂 مجلد الملفات: {FILES_DIR}")
    print(f"📂 مجلد السجلات: {LOGS_DIR}")
    print(f"👑 المطور: @{DEVELOPER_USERNAME}")
    print("🔐 BOT_TOKEN يُقرأ من متغير البيئة BOT_TOKEN.")
    print("💡 يمكنك تشغيل نسخة أخرى بتعيين PORT مختلف:\n   PORT=8081 python bot.py\n")

    app = (Application.builder().token(BOT_TOKEN).post_init(post_init).build())

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_error_handler(global_error_handler)

    try:
        jq = app.job_queue
        if jq:
            jq.run_repeating(auto_restart_job,   interval=60,    first=30)
            jq.run_repeating(auto_backup_job,     interval=3600,  first=600)
            jq.run_repeating(premium_expiry_job,  interval=3600,  first=300)
            jq.run_repeating(auto_cleanup_job,    interval=86400, first=7200)
            jq.run_repeating(scheduled_tasks_job, interval=60,    first=60)
    except Exception as e:
        logger.warning("job queue init: %s", e)

    logger.info("🚀 بدء تشغيل %s v%s ...", BOT_NAME, BOT_VERSION)
    keep_alive()
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯  موجّه ضغطات الأزرار
# ═══════════════════════════════════════════════════════════════════════════════

@maintenance_gate
@check_banned
@rate_limit
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q: return
    try: await q.answer()
    except: pass
    data = q.data or ""
    uid  = q.from_user.id

    if data not in ("check_sub", "noop") and not is_admin(uid):
        if not await enforce_subscription(update, context): return

    try:
        if data == "noop": return
        if data == "check_sub":
            ok, missing = await check_subscription(uid, context.bot)
            if ok:
                me = await context.bot.get_me()
                u  = db.get_user(uid)
                await send_named_sticker(update, context, "subscription_ok")
                await _edit_or_send(update, text_welcome(u, me.username), kb_main_menu(uid))
            else:
                kb = subscription_keyboard(missing)
                await update.callback_query.edit_message_reply_markup(reply_markup=kb)
            return

        # ─── أزرار الموافقة والرفض ──────────────────────────────
        if data.startswith("approve:"):
            file_id = data[8:]
            hf = db.get_file(file_id)
            if not hf:
                await _edit_or_send(update, f"{Icon.CROSS} الملف غير موجود.", kb_back("admin:panel"))
                return
            
            if hf.pending_approval and hf.approval_status == "pending":
                hf.pending_approval = False
                hf.approval_status = "approved"
                db.add_file(hf)
                
                try:
                    await context.bot.send_message(
                        hf.owner_id,
                        f"{Icon.APPROVAL} <b>تمت الموافقة على ملفك!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"الملف: <code>{escape_html(hf.file_name)}</code>\n"
                        f"{Icon.PLAY} يمكنك الآن تشغيله من خلال ملفاتي.",
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup([
                            [btn_primary(f"{Icon.FOLDER} ملفاتي", "menu:myfiles")]
                        ]),
                    )
                except Exception as e:
                    logger.warning(f"فشل إعلام المستخدم بالموافقة: {e}")
                
                await _edit_or_send(update, f"{Icon.APPROVAL} تمت الموافقة على الملف <code>{escape_html(hf.file_name)}</code>",
                                   InlineKeyboardMarkup([
                                       [btn_primary(f"{Icon.FILE} فتح الملف", f"file:open:{file_id}"),
                                        btn_secondary(f"{Icon.BACK} لوحة الإدارة", "admin:panel")]
                                   ]))
            else:
                await _edit_or_send(update, f"{Icon.INFO} هذا الملف لم يعد في انتظار الموافقة.",
                                   kb_back("admin:panel"))
            return

        if data.startswith("reject:"):
            file_id = data[7:]
            hf = db.get_file(file_id)
            if not hf:
                await _edit_or_send(update, f"{Icon.CROSS} الملف غير موجود.", kb_back("admin:panel"))
                return
            
            if hf.pending_approval and hf.approval_status == "pending":
                work_dir = os.path.dirname(hf.stored_path) or os.path.join(FILES_DIR, file_id)
                shutil.rmtree(work_dir, ignore_errors=True)
                db.remove_file(file_id)
                
                try:
                    await context.bot.send_message(
                        hf.owner_id,
                        f"{Icon.REJECT} <b>تم رفض ملفك</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"الملف: <code>{escape_html(hf.file_name)}</code>\n"
                        f"{Icon.WARN} لم تتم الموافقة على رفع هذا الملف.",
                        parse_mode=ParseMode.HTML,
                    )
                except Exception as e:
                    logger.warning(f"فشل إعلام المستخدم بالرفض: {e}")
                
                await _edit_or_send(update, f"{Icon.REJECT} تم رفض الملف <code>{escape_html(hf.file_name)}</code>",
                                   InlineKeyboardMarkup([
                                       [btn_secondary(f"{Icon.BACK} لوحة الإدارة", "admin:panel")]
                                   ]))
            else:
                await _edit_or_send(update, f"{Icon.INFO} هذا الملف لم يعد في انتظار الموافقة.",
                                   kb_back("admin:panel"))
            return

        # ─── أزرار التبديل الجديدة ──────────────────────────────
        if data == "admin:toggle_approval":
            await admin_toggle_approval(update, context)
            return
        if data == "admin:toggle_security":
            await admin_toggle_security(update, context)
            return

        # ─── الملفات قيد المراجعة ──────────────────────────────
        if data == "admin:pending":
            await admin_pending_files(update, context)
            return

        # ─── القائمة الرئيسية ───
        if data == "menu:main":
            me = await context.bot.get_me()
            u = db.get_user(uid)
            await _edit_or_send(update, text_welcome(u, me.username), kb_main_menu(uid))
            return
        if data == "menu:upload":
            await upload_start(update, context)
            return
        if data == "menu:myfiles":
            await show_my_files(update, context, 0)
            return
        if data == "menu:points":
            await show_points(update, context)
            return
        if data == "menu:invite":
            await show_invite(update, context)
            return
        if data == "menu:buy":
            await show_buy_points(update, context)
            return
        if data == "menu:stats":
            await show_stats(update, context)
            return
        if data == "menu:settings":
            await show_settings(update, context)
            return
        if data == "menu:support":
            await show_support(update, context)
            return
        if data == "menu:about":
            await show_about(update, context)
            return
        if data == "menu:security":
            await show_security_info(update, context)
            return
        if data == "menu:leaderboard":
            await show_leaderboard(update, context)
            return
        if data == "menu:redeem":
            await redeem_code_start(update, context)
            return

        # ─── صفحات الملفات ───
        if data.startswith("myfiles:page:"):
            page = int(data.split(":")[-1])
            await show_my_files(update, context, page)
            return

        # ─── إجراءات الملفات ───
        if data.startswith("file:open:"):
            await open_file(update, context, data[10:])
            return
        if data.startswith("file:run:"):
            await file_run(update, context, data[9:])
            return
        if data.startswith("file:stop:"):
            await file_stop(update, context, data[10:])
            return
        if data.startswith("file:restart:"):
            await file_restart(update, context, data[13:])
            return
        if data.startswith("file:log:"):
            await file_log(update, context, data[9:])
            return
        if data.startswith("file:export_log:"):
            await file_export_log(update, context, data[16:])
            return
        if data.startswith("file:install:"):
            await file_install(update, context, data[13:])
            return
        if data.startswith("file:terminal:"):
            await file_terminal_start(update, context, data[13:])
            return
        if data.startswith("file:del:"):
            await file_delete_confirm(update, context, data[9:])
            return
        if data.startswith("file:del_yes:"):
            await file_delete_do(update, context, data[13:])
            return
        if data.startswith("file:zip:"):
            await file_zip(update, context, data[9:])
            return
        if data.startswith("file:auto:"):
            await file_toggle_auto(update, context, data[10:])
            return
        if data.startswith("file:public:"):
            await file_toggle_public(update, context, data[12:])
            return
        if data.startswith("file:share:"):
            await file_share(update, context, data[11:])
            return
        if data.startswith("file:desc:"):
            await file_desc_start(update, context, data[10:])
            return
        if data.startswith("file:ai:"):
            await file_ai_analyze(update, context, data[8:])
            return

        # ─── شراء ───
        if data.startswith("buy:"):
            parts = data.split(":")
            await initiate_purchase(update, context, int(parts[1]), int(parts[2]))
            return

        # ─── Leaderboard ───
        if data.startswith("leaderboard:"):
            await show_leaderboard(update, context, data.split(":")[-1])
            return

        # ─── إعدادات المستخدم ───
        if data == "userset:toggle:notif":
            u = db.get_user(uid)
            u.notifications_enabled = not u.notifications_enabled
            db.update_user(u)
            await show_settings(update, context)
            return
        if data == "userset:export":
            u = db.get_user(uid)
            data_export = json.dumps(asdict(u), ensure_ascii=False, indent=2)
            await context.bot.send_document(
                chat_id=uid,
                document=InputFile(io.BytesIO(data_export.encode("utf-8")),
                                    filename=f"user_{uid}_data.json"),
                caption=f"{Icon.DOWNLOAD} بياناتك",
            )
            return

        # ─── البث ───
        if data.startswith("broadcast:target:"):
            target = data.split(":")[-1]
            context.user_data[ST_AWAIT_BROADCAST] = target
            await _edit_or_send(update,
                                 f"{Icon.BROADCAST} أرسل رسالة البث الآن ({target}):",
                                 InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")]]))
            return

        # ─── لوحة الإدارة ───
        if data == "admin:panel":
            await admin_panel(update, context)
            return
        if data == "admin:stats":
            await admin_stats(update, context)
            return
        if data.startswith("admin:users"):
            page = int(data.split(":")[-1]) if "page" in data else 0
            await admin_users(update, context, page)
            return
        if data.startswith("admin:files"):
            page = int(data.split(":")[-1]) if "page" in data else 0
            await admin_files(update, context, page)
            return
        if data.startswith("admin:user_files_page:"):
            parts = data.split(":")
            uid_t = int(parts[-2]); page = int(parts[-1])
            await admin_user_files_list(update, context, uid_t, page)
            return
        if data.startswith("admin:user_files:"):
            await admin_user_files_list(update, context, int(data.split(":")[-1]), 0)
            return
        if data.startswith("admin:user:"):
            await admin_user_details(update, context, int(data.split(":")[-1]))
            return
        if data == "admin:channels":
            await admin_channels(update, context)
            return
        if data == "admin:settings":
            await admin_settings_view(update, context)
            return
        if data == "admin:broadcast":
            await admin_broadcast_start(update, context)
            return
        if data == "admin:addpts":
            await admin_addpts_start(update, context)
            return
        if data == "admin:subpts":
            await admin_subpts_start(update, context)
            return
        if data.startswith("admin:addpts_user:"):
            uid_t = int(data.split(":")[-1])
            context.user_data["addpts_target"] = uid_t
            context.user_data[ST_AWAIT_ADDPTS_AMT] = True
            await _edit_or_send(update, f"{Icon.PLUS} أرسل عدد النقاط للإضافة للمستخدم <code>{uid_t}</code>:",
                                InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", f"admin:user:{uid_t}")]]))
            return
        if data.startswith("admin:subpts_user:"):
            uid_t = int(data.split(":")[-1])
            context.user_data["subpts_target"] = uid_t
            context.user_data[ST_AWAIT_SUBPTS_AMT] = True
            await _edit_or_send(update, f"{Icon.MINUS} أرسل عدد النقاط للخصم من <code>{uid_t}</code>:",
                                InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", f"admin:user:{uid_t}")]]))
            return
        if data == "admin:ban":
            await admin_ban_start(update, context)
            return
        if data == "admin:unban":
            await admin_unban_start(update, context)
            return
        if data.startswith("admin:ban_user:"):
            uid_t = int(data.split(":")[-1])
            if is_admin_immortal(uid_t):
                await _edit_or_send(update, f"{Icon.CROWN} المشرف محمي ولا يمكن حظره!", kb_back(f"admin:user:{uid_t}"))
                return
            context.user_data[ST_AWAIT_BAN_REASON] = uid_t
            await _edit_or_send(update, f"{Icon.BAN} أرسل سبب الحظر:",
                                InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", f"admin:user:{uid_t}")]]))
            return
        if data.startswith("admin:unban_user:"):
            uid_t = int(data.split(":")[-1])
            u = db.get_user(uid_t)
            u.is_banned = False; u.ban_reason = ""; u.ban_until = ""
            db.update_user(u)
            db.log_activity("unban", uid, str(uid_t))
            await _edit_or_send(update, f"{Icon.UNBAN} فُكّ حظر <code>{uid_t}</code>.",
                                kb_back(f"admin:user:{uid_t}"))
            return
        if data == "admin:search":
            await admin_search_start(update, context)
            return
        if data == "admin:procs":
            await admin_procs(update, context)
            return
        if data == "admin:stop_all":
            await admin_stop_all(update, context)
            return
        if data == "admin:backup":
            await admin_backup(update, context)
            return
        if data == "admin:restore":
            await admin_restore_info(update, context)
            return
        if data == "admin:maint":
            await admin_maint_toggle(update, context)
            return
        if data == "admin:bwords":
            await admin_bwords(update, context)
            return
        if data == "admin:bword_add":
            await admin_bword_add_start(update, context)
            return
        if data == "admin:bword_clear":
            await admin_bword_clear(update, context)
            return
        if data == "admin:codes":
            await admin_codes(update, context)
            return
        if data == "admin:security":
            await admin_security(update, context)
            return
        if data == "admin:stickers":
            await admin_stickers(update, context)
            return
        if data == "admin:sysinfo":
            await admin_sysinfo(update, context)
            return
        if data == "admin:bhist":
            await admin_broadcast_history(update, context)
            return
        if data == "admin:activity":
            await admin_activity_log(update, context)
            return
        if data == "admin:premium":
            await admin_premium(update, context)
            return
        if data == "admin:leaderboard":
            await admin_leaderboard(update, context)
            return
        if data == "admin:schedule":
            await admin_schedule(update, context)
            return
        if data == "admin:ai_reports":
            await admin_ai_reports(update, context)
            return

        # ─── إعدادات المشرف ───
        if data.startswith("adminset:toggle:"):
            await admin_settings_toggle(update, context, data[16:])
            return
        if data.startswith("adminset:num:"):
            await admin_settings_num_start(update, context, data[13:])
            return
        if data.startswith("adminset:text:"):
            await admin_settings_text_start(update, context, data[14:])
            return

        # ─── القنوات ───
        if data == "chan:add":
            await admin_channel_add_start(update, context)
            return
        if data.startswith("chan:toggle:"):
            await admin_channel_toggle(update, context, data[12:])
            return
        if data.startswith("chan:del:"):
            await admin_channel_delete(update, context, data[9:])
            return

        # ─── الأكواد ───
        if data == "code:add":
            await admin_code_add_start(update, context)
            return
        if data == "code:clear":
            await admin_codes_clear(update, context)
            return

        # ─── البريميوم ───
        if data == "premium:grant":
            context.user_data[ST_AWAIT_PREMIUM_UID] = "grant"
            await _edit_or_send(update, f"{Icon.PREMIUM} أرسل آيدي المستخدم:",
                                InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:premium")]]))
            return
        if data == "premium:revoke":
            context.user_data[ST_AWAIT_PREMIUM_UID] = "revoke"
            await _edit_or_send(update, f"{Icon.CROSS} أرسل آيدي المستخدم:",
                                InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:premium")]]))
            return
        if data.startswith("admin:grant_premium:"):
            uid_t = int(data.split(":")[-1])
            context.user_data[ST_AWAIT_PREMIUM_UID]  = f"grant:{uid_t}"
            context.user_data[ST_AWAIT_PREMIUM_DAYS] = True
            await _edit_or_send(update, f"{Icon.PREMIUM} كم يوم؟ (0 = أبداً):",
                                InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", f"admin:user:{uid_t}")]]))
            return
        if data.startswith("admin:revoke_premium:"):
            uid_t = int(data.split(":")[-1])
            u = db.get_user(uid_t)
            u.is_premium = False; u.premium_until = ""
            db.update_user(u)
            await _edit_or_send(update, f"{Icon.CHECK} سُحب البريميوم من <code>{uid_t}</code>.",
                                kb_back(f"admin:user:{uid_t}"))
            return
        if data.startswith("admin:note_user:"):
            uid_t = int(data.split(":")[-1])
            context.user_data[ST_AWAIT_NOTE] = uid_t
            await _edit_or_send(update, f"{Icon.NOTE} أرسل الملاحظة:",
                                InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", f"admin:user:{uid_t}")]]))
            return

        logger.debug("callback غير معالج: %s", data)

    except Exception as e:
        logger.exception("callback_router error for %s: %s", data, e)
        try: await _edit_or_send(update, f"{Icon.CROSS} خطأ: {escape_html(str(e)[:200])}", kb_back())
        except: pass


# ═══════════════════════════════════════════════════════════════════════════════
# 💬  موجّه الرسائل النصية
# ═══════════════════════════════════════════════════════════════════════════════

@maintenance_gate
@check_banned
@rate_limit
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text or ""
    ud   = context.user_data

    if ud.get(ST_AWAIT_TERMINAL):
        file_id = ud.get(ST_AWAIT_TERMINAL)
        if text.strip().lower() in {"خروج", "exit", "cancel", "إلغاء"}:
            ud.pop(ST_AWAIT_TERMINAL, None)
            await update.message.reply_text(
                f"{Icon.CHECK} تم الخروج من الترمنال.",
                reply_markup=InlineKeyboardMarkup([[btn_primary("⬅️ ملفاتي", "menu:myfiles")]])
            )
            return
        await file_terminal_exec(update, context, file_id, text)
        return

    if ud.get(ST_AWAIT_FILE_DESC):
        file_id = ud.pop(ST_AWAIT_FILE_DESC)
        hf = db.get_file(file_id)
        if hf:
            hf.description = text[:200]
            db.add_file(hf)
            await update.message.reply_text(
                f"{Icon.CHECK} تم تحديث الوصف.",
                reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.FILE} الملف", f"file:open:{file_id}")]]),
            )
        return

    if ud.get(ST_AWAIT_CODE_REDEEM):
        await redeem_code_do(update, context, text)
        return

    if ud.get(ST_AWAIT_CODE_CREATE) and is_admin(user.id):
        await admin_code_add_save(update, context, text)
        return

    if ud.get(ST_AWAIT_CHAN_ADD) and is_admin(user.id):
        await admin_channel_add_save(update, context, text)
        return

    if ud.get(ST_AWAIT_BROADCAST) and is_admin(user.id):
        await admin_broadcast_do(update, context)
        return

    if ud.get(ST_AWAIT_BWORD) and is_admin(user.id):
        ud.pop(ST_AWAIT_BWORD)
        word = text.strip().lower()
        if word and word not in db.banned_words:
            db.banned_words.append(word); db.save(force=True)
        await update.message.reply_text(
            f"{Icon.CHECK} أضيفت الكلمة المحظورة.",
            reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.SHIELD} الكلمات", "admin:bwords")]]),
        )
        return

    if ud.get(ST_AWAIT_SEARCH) and is_admin(user.id):
        ud.pop(ST_AWAIT_SEARCH)
        res  = db.search_users(text)[:20]
        out  = f"{Icon.SEARCH} وُجد <b>{len(res)}</b> نتيجة:\n"
        rows = []
        for u in res:
            flag = Icon.CROWN if is_admin(u.user_id) else (Icon.PREMIUM if u.is_premium else Icon.USER)
            out += f"• {flag} <code>{u.user_id}</code> {escape_html(u.first_name or '')} @{escape_html(u.username or '—')} · {u.points}pts\n"
            rows.append([btn_primary(f"{flag} [{u.user_id}] {shorten(u.first_name or '', 15)}", f"admin:user:{u.user_id}")])
        rows.append([btn_secondary(f"{Icon.BACK} رجوع", "admin:panel")])
        await update.message.reply_text(out, parse_mode=ParseMode.HTML,
                                         reply_markup=InlineKeyboardMarkup(rows))
        return

    if ud.get(ST_AWAIT_ADDPTS_ID) and is_admin(user.id):
        try:
            ud["addpts_target"] = int(text)
            ud.pop(ST_AWAIT_ADDPTS_ID)
            ud[ST_AWAIT_ADDPTS_AMT] = True
            await update.message.reply_text(f"{Icon.PLUS} أرسل عدد النقاط للإضافة:",
                                             reply_markup=InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:panel")]]))
        except:
            await update.message.reply_text(f"{Icon.CROSS} آيدي غير صحيح.")
        return

    if ud.get(ST_AWAIT_ADDPTS_AMT) and is_admin(user.id):
        try:
            amt  = int(text)
            tuid = int(ud.pop("addpts_target"))
            ud.pop(ST_AWAIT_ADDPTS_AMT)
            u = db.get_user(tuid)
            grant_points(u, amt, "admin", note=f"by {user.id}")
            db.update_user(u)
            await update.message.reply_text(
                f"{Icon.CHECK} +{amt} نقطة للمستخدم <code>{tuid}</code>. رصيده: <b>{u.points}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.USER} المستخدم", f"admin:user:{tuid}")]]),
            )
        except Exception as e:
            await update.message.reply_text(f"{Icon.CROSS} {escape_html(str(e))}")
        return

    if ud.get(ST_AWAIT_SUBPTS_ID) and is_admin(user.id):
        try:
            ud["subpts_target"] = int(text); ud.pop(ST_AWAIT_SUBPTS_ID); ud[ST_AWAIT_SUBPTS_AMT] = True
            await update.message.reply_text(f"{Icon.MINUS} أرسل عدد النقاط للخصم:")
        except:
            await update.message.reply_text(f"{Icon.CROSS} آيدي غير صحيح.")
        return

    if ud.get(ST_AWAIT_SUBPTS_AMT) and is_admin(user.id):
        try:
            amt  = int(text)
            tuid = int(ud.pop("subpts_target"))
            ud.pop(ST_AWAIT_SUBPTS_AMT)
            u    = db.get_user(tuid)
            u.points = max(0, u.points - amt)
            db.update_user(u)
            await update.message.reply_text(
                f"{Icon.CHECK} −{amt} نقطة من <code>{tuid}</code>. رصيده: <b>{u.points}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.USER} المستخدم", f"admin:user:{tuid}")]]),
            )
        except Exception as e:
            await update.message.reply_text(f"{Icon.CROSS} {escape_html(str(e))}")
        return

    if ud.get(ST_AWAIT_BAN_ID) and is_admin(user.id):
        try:
            tuid = int(text)
            ud.pop(ST_AWAIT_BAN_ID)
            if is_admin_immortal(tuid):
                await update.message.reply_text(f"{Icon.CROWN} المشرف محمي ولا يمكن حظره!")
                return
            ud[ST_AWAIT_BAN_REASON] = tuid
            await update.message.reply_text(
                f"{Icon.BAN} أرسل سبب الحظر للمستخدم <code>{tuid}</code>:\n(أو - لتخطي)",
                parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"{Icon.CROSS} {escape_html(str(e))}")
        return

    if ud.get(ST_AWAIT_BAN_REASON) is not None and is_admin(user.id):
        tuid   = int(ud.pop(ST_AWAIT_BAN_REASON))
        reason = text if text != "-" else "من لوحة الإدارة"
        u      = db.get_user(tuid)
        u.is_banned = True; u.ban_reason = reason
        db.update_user(u)
        stopped = pm.stop_all_for_user(tuid)
        db.log_activity("ban", user.id, f"{tuid}: {reason}")
        await update.message.reply_text(
            f"{Icon.BAN} حُظر <code>{tuid}</code>. السبب: {escape_html(reason)}\nعمليات موقوفة: <b>{stopped}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.USER} تفاصيله", f"admin:user:{tuid}")]]),
        )
        return

    if ud.get(ST_AWAIT_UNBAN_ID) and is_admin(user.id):
        try:
            tuid = int(text); ud.pop(ST_AWAIT_UNBAN_ID)
            u = db.get_user(tuid)
            u.is_banned = False; u.ban_reason = ""; u.ban_until = ""
            db.update_user(u)
            db.log_activity("unban", user.id, str(tuid))
            await update.message.reply_text(
                f"{Icon.UNBAN} فُكّ حظر <code>{tuid}</code>.", parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.USER} تفاصيله", f"admin:user:{tuid}")]]),
            )
        except Exception as e:
            await update.message.reply_text(f"{Icon.CROSS} {escape_html(str(e))}")
        return

    if ud.get(ST_AWAIT_SET_NUM) and is_admin(user.id):
        key = ud.pop(ST_AWAIT_SET_NUM)
        try:
            db.settings[key] = int(text); db.save(force=True)
            await update.message.reply_text(
                f"{Icon.CHECK} {escape_html(key)} = <b>{db.settings[key]}</b>", parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.SETTINGS} الإعدادات", "admin:settings")]]),
            )
        except Exception as e:
            await update.message.reply_text(f"{Icon.CROSS} {escape_html(str(e))}")
        return

    if ud.get(ST_AWAIT_SET_TEXT) and is_admin(user.id):
        key = ud.pop(ST_AWAIT_SET_TEXT)
        db.settings[key] = text; db.save(force=True)
        await update.message.reply_text(
            f"{Icon.CHECK} حُدّث {escape_html(key)}.", parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.SETTINGS} الإعدادات", "admin:settings")]]),
        )
        return

    if ud.get(ST_AWAIT_PREMIUM_DAYS) and is_admin(user.id):
        raw_target = ud.pop(ST_AWAIT_PREMIUM_UID, "")
        ud.pop(ST_AWAIT_PREMIUM_DAYS, None)
        try:
            days = int(text)
            if ":" in str(raw_target):
                _, tuid_s = str(raw_target).split(":", 1); tuid = int(tuid_s)
            else:
                tuid = int(raw_target) if raw_target else 0
            u = db.get_user(tuid)
            u.is_premium = True; u.premium_granted_by = user.id
            u.premium_until = ("9999-12-31T00:00:00" if days <= 0
                               else (datetime.now() + timedelta(days=days)).isoformat())
            db.update_user(u)
            db.log_activity("grant_premium", user.id, f"{tuid}: {days} days")
            await send_named_sticker(update, context, "premium_granted")
            await update.message.reply_text(
                f"{Icon.PREMIUM} منح البريميوم للمستخدم <code>{tuid}</code>\n"
                f"المدة: {'أبداً' if days <= 0 else f'{days} يوم'}\nحتى: {format_dt(u.premium_until)}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.USER} تفاصيله", f"admin:user:{tuid}")]]),
            )
            try:
                await context.bot.send_message(
                    tuid,
                    f"{Icon.PREMIUM} تهانينا! حصلت على عضوية بريميوم!\nالمدة: {'أبداً' if days <= 0 else f'{days} يوم'}",
                    parse_mode=ParseMode.HTML,
                )
            except: pass
        except Exception as e:
            await update.message.reply_text(f"{Icon.CROSS} {escape_html(str(e))}")
        return

    if ud.get(ST_AWAIT_PREMIUM_UID) and is_admin(user.id):
        raw_action = ud.pop(ST_AWAIT_PREMIUM_UID)
        try:
            tuid = int(text)
            if raw_action == "grant":
                ud[ST_AWAIT_PREMIUM_UID]  = f"grant:{tuid}"
                ud[ST_AWAIT_PREMIUM_DAYS] = True
                await update.message.reply_text(
                    f"{Icon.PREMIUM} كم يوم؟ (0 = أبداً):",
                    reply_markup=InlineKeyboardMarkup([[btn_danger(f"{Icon.CROSS} إلغاء", "admin:premium")]]))
            elif raw_action == "revoke":
                u = db.get_user(tuid)
                u.is_premium = False; u.premium_until = ""
                db.update_user(u)
                await update.message.reply_text(
                    f"{Icon.CHECK} سُحب البريميوم من <code>{tuid}</code>.", parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.PREMIUM} البريميوم", "admin:premium")]]),
                )
        except Exception as e:
            await update.message.reply_text(f"{Icon.CROSS} {escape_html(str(e))}")
        return

    if ud.get(ST_AWAIT_NOTE) and is_admin(user.id):
        tuid = int(ud.pop(ST_AWAIT_NOTE))
        u    = db.get_user(tuid)
        u.notes = text[:500]
        db.update_user(u)
        await update.message.reply_text(
            f"{Icon.CHECK} حُفظت الملاحظة.",
            reply_markup=InlineKeyboardMarkup([[btn_primary(f"{Icon.USER} تفاصيله", f"admin:user:{tuid}")]]),
        )
        return

    # الرد الافتراضي
    me = await context.bot.get_me()
    u  = db.get_user(user.id)
    await update.message.reply_text(
        text_welcome(u, me.username),
        reply_markup=kb_main_menu(u.user_id),
        parse_mode=ParseMode.HTML,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 🔭  ميزات المستخدم (دوال إضافية)
# ═══════════════════════════════════════════════════════════════════════════════

async def show_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = db.get_user(update.effective_user.id)
    premium_bonus = " (بريميوم — رفع مجاني)" if u.is_premium else ""
    text = (
        f"{Icon.DIAMOND} <b>نقاطك</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"رصيد النقاط: <b>{u.points}</b>\n"
        f"رفع مجاني متبقي: <b>{u.free_uploads}</b>{premium_bonus}\n"
        f"إجمالي ما ربحته: <b>{u.total_points_earned}</b>\n"
        f"النجوم المدفوعة: <b>{u.purchases_total_stars}</b>"
    )
    kb = InlineKeyboardMarkup([
        [btn_warning(f"{Icon.STAR} شراء نقاط",  "menu:buy"),
         btn_success(f"{Icon.GIFT} ادعُ أصدقاءك","menu:invite")],
        [btn_primary(f"{Icon.CODE} استرداد كود",  "menu:redeem")],
        [btn_secondary(f"{Icon.BACK} الرئيسية",  "menu:main")],
    ])
    await _edit_or_send(update, text, kb)


async def show_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u    = db.get_user(update.effective_user.id)
    me   = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref{u.user_id}"
    share_text = urllib.parse.quote(f"جرّب بوت الاستضافة الأقوى لملفات Python! {link}")
    text = (
        f"{Icon.GIFT} <b>ادعُ أصدقاءك واربح نقاطاً</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"بكل صديق جديد ينضم عبر رابطك تحصل على <b>{db.settings.get('points_per_invite', 2)}</b> نقطة.\n\n"
        f"{Icon.LINK} رابطك:\n<code>{link}</code>\n\n"
        f"دعوات ناجحة: <b>{len(u.invited_users)}</b>"
    )
    kb = InlineKeyboardMarkup([
        [btn_url_success(f"{Icon.LINK} مشاركة الرابط",
                         f"https://t.me/share/url?url={urllib.parse.quote(link)}&text={share_text}")],
        [btn_secondary(f"{Icon.BACK} الرئيسية", "menu:main")],
    ])
    await send_named_sticker(update, context, "share_link")
    await _edit_or_send(update, text, kb)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = db.get_user(update.effective_user.id)
    files_running = sum(1 for fid in u.files if pm.is_running(fid))
    text = (
        f"{Icon.STATS} <b>إحصائياتك</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"المعرّف: <code>{u.user_id}</code>\n"
        f"الانضمام: {format_dt(u.join_date)}\n"
        f"آخر نشاط: {humanize_delta(u.last_active)}\n"
        f"مرات الدخول: <b>{u.login_count}</b>\n"
        f"الرفع: <b>{u.total_uploads}</b>\n"
        f"التشغيل: <b>{u.total_runs}</b>\n"
        f"التحميلات: <b>{u.total_downloads}</b>\n"
        f"النقاط: <b>{u.points}</b>\n"
        f"الدعوات: <b>{len(u.invited_users)}</b>\n"
        f"الملفات: <b>{len(u.files)}</b> (يعمل: {files_running})\n"
        f"انتهاكات Rate: <b>{u.rate_violations}</b>"
    )
    await _edit_or_send(update, text,
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} الرئيسية", "menu:main")]]))


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u    = db.get_user(update.effective_user.id)
    prem = f" · بريميوم حتى {format_dt(u.premium_until)}" if u.is_premium else ""
    text = (
        f"{Icon.SETTINGS} <b>إعداداتك</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الإشعارات: <b>{'مفعّلة' if u.notifications_enabled else 'معطّلة'}</b>{prem}"
    )
    await _edit_or_send(update, text, kb_settings_user(u))


async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _edit_or_send(update, f"{Icon.SUPPORT} <b>الدعم الفني</b>", InlineKeyboardMarkup(support_rows()))


async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _edit_or_send(update, text_about(),
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} الرئيسية", "menu:main")]]))


async def show_security_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"{Icon.SHIELD} <b>حماية الاستضافة والـ API</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{Icon.API_PROTECT} يمنع سرقة توكن البوت ومفاتيح API\n"
        f"{Icon.TOKEN_SAFE} يكشف محاولات استخراج بيانات الاعتماد\n"
        f"{Icon.SHIELD} يفحص الكود قبل التشغيل\n"
        f"{Icon.AI} الذكاء الاصطناعي يحلل الكود تلقائياً\n"
        f"{Icon.CROWN} المشرفون محميون دائماً"
    )
    await _edit_or_send(update, text,
                        InlineKeyboardMarkup([[btn_secondary(f"{Icon.BACK} الرئيسية", "menu:main")]]))


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str = "points") -> None:
    if not db.settings.get("leaderboard_enabled", True):
        await _edit_or_send(update, f"{Icon.INFO} المتصدرون معطّلون.", kb_back("menu:main"))
        return
    text = text_leaderboard(category)
    kb   = InlineKeyboardMarkup([
        [btn_primary(f"{Icon.DIAMOND} النقاط",  "leaderboard:points"),
         btn_primary(f"{Icon.UPLOAD} الرفع",    "leaderboard:uploads"),
         btn_primary(f"{Icon.GIFT} الدعوات",    "leaderboard:invites")],
        [btn_secondary(f"{Icon.BACK} الرئيسية", "menu:main")],
    ])
    await send_named_sticker(update, context, "leaderboard")
    await _edit_or_send(update, text, kb)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹ تم الإيقاف بواسطة المستخدم.")
    except Exception as e:
        logger.exception("❌ خطأ قاتل: %s", e)
        sys.exit(1)
