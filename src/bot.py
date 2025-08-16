import asyncio
import logging
import datetime
import phonenumbers
from typing import Dict, Any, List, Optional

from aiohttp import web
from pytz import timezone

from telegram import (
    Update,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)


from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import asyncio
import logging


)

import gspread


from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, UI, LANGS, \
                   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, LEADS_EMAILS, \
                   get_gsheets_credentials_dict, GSHEET_NAME, COMPANY_PHONE, WHATSAPP_PHONE, WEBSITE_URL, ABOUT_US_PHOTO_URL

# ---------- ЛОГИ ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("sunera-bot")

# ---------- ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ ----------
USER: Dict[int, Dict[str, Any]] = {}

# ---------- GOOGLE SHEETS ----------


from google.oauth2.service_account import Credentials  # Добавьте этот импорт в начале файла

def get_sheet():
    creds_dict = get_gsheets_credentials_dict()
    if not creds_dict:
        return None
    try:
        scope = ["https://spreadsheets.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open(GSHEET_NAME)
        ws = sh.sheet1
        if not ws.row_values(1):
            ws.append_row(["Timestamp", "Username", "ChatID", "Type", "Data"])
        return ws
    except Exception as e:
        log.error(f"Sheets error: {e}")
        return None




SHEET = get_sheet()

def sheet_append(row: List[str]):
    try:
        if SHEET:
            SHEET.append_row(row)
    except Exception as e:
        log.error(f"Append to sheet failed: {e}")

# ---------- EMAIL ----------
def send_email(subject: str, body: str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and LEADS_EMAILS):
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(LEADS_EMAILS)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, LEADS_EMAILS, msg.as_string())
        log.info("Email sent")
    except Exception as e:
        log.error(f"Email error: {e}")

# ---------- УТИЛИТЫ UI ----------
def t(lang: str, key: str, **fmt):
    cfg = UI.get(lang, UI["Русский"])
    val = cfg.get(key, "")
    return val.format(**fmt) if fmt else val

def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    cfg = UI.get(lang, UI["Русский"])
    btns = [
        [KeyboardButton(cfg["about_us"]), KeyboardButton(cfg["services"])],
        [KeyboardButton(cfg["consult"]), KeyboardButton(cfg["website"])],
        [KeyboardButton(cfg["call_us"]), KeyboardButton(cfg["whatsapp"])]
    ]
    return ReplyKeyboardMarkup(btns, resize_keyboard=True)

def back_kb(lang: str) -> ReplyKeyboardMarkup:
    cfg = UI.get(lang, UI["Русский"])
    return ReplyKeyboardMarkup([[KeyboardButton(cfg["back"])]], resize_keyboard=True)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    USER[chat_id] = {"lang": None, "state": None}
    kb = ReplyKeyboardMarkup([[KeyboardButton(x)] for x in LANGS], resize_keyboard=True)
    await update.message.reply_text(UI["Русский"]["welcome"], reply_markup=kb)

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = USER.get(chat_id, {}).get("lang") or "Русский"
    await update.message.reply_text(t(lang, "your_id", cid=chat_id))

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_CHAT_ID and update.effective_chat.id == ADMIN_CHAT_ID:
        sheets = "✅ подключено" if SHEET else "—"
        users_count = len(USER)
        await update.message.reply_text(t("Русский", "admin_status", sheets=sheets, users_cnt=users_count))
    else:
        await update.message.reply_text("No access.")

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    if text in LANGS:
        USER[chat_id] = {"lang": text, "state": None}
        await update.message.reply_text(t(text, "menu"), reply_markup=main_menu_kb(text))
        return

    if chat_id not in USER or USER[chat_id].get("lang") is None:
        kb = ReplyKeyboardMarkup([[KeyboardButton(x)] for x in LANGS], resize_keyboard=True)
        await update.message.reply_text(UI["Русский"]["welcome"], reply_markup=kb)
        return

    lang = USER[chat_id]["lang"]
    state = USER[chat_id].get("state")
    cfg = UI[lang]

    if text == cfg["back"]:
        USER[chat_id]["state"] = None
        await update.message.reply_text(t(lang, "menu"), reply_markup=main_menu_kb(lang))
        return

    if text == cfg["about_us"]:
        if cfg.get("about_us_photo"):
            await update.message.reply_photo(
                photo=cfg["about_us_photo"],
                caption=cfg["about_us_text"],
                reply_markup=main_menu_kb(lang)
            )
        else:
            await update.message.reply_text(cfg["about_us_text"], reply_markup=main_menu_kb(lang))
        return

    if text == cfg["services"]:
        await update.message.reply_text(cfg["services_info"], reply_markup=main_menu_kb(lang))
        return

    if text == cfg["consult"]:
        USER[chat_id]["state"] = "consult"
        await update.message.reply_text(cfg["consult_prompt"], reply_markup=back_kb(lang))
        return

    if text == cfg["website"]:
        await update.message.reply_text(t(lang, "website_text", url=WEBSITE_URL), reply_markup=main_menu_kb(lang))
        return

    if text == cfg["call_us"]:
        await update.message.reply_text(t(lang, "call_us_text", phone=COMPANY_PHONE), reply_markup=main_menu_kb(lang))
        return

    if text == cfg["whatsapp"]:
        await update.message.reply_text(t(lang, "whatsapp_text", phone=WHATSAPP_PHONE), reply_markup=main_menu_kb(lang))
        return

    if state == "consult":
        phone = ""
        for token in text.split():
            try:
                pn = phonenumbers.parse(token, None)
                if phonenumbers.is_valid_number(pn):
                    phone = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                    break
            except Exception:
                continue

        lead_text = f"Новая заявка: {text}\nТелефон: {phone or 'не распознан'}\nОт: @{update.effective_user.username or ''} ({chat_id})"
        await update.message.reply_text(UI[lang]["consult_ok"], reply_markup=main_menu_kb(lang))
        USER[chat_id]["state"] = None

        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(ADMIN_CHAT_ID, f"📝 {lead_text}")
            except Exception:
                pass

        uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
        ts = datetime.datetime.utcnow().isoformat()
        sheet_append([ts, uname, str(chat_id), "Consult", text])
        send_email("Sunera: новая заявка", lead_text)
        return

    await update.message.reply_text(cfg["unknown"], reply_markup=main_menu_kb(lang))

# ---------- ЗАПУСК: Telegram + HTTP-сервер (для Render) ----------
async def run_http_server():
    async def handle_health(request):
        return web.Response(text="OK")
    app = web.Application()
    app.add_routes([web.get("/", handle_health), web.get("/health", handle_health)])
    port = int(web.os.environ.get("PORT", "10000"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"HTTP server started on 0.0.0.0:{port}")

async def main():
    if not TELEGRAM_BOT_TOKEN:
        log.error("No TELEGRAM_BOT_TOKEN in env!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    await app.initialize()
    await app.start()
    log.info("Telegram bot started")

    await run_http_server()

    try:
        await asyncio.Event().wait()
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":  # Исправлено на правильное имя проверки
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Stopped.")
        
