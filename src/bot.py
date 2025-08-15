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
from telegram.ext import (
    Application, ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, CallbackQueryHandler,
    filters
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, UI, LANGS, \
                   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, LEADS_EMAILS, \
                   get_gsheets_credentials_dict, GSHEET_NAME

# ---------- ЛОГИ ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("sunera-bot")

# ---------- ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ ----------
# Храним язык и состояние. Это в памяти (RAM). Для продакшна можно вынести в БД.
USER: Dict[int, Dict[str, Any]] = {}

# ---------- GOOGLE SHEETS ----------
def get_sheet():
    creds_dict = get_gsheets_credentials_dict()
    if not creds_dict:
        return None
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sh = client.open(GSHEET_NAME)
        ws = sh.sheet1
        # Заголовки при первом запуске
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
        return  # email не настроен — пропускаем тихо
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
        [KeyboardButton(cfg["services"]), KeyboardButton(cfg["calc"])],
        [KeyboardButton(cfg["consult"]), KeyboardButton(cfg["faq"])]
    ]
    return ReplyKeyboardMarkup(btns, resize_keyboard=True)

def back_kb(lang: str) -> ReplyKeyboardMarkup:
    cfg = UI.get(lang, UI["Русский"])
    return ReplyKeyboardMarkup([[KeyboardButton(cfg["back"])]], resize_keyboard=True)

def services_inline(lang: str) -> InlineKeyboardMarkup:
    cfg = UI.get(lang, UI["Русский"])
    rows = [[InlineKeyboardButton(text=txt, callback_data=f"svc_{i}")]
            for i, txt in enumerate(cfg["services_list"], start=1)]
    return InlineKeyboardMarkup(rows)

def faq_inline(lang: str) -> InlineKeyboardMarkup:
    cfg = UI.get(lang, UI["Русский"])
    rows = [[InlineKeyboardButton(text=q, callback_data=f"faq_{i}")]
            for i, (q, _a) in enumerate(cfg["faq_items"], start=1)]
    return InlineKeyboardMarkup(rows)

# ---------- ОБРАБОТЧИКИ ----------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Сброс состояния и язык по умолчанию не выбран
    USER[chat_id] = {"lang": None, "state": None}
    # Показ выбора языка
    kb = ReplyKeyboardMarkup([[KeyboardButton(x)] for x in LANGS], resize_keyboard=True)
    await update.message.reply_text(UI["Русский"]["welcome"], reply_markup=kb)

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = USER.get(chat_id, {}).get("lang") or "Русский"
    await update.message.reply_text(t(lang, "your_id", cid=chat_id))

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_CHAT_ID and update.effective_chat.id == ADMIN_CHAT_ID:
        sheets = "✅ подключено" if SHEET else "—"
        users_cnt = len(USER)
        await update.message.reply_text(t("Русский", "admin_status", sheets=sheets, users_cnt=users_cnt))
    else:
        await update.message.reply_text("No access.")

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    # 1) Выбор языка?
    if text in LANGS:
        USER[chat_id] = {"lang": text, "state": None}
        await update.message.reply_text(
            t(text, "menu"),
            reply_markup=main_menu_kb(text)
        )
        return

    # 2) Если язык ещё не выбран — просим выбрать
    if chat_id not in USER or USER[chat_id].get("lang") is None:
        kb = ReplyKeyboardMarkup([[KeyboardButton(x)] for x in LANGS], resize_keyboard=True)
        await update.message.reply_text(UI["Русский"]["welcome"], reply_markup=kb)
        return

    lang = USER[chat_id]["lang"]
    state = USER[chat_id].get("state")

    cfg = UI[lang]
    # 3) Кнопки главного меню
    if text == cfg["back"]:
        USER[chat_id]["state"] = None
        await update.message.reply_text(t(lang, "menu"), reply_markup=main_menu_kb(lang))
        return

    if text == cfg["services"]:
        await update.message.reply_text(cfg["services_info"], reply_markup=main_menu_kb(lang))
        await update.message.reply_markup  # просто сохраняем клавиатуру
        await update.message.reply_text("—", reply_markup=None)
        await update.message.reply_text(cfg["services_info"], reply_markup=None)
        await update.message.reply_text(cfg["services_info"], reply_markup=None)
        # показываем inline-кнопки
        await update.message.reply_text(cfg["services_info"], reply_markup=services_inline(lang))
        return

    if text == cfg["faq"]:
        await update.message.reply_text(cfg["faq_title"], reply_markup=faq_inline(lang))
        return

    if text == cfg["calc"]:
        USER[chat_id]["state"] = "calc"
        await update.message.reply_text(cfg["calc_prompt"], reply_markup=back_kb(lang))
        return

    if text == cfg["consult"]:
        USER[chat_id]["state"] = "consult"
        await update.message.reply_text(cfg["consult_prompt"], reply_markup=back_kb(lang))
        return

    # 4) Состояния
    if state == "calc":
        try:
            cons = float(text.replace(",", "."))
            # Модель: kW = (kWh/month)/30 / (PSH 4.5) / PR(0.8)
            kw = round(cons / 30.0 / 4.5 / 0.8, 2)
            await update.message.reply_text(
                t(lang, "calc_result", kw=kw, cons=cons),
                reply_markup=main_menu_kb(lang)
            )
            USER[chat_id]["state"] = None
            # Логи в админ/таблицу
            uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
            ts = datetime.datetime.utcnow().isoformat()
            sheet_append([ts, uname, str(chat_id), "Power_Calc", f"{cons} kWh/mo -> {kw} kW"])
            if ADMIN_CHAT_ID:
                try:
                    await context.bot.send_message(
                        ADMIN_CHAT_ID,
                        f"🔢 Расчёт мощности от {uname or chat_id}: {cons} кВт·ч/мес → {kw} кВт"
                    )
                except Exception:
                    pass
        except ValueError:
            await update.message.reply_text(cfg["calc_error"], reply_markup=back_kb(lang))
        return

    if state == "consult":
        # Пытаемся вытащить телефон
        phone = ""
        try:
            for token in text.split():
                try:
                    pn = phonenumbers.parse(token, None)
                    if phonenumbers.is_valid_number(pn):
                        phone = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        lead_text = f"Новая заявка: {text}\nТелефон: {phone or 'не распознан'}\nОт: @{update.effective_user.username or ''} ({chat_id})"
        await update.message.reply_text(UI[lang]["consult_ok"], reply_markup=main_menu_kb(lang))
        USER[chat_id]["state"] = None

        # Шлём админу
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(ADMIN_CHAT_ID, f"📝 {lead_text}")
            except Exception:
                pass

        # Пишем в таблицу
        uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
        ts = datetime.datetime.utcnow().isoformat()
        sheet_append([ts, uname, str(chat_id), "Consult", text])

        # Отправляем email (если настроен)
        send_email("Sunera: новая заявка", lead_text)
        return

    # 5) Неизвестное сообщение
    await update.message.reply_text(cfg["unknown"], reply_markup=main_menu_kb(lang))

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.callback_query:
        return
    chat_id = update.effective_chat.id
    lang = USER.get(chat_id, {}).get("lang") or "Русский"
    data = update.callback_query.data

    if data.startswith("svc_"):
        idx = int(data.split("_")[1]) - 1
        txt = UI[lang]["services_list"][idx] if 0 <= idx < len(UI[lang]["services_list"]) else "—"
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(f"ℹ️ {txt}: подробности и предложение индивидуально после консультации.")
        return

    if data.startswith("faq_"):
        idx = int(data.split("_")[1]) - 1
        qa = UI[lang]["faq_items"][idx] if 0 <= idx < len(UI[lang]["faq_items"]) else ("—", "—")
        q, a = qa
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(f"❓ {q}\n\n💡 {a}")
        return

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
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    # Запускаем одновременно Telegram-бот и HTTP-сервер для Render
    await app.initialize()
    await app.start()
    log.info("Telegram bot started")

    # HTTP сервер — чтобы Render Web Service считал, что сервис жив
    await run_http_server()

    # Ждём бесконечно
    try:
        await asyncio.Event().wait()
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Stopped.")
