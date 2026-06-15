"""Alaboodi TV — Telegram Mini App bot with full admin dashboard."""
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    MenuButtonWebApp,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────────────────
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
DEV_URL = os.getenv("DEV_URL", "").strip()
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
}

if not BOT_TOKEN:
    sys.exit("BOT_TOKEN missing.")
if not WEBAPP_URL or not WEBAPP_URL.startswith("https://"):
    sys.exit("WEBAPP_URL missing or not HTTPS.")

# ──────────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent
USERS_FILE = DATA_DIR / "users.json"
CHANNELS_FILE = DATA_DIR / "forced_channels.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

# The 4 sources the gateway portal (showcase.html) exposes, each reverse-proxied
# under /s/<id>/ at the same time. Display-only: the portal routes the user. The bot
# does NOT switch a single "active" source — doing so via yala-switch would overwrite
# the live multi-source nginx config. See server/nginx/yala.zaboni.store.conf.
SOURCES = [
    {"id": "koora4live", "label": "المصدر الأول — Koora4Live", "host": "gonutradeal.com",  "path": "/s/koora4live/"},
    {"id": "kooracity",  "label": "المصدر الثاني — Koora City", "host": "koooracity.io",    "path": "/s/kooracity/"},
    {"id": "livescore",  "label": "المصدر الثالث — Live Score", "host": "www.freekora.com", "path": "/s/livescore/"},
    {"id": "syrlive",    "label": "المصدر الرابع — Syria Live", "host": "d.syrlive.com",    "path": "/s/syrlive/"},
]

BOT_START_TS = time.time()
ADMIN_BROADCAST_PENDING: dict[int, bool] = {}   # admin id → awaiting broadcast text
ADMIN_CHANNEL_ADD_PENDING: dict[int, bool] = {}  # admin id → awaiting channel id

# ──────────────────────────────────────────────────────────────────────────
# Persistence helpers
# ──────────────────────────────────────────────────────────────────────────
def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_users() -> dict[str, dict]:
    """Load users dict {id_str: {first_seen, last_seen, name, username}}.
    Migrates legacy list-of-ints format on first load."""
    data = _load_json(USERS_FILE, {})
    if isinstance(data, list):
        # legacy: list of ints → migrate
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        data = {str(uid): {"first_seen": now, "last_seen": now, "name": "", "username": ""} for uid in data}
        _save_json(USERS_FILE, data)
    return data


def save_users(users: dict[str, dict]) -> None:
    _save_json(USERS_FILE, users)


def load_channels() -> list[dict]:
    return _load_json(CHANNELS_FILE, [])


def save_channels(channels: list[dict]) -> None:
    _save_json(CHANNELS_FILE, channels)


def load_settings() -> dict:
    return _load_json(SETTINGS_FILE, {
        "welcome_emoji": "⚽️",
        "button_label": "مشاهدة المباريات المباشرة ⚽️",
        "force_join_enabled": False,
    })


def save_settings(s: dict) -> None:
    _save_json(SETTINGS_FILE, s)


def source_label(sid: str) -> str:
    return next((s["label"] for s in SOURCES if s["id"] == sid), sid)


# ──────────────────────────────────────────────────────────────────────────
# Activity tracking
# ──────────────────────────────────────────────────────────────────────────
USERS: dict[str, dict] = load_users()


def touch_user(user_id: int, name: str = "", username: str = "") -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    key = str(user_id)
    rec = USERS.get(key)
    if rec is None:
        USERS[key] = {"first_seen": now, "last_seen": now, "name": name, "username": username}
    else:
        rec["last_seen"] = now
        if name:
            rec["name"] = name
        if username:
            rec["username"] = username
    save_users(USERS)


def count_active_today() -> int:
    today = datetime.now(timezone.utc).date()
    n = 0
    for r in USERS.values():
        try:
            ts = datetime.fromisoformat(r.get("last_seen", "").replace("Z", "+00:00"))
            if ts.date() == today:
                n += 1
        except Exception:
            pass
    return n


def fmt_uptime(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, _ = divmod(rem, 60)
    if h >= 24:
        d, h = divmod(h, 24)
        return f"{d}ي {h}س"
    return f"{h}س {m}د"


# ──────────────────────────────────────────────────────────────────────────
# UI builders
# ──────────────────────────────────────────────────────────────────────────
def build_welcome() -> str:
    return (
        "⚽️ مرحباً بك في بوت نقل المباريات\n\n"
        "📺 يمكنك مشاهدة:\n"
        "• المباريات العالمية\n"
        "• المباريات العربية\n"
        "• البث المباشر\n\n"
        "🔴 اضغط الزر بالاسفل لمشاهدة المباريات"
    )


def webapp_url_with_source() -> str:
    """Cache-busted WebApp URL. iOS Telegram caches WebApp pages by full URL, so a
    changing `_v` param forces a fresh fetch each time the button is rebuilt."""
    return f"{WEBAPP_URL}?_v={int(time.time())}"


def build_user_keyboard() -> InlineKeyboardMarkup:
    settings = load_settings()
    rows = [
        [InlineKeyboardButton(
            text=settings.get("button_label", "مشاهدة المباريات المباشرة ⚽️"),
            web_app=WebAppInfo(url=webapp_url_with_source()),
        )]
    ]
    if DEV_URL:
        rows.append([InlineKeyboardButton(text="Dev", url=DEV_URL)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Persistent reply keyboards (always shown at bottom of chat)
ADMIN_PANEL_LABEL = "🎛 لوحة التحكم"


def build_user_persistent_keyboard() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard with one WebApp button — always visible at bottom of chat.
    URL includes ?src=<active> so a source switch invalidates iOS Telegram's WebApp cache."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            text="📺 فتح التطبيق",
            web_app=WebAppInfo(url=webapp_url_with_source()),
        )]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="اضغط الزر بالأسفل لفتح التطبيق",
    )


def build_admin_persistent_keyboard() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard for admins — single shortcut to the inline dashboard
    (which itself contains the WebApp launch button alongside the admin tools)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=ADMIN_PANEL_LABEL)]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="اضغط 🎛 لوحة التحكم لفتح كل الأدوات",
    )


def keyboard_for(user_id: int | None) -> ReplyKeyboardMarkup:
    return build_admin_persistent_keyboard() if is_admin(user_id) else build_user_persistent_keyboard()


def build_admin_home() -> tuple[str, InlineKeyboardMarkup]:
    total = len(USERS)
    today = count_active_today()
    uptime = fmt_uptime(time.time() - BOT_START_TS)

    text = (
        "👑 <b>لوحة تحكم الأدمن - Alaboodi TV</b>\n\n"
        "📊 <b>الإحصائيات:</b>\n"
        f"├ 👥 المستخدمين: <b>{total}</b>\n"
        f"├ 🟢 نشطين اليوم: <b>{today}</b>\n"
        f"├ 📺 المصادر: <b>{len(SOURCES)}</b> (بوابة Trab TV)\n"
        f"└ 🕒 وقت التشغيل: <b>{uptime}</b>\n\n"
        "⚡ اختر من القائمة أدناه:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📺 فتح التطبيق ⚽️",
                web_app=WebAppInfo(url=webapp_url_with_source()),
            ),
        ],
        [
            InlineKeyboardButton(text="👥 المستخدمين",            callback_data="adm:users:0"),
            InlineKeyboardButton(text="📊 الإحصائيات الكاملة",   callback_data="adm:stats"),
        ],
        [
            InlineKeyboardButton(text="📡 حالة المصادر",           callback_data="adm:source"),
            InlineKeyboardButton(text="📢 القنوات الإجبارية",      callback_data="adm:channels"),
        ],
        [
            InlineKeyboardButton(text="⚙️ إعدادات البوت",          callback_data="adm:settings"),
            InlineKeyboardButton(text="📤 إرسال جماعي",            callback_data="adm:broadcast"),
        ],
        [
            InlineKeyboardButton(text="🔄 تحديث",                  callback_data="adm:home"),
        ],
    ])
    return text, kb


def build_source_panel() -> tuple[str, InlineKeyboardMarkup]:
    """Read-only view of the gateway sources. The portal (showcase.html) routes users
    between them; the bot intentionally does NOT switch sources (that would overwrite
    the live multi-source nginx config)."""
    lines = [
        "📡 <b>حالة المصادر</b>\n",
        "كل المصادر تُعرض سوا في بوابة <b>Trab TV</b> والمستخدم يختار منها:\n",
    ]
    for i, src in enumerate(SOURCES, 1):
        lines.append(
            f"<b>{i}.</b> {src['label']}\n"
            f"   <code>{src['host']}</code> · <code>{src['path']}</code>"
        )
    lines.append(f"\n🔗 البوابة: <code>{WEBAPP_URL}</code>")
    rows = [
        [InlineKeyboardButton(text="📺 فتح البوابة", web_app=WebAppInfo(url=webapp_url_with_source()))],
        [InlineKeyboardButton(text="« رجوع", callback_data="adm:home")],
    ]
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


def build_users_panel(page: int = 0, per_page: int = 10) -> tuple[str, InlineKeyboardMarkup]:
    items = sorted(
        USERS.items(),
        key=lambda kv: kv[1].get("last_seen", ""),
        reverse=True,
    )
    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(0, min(page, pages - 1))
    start = page * per_page
    chunk = items[start:start + per_page]

    lines = [f"👥 <b>المستخدمون</b> ({total} إجمالي)\n"]
    for i, (uid, rec) in enumerate(chunk, start=1 + start):
        name = rec.get("name") or "—"
        un = rec.get("username") or ""
        un_str = f" @{un}" if un else ""
        last = (rec.get("last_seen") or "")[:16].replace("T", " ")
        lines.append(f"<b>{i}.</b> {name}{un_str}\n   <code>{uid}</code> · آخر نشاط: {last}")

    text = "\n".join(lines) if chunk else "👥 لا يوجد مستخدمون بعد."

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="« السابق", callback_data=f"adm:users:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="adm:noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="التالي »", callback_data=f"adm:users:{page+1}"))
    rows = [nav, [InlineKeyboardButton(text="« رجوع", callback_data="adm:home")]]
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def build_stats_panel() -> tuple[str, InlineKeyboardMarkup]:
    total = len(USERS)
    today = count_active_today()
    # Last 7 days breakdown
    today_dt = datetime.now(timezone.utc).date()
    counts = {}
    for r in USERS.values():
        try:
            ts = datetime.fromisoformat((r.get("last_seen") or "").replace("Z", "+00:00")).date()
            counts[ts] = counts.get(ts, 0) + 1
        except Exception:
            pass

    lines = [
        "📊 <b>الإحصائيات الكاملة</b>\n",
        f"👥 إجمالي المستخدمين: <b>{total}</b>",
        f"🟢 نشطين اليوم: <b>{today}</b>",
        f"📅 نشاط آخر 7 أيام:",
    ]
    for i in range(7):
        d = today_dt - timedelta(days=i)
        n = counts.get(d, 0)
        bar = "█" * min(n, 20) + "░" * max(0, 20 - n)
        marker = "اليوم" if i == 0 else d.isoformat()
        lines.append(f"<code>{marker:11}</code> {bar} {n}")

    lines.append(f"\n📺 المصادر المتاحة: <b>{len(SOURCES)}</b> (بوابة Trab TV)")
    lines.append(f"🕒 وقت تشغيل البوت: <b>{fmt_uptime(time.time() - BOT_START_TS)}</b>")

    rows = [[InlineKeyboardButton(text="« رجوع", callback_data="adm:home")]]
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


def build_channels_panel() -> tuple[str, InlineKeyboardMarkup]:
    chans = load_channels()
    settings = load_settings()
    enabled = settings.get("force_join_enabled", False)
    state = "🟢 مُفعَّل" if enabled else "⚪ مُعطَّل"

    lines = [
        "📢 <b>القنوات الإجبارية</b>\n",
        f"الحالة: {state}",
        f"عدد القنوات: <b>{len(chans)}</b>\n",
    ]
    if chans:
        for i, ch in enumerate(chans, 1):
            lines.append(f"<b>{i}.</b> {ch.get('title', '?')} — <code>{ch.get('chat_id','?')}</code>")
    else:
        lines.append("<i>لم تُضف قنوات بعد.</i>")

    rows = [
        [InlineKeyboardButton(text="➕ إضافة قناة", callback_data="adm:ch_add")],
    ]
    if chans:
        for ch in chans:
            cid = ch.get("chat_id", "")
            rows.append([
                InlineKeyboardButton(
                    text=f"🗑 حذف: {ch.get('title','?')}",
                    callback_data=f"adm:ch_rm:{cid}",
                )
            ])
    rows.append([
        InlineKeyboardButton(
            text=("⏸ إيقاف الإجبار" if enabled else "▶️ تفعيل الإجبار"),
            callback_data="adm:ch_toggle",
        ),
        InlineKeyboardButton(text="« رجوع", callback_data="adm:home"),
    ])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


def build_settings_panel() -> tuple[str, InlineKeyboardMarkup]:
    settings = load_settings()
    text = (
        "⚙️ <b>إعدادات البوت</b>\n\n"
        f"🔗 رابط التطبيق:\n<code>{WEBAPP_URL}</code>\n\n"
        f"🔘 نص زر التشغيل:\n<i>{settings.get('button_label','—')}</i>\n\n"
        f"🆔 معرّفات الأدمن:\n<code>{', '.join(map(str, sorted(ADMIN_IDS))) or '—'}</code>\n\n"
        f"📂 ملف المصادر النشط:\n<code>/var/lib/yala-source</code>\n"
    )
    rows = [
        [InlineKeyboardButton(text="« رجوع", callback_data="adm:home")],
    ]
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def build_broadcast_panel() -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "📤 <b>إرسال جماعي</b>\n\n"
        f"عدد المستلمين: <b>{len(USERS)}</b>\n\n"
        "أرسل الآن الرسالة (نص أو صورة مع تعليق) "
        "وسأعرضها عليك للتأكيد قبل البث."
    )
    rows = [
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="adm:home")],
    ]
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


# ──────────────────────────────────────────────────────────────────────────
# Bot wiring
# ──────────────────────────────────────────────────────────────────────────
dp = Dispatcher()


def is_admin(uid: int | None) -> bool:
    return bool(uid and uid in ADMIN_IDS)


# ──────────────────────────────────────────────────────────────────────────
# Forced-channel join gate
# ──────────────────────────────────────────────────────────────────────────
def _channel_url(ch: dict) -> str | None:
    un = (ch.get("username") or "").lstrip("@")
    if un:
        return f"https://t.me/{un}"
    return ch.get("invite_link") or None


async def unjoined_channels(bot: Bot, user_id: int) -> list[dict]:
    """Return the forced channels the user has NOT joined. Empty list = all good
    (or enforcement disabled / no channels). A channel the bot itself can't query
    (not an admin there) is skipped — logged, never used to hard-lock users out."""
    settings = load_settings()
    if not settings.get("force_join_enabled", False):
        return []
    missing: list[dict] = []
    for ch in load_channels():
        cid = ch.get("chat_id")
        if cid is None:
            continue
        try:
            member = await bot.get_chat_member(cid, user_id)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except TelegramForbiddenError:
            logging.warning("force-join: bot lacks access to %s; skipping", cid)
        except TelegramBadRequest as e:
            logging.warning("force-join check failed for %s: %s", cid, e)
            missing.append(ch)
        except Exception as e:
            logging.warning("force-join unexpected error for %s: %s", cid, e)
    return missing


def build_join_gate(channels: list[dict]) -> tuple[str, InlineKeyboardMarkup]:
    rows: list[list[InlineKeyboardButton]] = []
    for ch in channels:
        title = ch.get("title", "القناة")
        url = _channel_url(ch)
        if url:
            rows.append([InlineKeyboardButton(text=f"📢 {title}", url=url)])
        else:
            rows.append([InlineKeyboardButton(text=f"📢 {title} (انضم يدوياً)", callback_data="join:noop")])
    rows.append([InlineKeyboardButton(text="✅ اشتركت — تحقّق", callback_data="join:check")])
    text = (
        "🔒 <b>للمتابعة، اشترك أولاً</b>\n\n"
        "لازم تشترك بالقنوات التالية حتى تقدر تفتح التطبيق.\n"
        "بعد الاشتراك اضغط <b>✅ اشتركت — تحقّق</b>."
    )
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.callback_query(F.data.startswith("join:"))
async def on_join_check(query: CallbackQuery, bot: Bot) -> None:
    action = (query.data or "").split(":", 1)[1] if ":" in (query.data or "") else ""
    if action == "noop":
        await query.answer("افتح القناة، اشترك، ثم ارجع واضغط تحقّق", show_alert=True)
        return
    uid = query.from_user.id
    missing = await unjoined_channels(bot, uid)
    if missing:
        await query.answer("لسّا ما اشتركت بكل القنوات ❌", show_alert=True)
        text, kb = build_join_gate(missing)
        await _safe_edit(query, text, kb)
        return
    await query.answer("تم التحقق ✓")
    if query.message:
        try:
            await query.message.edit_text("✅ تم التحقق! أهلاً بك.")
        except Exception:
            pass
        await query.message.answer(build_welcome(), reply_markup=build_user_keyboard())
        await query.message.answer(
            "📌 زر <b>📺 فتح التطبيق</b> ثابت بالأسفل — اضغطه أي وقت.",
            reply_markup=keyboard_for(uid),
        )


@dp.message(CommandStart())
async def on_start(message: Message, bot: Bot) -> None:
    uid = None
    if message.from_user:
        uid = message.from_user.id
        touch_user(
            uid,
            name=message.from_user.full_name or "",
            username=message.from_user.username or "",
        )
    # Forced-channel gate — admins bypass. If enabled and user hasn't joined all
    # required channels, show the join gate instead of the WebApp button.
    if not is_admin(uid) and uid:
        missing = await unjoined_channels(bot, uid)
        if missing:
            text, kb = build_join_gate(missing)
            await message.answer(text, reply_markup=kb)
            return
    # Send welcome with inline WebApp button
    await message.answer(build_welcome(), reply_markup=build_user_keyboard())
    # Then pin a persistent reply keyboard at the bottom of chat (always visible)
    await message.answer(
        "📌 زر <b>📺 فتح التطبيق</b> ثابت بالأسفل — اضغطه أي وقت.",
        reply_markup=keyboard_for(uid),
    )


@dp.message(F.text == ADMIN_PANEL_LABEL)
async def on_admin_panel_button(message: Message) -> None:
    """Admin pressed the persistent '🎛 لوحة التحكم' reply-keyboard button."""
    if not is_admin(message.from_user.id if message.from_user else None):
        return
    text, kb = build_admin_home()
    await message.answer(text, reply_markup=kb)


@dp.message(Command("whoami"))
async def on_whoami(message: Message) -> None:
    if not message.from_user:
        return
    touch_user(message.from_user.id, message.from_user.full_name or "", message.from_user.username or "")
    await message.answer(
        f"🆔 معرّفك في تليجرام:\n<code>{message.from_user.id}</code>\n\n"
        "أضفه إلى <code>ADMIN_IDS</code> في ملف .env لتفعيل لوحة التحكم."
    )


@dp.message(Command("admin"))
@dp.message(Command("source"))   # legacy alias
async def on_admin(message: Message) -> None:
    uid = message.from_user.id if message.from_user else None
    if not is_admin(uid):
        return
    # First: re-attach the admin reply keyboard at the bottom (covers fresh sessions
    # and refreshes any stale single-button keyboard from previous bot versions)
    await message.answer(
        "🎛 <b>قائمة الأدمن</b> ثابتة بالأسفل.",
        reply_markup=keyboard_for(uid),
    )
    # Then: send the dashboard with its inline keyboard
    text, kb = build_admin_home()
    await message.answer(text, reply_markup=kb)


# ──────────────────────────────────────────────────────────────────────────
# Admin callback router
# ──────────────────────────────────────────────────────────────────────────
async def _safe_edit(query: CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    if not query.message:
        return
    try:
        await query.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        # message identical or edit window expired — try sending fresh
        try:
            await query.message.answer(text, reply_markup=kb)
        except Exception:
            pass


@dp.callback_query(F.data.startswith("adm:"))
async def on_admin_cb(query: CallbackQuery) -> None:
    if not is_admin(query.from_user.id if query.from_user else None):
        await query.answer("غير مصرّح لك", show_alert=True)
        return

    parts = (query.data or "").split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "noop":
        await query.answer()
        return

    if action == "home":
        await query.answer()
        text, kb = build_admin_home()
        await _safe_edit(query, text, kb)
        return

    if action == "users":
        page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        await query.answer()
        text, kb = build_users_panel(page)
        await _safe_edit(query, text, kb)
        return

    if action == "stats":
        await query.answer()
        text, kb = build_stats_panel()
        await _safe_edit(query, text, kb)
        return

    if action == "source":
        await query.answer()
        text, kb = build_source_panel()
        await _safe_edit(query, text, kb)
        return

    if action == "channels":
        await query.answer()
        text, kb = build_channels_panel()
        await _safe_edit(query, text, kb)
        return

    if action == "ch_add":
        ADMIN_CHANNEL_ADD_PENDING[query.from_user.id] = True
        await query.answer()
        await _safe_edit(
            query,
            "➕ <b>إضافة قناة إجبارية</b>\n\n"
            "أرسل الآن معرّف القناة (مثل <code>@my_channel</code>) "
            "أو الرقم (<code>-100...</code>).\n\n"
            "تأكّد إن البوت <b>أدمن</b> في القناة.",
            InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="❌ إلغاء", callback_data="adm:channels"),
            ]]),
        )
        return

    if action == "ch_rm":
        cid = parts[2] if len(parts) > 2 else ""
        chans = [c for c in load_channels() if str(c.get("chat_id")) != str(cid)]
        save_channels(chans)
        await query.answer("تم الحذف ✓")
        text, kb = build_channels_panel()
        await _safe_edit(query, text, kb)
        return

    if action == "ch_toggle":
        s = load_settings()
        s["force_join_enabled"] = not s.get("force_join_enabled", False)
        save_settings(s)
        await query.answer("تم التبديل ✓")
        text, kb = build_channels_panel()
        await _safe_edit(query, text, kb)
        return

    if action == "settings":
        await query.answer()
        text, kb = build_settings_panel()
        await _safe_edit(query, text, kb)
        return

    if action == "broadcast":
        ADMIN_BROADCAST_PENDING[query.from_user.id] = True
        await query.answer()
        text, kb = build_broadcast_panel()
        await _safe_edit(query, text, kb)
        return

    if action == "bcast_send":
        # confirmed broadcast — text was passed as raw message earlier
        await query.answer("جارٍ البث...")
        return

    await query.answer()


# ──────────────────────────────────────────────────────────────────────────
# Pending input handlers (broadcast text + channel add)
# ──────────────────────────────────────────────────────────────────────────
@dp.message(F.from_user.id.in_(ADMIN_IDS) if ADMIN_IDS else F.from_user.id == 0)
async def on_admin_input(message: Message, bot: Bot) -> None:
    """Catches free-form admin input when a pending state is active."""
    uid = message.from_user.id if message.from_user else 0

    # touch the admin like any user
    if message.from_user:
        touch_user(uid, message.from_user.full_name or "", message.from_user.username or "")

    if ADMIN_CHANNEL_ADD_PENDING.get(uid):
        del ADMIN_CHANNEL_ADD_PENDING[uid]
        raw = (message.text or "").strip()
        if not raw:
            await message.answer("⚠️ معرّف فارغ — تم الإلغاء.")
            return
        # Validate by querying chat
        try:
            chat = await bot.get_chat(raw)
            chans = load_channels()
            entry = {
                "chat_id": chat.id,
                "title": chat.title or chat.username or str(chat.id),
                "username": chat.username or "",
                "invite_link": getattr(chat, "invite_link", "") or "",
            }
            if not any(str(c.get("chat_id")) == str(chat.id) for c in chans):
                chans.append(entry)
                save_channels(chans)
                await message.answer(f"✅ تمت إضافة <b>{entry['title']}</b>")
            else:
                await message.answer("ℹ️ القناة موجودة بالفعل.")
        except Exception as e:
            await message.answer(f"❌ تعذّر إضافة القناة: {e}")
        text, kb = build_channels_panel()
        await message.answer(text, reply_markup=kb)
        return

    if ADMIN_BROADCAST_PENDING.get(uid):
        del ADMIN_BROADCAST_PENDING[uid]
        # Ask for confirmation showing the message back
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ بث الآن", callback_data=f"adm:bcast_go:{message.message_id}"),
            InlineKeyboardButton(text="❌ إلغاء",   callback_data="adm:home"),
        ]])
        await message.answer(
            f"🔎 <b>معاينة الرسالة</b>\nسيتم إرسالها إلى <b>{len(USERS)}</b> مستخدم.\n"
            f"اضغط (بث الآن) للتأكيد.",
            reply_markup=kb,
        )
        return

    # Otherwise: ignore admin's free-form text (they should use /admin)
    return


@dp.callback_query(F.data.startswith("adm:bcast_go:"))
async def on_broadcast_go(query: CallbackQuery, bot: Bot) -> None:
    if not is_admin(query.from_user.id if query.from_user else None):
        await query.answer("غير مصرّح", show_alert=True)
        return
    parts = (query.data or "").split(":")
    if len(parts) < 3 or not parts[2].isdigit():
        await query.answer("معرّف رسالة غير صالح", show_alert=True)
        return
    src_message_id = int(parts[2])
    await query.answer("بدأ البث…")
    sent, failed = 0, 0
    for uid in list(USERS.keys()):
        try:
            await bot.copy_message(
                chat_id=int(uid),
                from_chat_id=query.from_user.id,
                message_id=src_message_id,
            )
            sent += 1
        except (TelegramBadRequest, TelegramForbiddenError):
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # gentle rate limit
    if query.message:
        await query.message.answer(
            f"📊 <b>نتائج البث</b>\nتم: <b>{sent}</b> · فشل: <b>{failed}</b>"
        )
    text, kb = build_admin_home()
    await _safe_edit(query, text, kb)


# ──────────────────────────────────────────────────────────────────────────
async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Persistent menu button next to the message input — opens WebApp for everyone.
    # URL includes ?src=<active> so iOS Telegram's WebApp cache resets after a source switch.
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📺 فتح التطبيق",
                web_app=WebAppInfo(url=webapp_url_with_source()),
            )
        )
    except Exception as e:
        logging.warning("set_chat_menu_button failed: %s", e)

    # Suggested commands list (shown when user types '/')
    try:
        await bot.set_my_commands([
            BotCommand(command="start",   description="🚀 بدء التشغيل"),
            BotCommand(command="admin",   description="🎛 لوحة التحكم (للأدمن فقط)"),
            BotCommand(command="whoami",  description="🆔 عرض معرّفك في تليجرام"),
        ])
    except Exception as e:
        logging.warning("set_my_commands failed: %s", e)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
