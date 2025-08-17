import logging
import json
import time
import datetime
from typing import Dict, Any, List, Optional, Set
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, filters
from config import (
    UI, LANGS, COMPANY_NAME, WEBSITE_URL, WHATSAPP_NUMBER, COMPANY_PHONE, ADMIN_CHAT_ID,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, LEADS_EMAILS,
    SPREADSHEET_ID, GSHEET_NAME, MEMORY_SHEET_NAME,
    get_gsheets_credentials_dict
)
from utils import t, main_menu_kb, back_kb, parse_phone
import gspread

log = logging.getLogger("handlers")

USER: Dict[int, Dict[str, Any]] = {}
KNOWN_CHATS: Set[int] = set()
DIALOG: Dict[int, List[Dict[str, str]]] = {}

SHEET = None
MEMORY_SHEET = None

def init_sheets():
    global SHEET, MEMORY_SHEET
    try:
        creds = get_gsheets_credentials_dict()
        if not creds:
            log.error("Google Sheets credentials not found.")
            return

        client = gspread.service_account_from_dict(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        
        try:
            ws = sh.worksheet(GSHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=GSHEET_NAME, rows=2000, cols=12)
        
        try:
            mem = sh.worksheet(MEMORY_SHEET_NAME)
        except gspread.WorksheetNotFound:
            mem = sh.add_worksheet(title=MEMORY_SHEET_NAME, rows=2000, cols=12)

        if not ws.row_values(1):
            ws.append_row(["TimestampUTC", "Username", "ChatID", "Lang", "Type", "Data"])
        if not mem.row_values(1):
            mem.append_row(["TimestampUTC", "ChatID", "Lang", "Type", "Q", "A"])
        
        SHEET = ws
        MEMORY_SHEET = mem
        log.info("Google Sheets ready")

    except Exception as e:
        log.error("Sheets init failed: %s", e)
        SHEET = None
        MEMORY_SHEET = None

def sheet_append(row: List[str], memory: bool = False):
    try:
        if memory and MEMORY_SHEET:
            MEMORY_SHEET.append_row(row)
        elif SHEET:
            SHEET.append_row(row)
    except Exception as e:
        log.error("Append sheet failed: %s", e)

def send_email(subject: str, body: str):
    if not SMTP_USER or not SMTP_PASS or not LEADS_EMAILS:
        log.warning("Email disabled or not configured.")
        return
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import smtplib

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


async def get_or_create_user_state(chat_id: int, update: Update) -> Dict[str, Any]:
    if chat_id not in USER:
        from utils import guess_lang_by_text
        lang = guess_lang_by_text(update.effective_message.text)
        USER[chat_id] = {"lang": lang, "state": None, "lead": {}}
    return USER[chat_id]

def dialog_add(chat_id: int, role: str, content: str, limit: int = 10):
    hist = DIALOG.setdefault(chat_id, [])
    hist.append({"role": role, "content": content})
    if len(hist) > limit:
        del hist[0:len(hist) - limit]
    
    # Сохраняем в Google Sheets
    if MEMORY_SHEET:
        sheet_append([datetime.datetime.utcnow().isoformat(), str(chat_id), USER.get(chat_id, {}).get("lang", "Русский"), "dialog", role, content], memory=True)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = await get_or_create_user_state(chat_id, update)
    lang = user_data["lang"]
    await update.message.reply_text(t(lang, "welcome"), reply_markup=main_menu_kb(lang))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = await get_or_create_user_state(chat_id, update)
    lang = user_data["lang"]
    await update.message.reply_text(t(lang, "help_text"))

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"chat_id: {chat_id}")

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if ADMIN_CHAT_ID and chat_id == ADMIN_CHAT_ID:
        sheets_status = "✅" if SHEET and MEMORY_SHEET else "❌"
        await update.message.reply_text(f"Статус: OK\nSheets: {sheets_status}\nПользователей в памяти: {len(USER)}")
    else:
        await update.message.reply_text("No access.")

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = await get_or_create_user_state(chat_id, update)
    lang = user_data["lang"]
    
    if user_data["state"] == "consult_name" and update.message.contact:
        contact = update.message.contact
        user_data["lead"]["name"] = contact.first_name or contact.last_name or ""
        user_data["lead"]["phone"] = parse_phone(contact.phone_number)
        user_data["state"] = "consult_city"
        await update.message.reply_text(t(lang, "consult_prompt_city"), reply_markup=back_kb(lang))

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    user_data = await get_or_create_user_state(chat_id, update)
    lang = user_data["lang"]
    state = user_data["state"]

    if text in LANGS:
        user_data["lang"] = text
        user_data["state"] = None
        await update.message.reply_text(t(text, "welcome"), reply_markup=main_menu_kb(text))
        return

    if text == t(lang, "back"):
        user_data["state"] = None
        user_data["lead"] = {}
        await update.message.reply_text(t(lang, "menu"), reply_markup=main_menu_kb(lang))
        return

    if state == "consult_name":
        user_data["lead"]["name"] = text
        user_data["state"] = "consult_phone"
        await update.message.reply_text(t(lang, "consult_prompt_phone"), reply_markup=back_kb(lang))
        return

    if state == "consult_phone":
        user_data["lead"]["phone"] = parse_phone(text)
        user_data["state"] = "consult_city"
        await update.message.reply_text(t(lang, "consult_prompt_city"), reply_markup=back_kb(lang))
        return

    if state == "consult_city":
        user_data["lead"]["city"] = text
        user_data["state"] = "consult_note"
        await update.message.reply_text(t(lang, "consult_prompt_note"), reply_markup=back_kb(lang))
        return

    if state == "consult_note":
        user_data["lead"]["note"] = text
        user_data["state"] = None
        lead = user_data["lead"]
        uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
        ts = datetime.datetime.utcnow().isoformat()
        lead_text = f"🆕 Лид ({COMPANY_NAME})\nИмя: {lead.get('name','')}\nТел: {lead.get('phone','')}\nГород: {lead.get('city','')}\nКомментарий: {lead.get('note','')}\nОт: {uname or chat_id}\nЯзык: {lang}"
        
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(ADMIN_CHAT_ID, lead_text)
            except Exception as e:
                log.error(f"Failed to notify admin: {e}")
        
        if SHEET:
            sheet_append([ts, uname, str(chat_id), lang, "Consult", f"Name={lead.get('name')};Phone={lead.get('phone')};City={lead.get('city')};Note={lead.get('note')}"])
        
        send_email(f"SUNERA lead: {lead.get('name')}", lead_text)
        
        await update.message.reply_text(t(lang, "consult_ok"), reply_markup=main_menu_kb(lang))
        dialog_add(chat_id, "assistant", t(lang, "consult_ok"))
        return

    if state == "solar_calc":
        try:
            parts = text.replace(",", ".").split()
            if len(parts) < 2 or len(parts) > 3: raise ValueError
            consumption = float(parts[0])
            tariff = float(parts[1])
            psh = float(parts[2]) if len(parts) == 3 else 4.5
            if min(consumption, tariff, psh) <= 0: raise ValueError
            kw = round(consumption / 30.0 / psh / 0.8, 2)
            cost_per_kw = 1050
            cost = round(kw * cost_per_kw, 2)
            yearly_gen = round(kw * psh * 365 * 0.8, 0)
            yearly_save = round(yearly_gen * tariff, 2)
            payback = round(cost / yearly_save, 2) if yearly_save > 0 else 0.0
            out = t(lang, "solar_calc_result", kw=kw, cost=cost, gen=yearly_gen, save=yearly_save, payback=payback, cost_per_kw=cost_per_kw)
            await update.message.reply_text(out, reply_markup=main_menu_kb(lang))
            if SHEET:
                sheet_append([datetime.datetime.utcnow().isoformat(), f"@{update.effective_user.username}" if update.effective_user.username else "", str(chat_id), lang, "SolarCalc", f"{consumption}kWh/mo; {tariff}€/kWh; PSH{psh} -> {kw}kW"])
            user_data["state"] = None
        except (ValueError, IndexError):
            await update.message.reply_text(t(lang, "solar_format_error"), reply_markup=back_kb(lang))
        return

    if text == t(lang, "about_us"):
        txt = t(lang, "about_us_text").format(company=COMPANY_NAME, phone=COMPANY_PHONE, url=WEBSITE_URL)
        await update.message.reply_text(txt, reply_markup=main_menu_kb(lang))
        dialog_add(chat_id, "assistant", txt)
        return
    
    if text == t(lang, "services"):
        txt = t(lang, "services_info")
        await update.message.reply_text(txt, reply_markup=main_menu_kb(lang))
        dialog_add(chat_id, "assistant", txt)
        return

    if text == t(lang, "consult"):
        user_data["state"] = "consult_name"
        user_data["lead"] = {}
        await update.message.reply_text(t(lang, "consult_prompt_name"), reply_markup=back_kb(lang))
        return

    if text == t(lang, "solar_calc_button"):
        user_data["state"] = "solar_calc"
        await update.message.reply_text(t(lang, "solar_calc_prompt"), reply_markup=back_kb(lang))
        return
    
    if text == t(lang, "calc_button"):
        user_data["state"] = "calc"
        await update.message.reply_text(t(lang, "calc_prompt"), reply_markup=back_kb(lang))
        return

    await update.message.reply_text(t(lang, "unknown"), reply_markup=main_menu_kb(lang))

