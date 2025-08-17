import logging
import datetime
import math
import os
from typing import Dict, Any, List
import phonenumbers
import gspread
from telegram import Update
from telegram.ext import ContextTypes
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from huggingface_hub import InferenceClient

from config import (
    TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, UI, LANGS,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, LEADS_EMAILS,
    get_gsheets_credentials_dict, SPREADSHEET_ID, GSHEET_NAME,
    COMPANY_NAME, WEBSITE_URL, WHATSAPP_NUMBER, COMPANY_PHONE
)
from utils import t, main_menu_kb, back_kb, guess_lang_by_telegram, parse_phone
from db import DB
from rag import RAG

# ======== НАСТРОЙКИ ЛОГГИРОВАНИЯ И ПЕРЕМЕННЫЕ СОСТОЯНИЯ ========
log = logging.getLogger("sunera-bot")

# Инициализация сервисов
db = DB()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_CLIENT = None
RAG_SYSTEM = None

if HF_TOKEN:
    model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
    try:
        HF_CLIENT = InferenceClient(model=model_name, token=HF_TOKEN)
        log.info(f"Hugging Face client initialized for model: {model_name}")
        RAG_SYSTEM = RAG(HF_CLIENT)
    except Exception as e:
        log.error(f"Failed to initialize Hugging Face client: {e}. AI functionality will be disabled.")

SHEET = None

def init_sheets():
    """Инициализирует подключение к Google Sheets."""
    global SHEET
    creds_dict = get_gsheets_credentials_dict()
    if not creds_dict or not SPREADSHEET_ID:
        log.warning("Sheets not configured (no creds or no spreadsheet id).")
        return None
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        try:
            ws = sh.worksheet(GSHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=GSHEET_NAME, rows=2000, cols=12)
        if not ws.row_values(1):
            ws.append_row(["TimestampUTC", "Username", "ChatID", "Lang", "Type", "Data"])
        SHEET = ws
        log.info("Google Sheets ready")
    except Exception as e:
        log.error("Sheets init failed: %s", e)
        SHEET = None

def sheet_append(row: List[str]):
    """Добавляет строку в лист Google Sheets."""
    try:
        if SHEET:
            SHEET.append_row(row)
    except Exception as e:
        log.error("Append to sheet failed: %s", e)

def send_email(subject: str, body: str):
    """Отправляет email-уведомление."""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and LEADS_EMAILS):
        log.warning("Email disabled or not configured.")
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(LEADS_EMAILS)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, LEADS_EMAILS, msg.as_string())
        log.info("Email sent successfully.")
    except Exception as e:
        log.error("Email send error: %s", e)

# ====== COMMANDS ======
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    chat_id = update.effective_chat.id
    lang = guess_lang_by_telegram(update)
    context.user_data["lang"] = lang
    db.save_user(chat_id, update.effective_user.first_name, update.effective_user.username, lang)
    db.save_dialog(chat_id, lang, "user", "/start")
    await update.message.reply_text(t(lang, "welcome"), reply_markup=main_menu_kb(lang))
    db.save_dialog(chat_id, lang, "assistant", t(lang, "welcome"))

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /id."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"chat_id: {chat_id}")

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin."""
    chat_id = update.effective_chat.id
    if ADMIN_CHAT_ID and chat_id == ADMIN_CHAT_ID:
        sheets_status = "✅" if SHEET else "❌"
        conn, cursor = db._get_connection()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        await update.message.reply_text(f"Статус: OK\nSheets: {sheets_status}\nПользователей в БД: {user_count}")
    else:
        await update.message.reply_text("No access.")

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения контакта."""
    chat_id = update.effective_chat.id
    user_data = context.user_data
    lang = user_data.get("lang", guess_lang_by_telegram(update))
    user_data["lang"] = lang
    
    if user_data.get("state") == "consult_phone" and update.message.contact:
        contact = update.message.contact
        user_data["lead"]["phone"] = parse_phone(contact.phone_number)
        if not user_data["lead"].get("name"):
            user_data["lead"]["name"] = contact.first_name or contact.last_name or ""
        
        user_data["state"] = "consult_city"
        db.save_dialog(chat_id, lang, "user", f"Contact shared: {user_data['lead']['phone']}")
        await update.message.reply_text(t(lang, "consult_prompt_city"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_city"))

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений, который объединяет логику меню и LLM."""
    if not update.message: return
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    
    user_data = context.user_data
    lang = user_data.get("lang", guess_lang_by_telegram(update))
    user_data["lang"] = lang
    state = user_data.get("state")

    menu_buttons = [t(l, key) for l in LANGS for key in UI] + [t(lang, "back")]
    is_menu_action = text in menu_buttons or text in LANGS

    if text in LANGS:
        user_data["lang"] = text
        user_data["state"] = None
        db.save_user(chat_id, update.effective_user.first_name, update.effective_user.username, text)
        db.save_dialog(chat_id, text, "user", text)
        await update.message.reply_text(t(text, "welcome"), reply_markup=main_menu_kb(text))
        db.save_dialog(chat_id, text, "assistant", t(text, "welcome"))
        return

    if not is_menu_action:
        db.save_dialog(chat_id, lang, "user", text)
    
    if text == t(lang, "back"):
        user_data["state"] = None
        user_data["lead"] = {}
        await update.message.reply_text(t(lang, "menu"), reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "menu"))
        return

    if state == "consult_name":
        user_data["lead"]["name"] = text
        user_data["state"] = "consult_phone"
        await update.message.reply_text(t(lang, "consult_prompt_phone"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_phone"))
        return
    if state == "consult_phone":
        user_data["lead"]["phone"] = parse_phone(text)
        user_data["state"] = "consult_city"
        await update.message.reply_text(t(lang, "consult_prompt_city"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_city"))
        return
    if state == "consult_city":
        user_data["lead"]["city"] = text
        user_data["state"] = "consult_note"
        await update.message.reply_text(t(lang, "consult_prompt_note"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_note"))
        return
    if state == "consult_note":
        user_data["state"] = None
        user_data["lead"]["note"] = text
        lead = user_data["lead"]
        uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
        ts = datetime.datetime.utcnow().isoformat()
        
        lead_text = (
            f"🆕 Лид ({COMPANY_NAME})\n"
            f"Имя: {lead.get('name','')}\n"
            f"Тел: {lead.get('phone','')}\n"
            f"Город: {lead.get('city','')}\n"
            f"Комментарий: {lead.get('note','')}\n"
            f"От: {uname or chat_id}\n"
            f"Язык: {lang}"
        )
        if ADMIN_CHAT_ID:
            try: await context.bot.send_message(ADMIN_CHAT_ID, lead_text)
            except Exception as e: log.error(f"Failed to notify admin: {e}")
        
        sheet_append([ts, uname, str(chat_id), lang, "Consult", f"Name={lead.get('name')};Phone={lead.get('phone')};City={lead.get('city')};Note={lead.get('note')}"])
        send_email(f"SUNERA lead: {lead.get('name')}", lead_text)
        await update.message.reply_text(t(lang, "consult_ok"), reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_ok"))
        return

    if state == "calc":
        try:
            parts = text.replace(",", ".").split()
            if len(parts) != 3: raise ValueError(t(lang, "calc_format_error"))
            amount, years, rate = float(parts[0]), int(parts[1]), float(parts[2])
            if min(amount, years, rate) <= 0: raise ValueError(t(lang, "calc_invalid_input"))
            rate_monthly, months = rate / 100 / 12, years * 12
            monthly_payment = (amount * rate_monthly) / (1 - math.pow(1 + rate_monthly, -months))
            total_payment = monthly_payment * months
            overpayment = total_payment - amount
            out = t(lang, "calc_result", monthly=round(monthly_payment, 2), total=round(total_payment, 2), over=round(overpayment, 2))
            await update.message.reply_text(out, reply_markup=main_menu_kb(lang))
            user_data["state"] = None
            uname = f"@{update.effective_user.username}" if update.effective_user.username else ""
            ts = datetime.datetime.utcnow().isoformat()
            sheet_append([ts, uname, str(chat_id), lang, "LoanCalc", f"{text} -> {out}"])
            db.save_dialog(chat_id, lang, "assistant", out)
        except ValueError:
            await update.message.reply_text(t(lang, "calc_format_error"), reply_markup=back_kb(lang))
            db.save_dialog(chat_id, lang, "assistant", t(lang, "calc_format_error"))
        return

    if state == "solar_calc":
        try:
            parts = text.replace(",", ".").split()
            if len(parts) < 2 or len(parts) > 3: raise ValueError
            consumption, tariff, psh = float(parts[0]), float(parts[1]), float(parts[2]) if len(parts) == 3 else 4.5
            if min(consumption, tariff, psh) <= 0: raise ValueError
            performance_ratio, cost_per_kw = 0.8, 1050
            kw = round(consumption / 30.0 / psh / performance_ratio, 2)
            cost = round(kw * cost_per_kw, 2)
            yearly_gen = round(kw * psh * 365 * performance_ratio, 0)
            yearly_save = round(yearly_gen * tariff, 2)
            payback = round(cost / yearly_save, 2) if yearly_save > 0 else 0.0
            out = t(lang, "solar_calc_result", kw=kw, cost=cost, gen=yearly_gen, save=yearly_save, payback=payback, cost_per_kw=cost_per_kw)
            await update.message.reply_text(out, reply_markup=main_menu_kb(lang))
            user_data["state"] = None
            uname = f"@{update.effective_user.username}" if update.effective_user.username else ""
            ts = datetime.datetime.utcnow().isoformat()
            sheet_append([ts, uname, str(chat_id), lang, "SolarCalc", f"{text} -> {out}"])
            db.save_dialog(chat_id, lang, "assistant", out)
        except (ValueError, IndexError):
            await update.message.reply_text(t(lang, "solar_format_error"), reply_markup=back_kb(lang))
            db.save_dialog(chat_id, lang, "assistant", t(lang, "solar_format_error"))
        return

    if text == t(lang, "about_us"):
        txt = t(lang, "about_us_text").format(company=COMPANY_NAME, phone=COMPANY_PHONE, url=WEBSITE_URL)
        await update.message.reply_text(txt, reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", txt)
        return
    if text == t(lang, "services"):
        txt = t(lang, "services_info")
        await update.message.reply_text(txt, reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", txt)
        return
    if text == t(lang, "consult"):
        user_data["state"] = "consult_name"
        user_data["lead"] = {}
        await update.message.reply_text(t(lang, "consult_prompt_name"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_name"))
        return
    if text == t(lang, "solar_calc_button"):
        user_data["state"] = "solar_calc"
        await update.message.reply_text(t(lang, "solar_calc_prompt"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "solar_calc_prompt"))
        return
    if text == t(lang, "calc_button"):
        user_data["state"] = "calc"
        await update.message.reply_text(t(lang, "calc_prompt"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "calc_prompt"))
        return
    if text == t(lang, "website"):
        await update.message.reply_text(t(lang, "website_text", url=WEBSITE_URL))
        return
    if text == t(lang, "whatsapp"):
        await update.message.reply_text(t(lang, "whatsapp_text", wa=WHATSAPP_NUMBER.replace('+', '')))
        return
    if text == t(lang, "call_us"):
        await update.message.reply_text(t(lang, "call_us_text", phone=COMPANY_PHONE))
        return

    if RAG_SYSTEM and user_data.get("state") is None:
        try:
            await context.bot.send_chat_action(chat_id, "typing")
            dialog_history = db.get_dialog_history(chat_id)
            rag_response = RAG_SYSTEM.query(text, dialog_history)
            
            if rag_response:
                await update.message.reply_text(rag_response, reply_to_message_id=update.message.message_id)
                db.save_dialog(chat_id, lang, "assistant", rag_response)
            else:
                await update.message.reply_text(t(lang, "unknown"), reply_to_message_id=update.message.message_id, reply_markup=main_menu_kb(lang))
                db.save_dialog(chat_id, lang, "assistant", t(lang, "unknown"))
        except Exception as e:
            log.error(f"RAG query failed: {e}")
            await update.message.reply_text(t(lang, "unknown"), reply_to_message_id=update.message.message_id, reply_markup=main_menu_kb(lang))
            db.save_dialog(chat_id, lang, "assistant", t(lang, "unknown"))
    else:
        await update.message.reply_text(t(lang, "unknown"), reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "unknown"))
