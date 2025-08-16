# bot.py
import os
import asyncio
import logging
import datetime
from typing import Dict, Any, List

import phonenumbers
from aiohttp import web

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, UI, LANGS,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, LEADS_EMAILS,
    get_gsheets_credentials_dict, SPREADSHEET_ID, GSHEET_NAME,
    COMPANY_NAME, WEBSITE_URL, WHATSAPP_NUMBER, COMPANY_PHONE
)
import logging

# Настраиваем логирование, чтобы сообщения выводились в консоль
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ====== AI INTEGRATION (Hugging Face) ======
from huggingface_hub import InferenceClient

# Получаем токен Hugging Face из переменных окружения
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    log.warning("Hugging Face token not found. AI functionality will be disabled.")
    HF_CLIENT = None
else:
    # Инициализируем клиента Hugging Face
    model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
    try:
        HF_CLIENT = InferenceClient(model=model_name, token=HF_TOKEN)
        log.info(f"Hugging Face client initialized for model: {model_name}")
    except Exception as e:
        log.error(f"Failed to initialize Hugging Face client: {e}. AI functionality will be disabled.")
        HF_CLIENT = None

# ====== LOGGING ======
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("sunera-bot")

# ====== USER MEMORY ======
USER: Dict[int, Dict[str, Any]] = {}

# ====== CONSTANTS FOR SOLAR CALC ======
DEFAULT_PSH = 4.5               # средние солнечные часы/сутки
PERFORMANCE_RATIO = 0.80         # потери системы (кабели/темп. и т.д.)
COST_PER_KW_EUR = 1050.0         # ориент. цена за кВт установленной мощности

# ====== GOOGLE SHEETS ======
def _ensure_headers(ws):
    try:
        if not ws.row_values(1):
            ws.append_row(["TimestampUTC", "Username", "ChatID", "Lang", "Type", "Data"])
    except Exception:
        pass

def get_sheet():
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
            ws = sh.add_worksheet(title=GSHEET_NAME, rows=1000, cols=12)
        _ensure_headers(ws)
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

# ====== EMAIL ======
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
        log.info("Email sent.")
    except Exception as e:
        log.error(f"Email error: {e}")
# ====== AI HANDLER ======
async def ai_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет сообщение пользователя в AI-модель и отправляет ответ, 
    если пользователь не находится в процессе заполнения формы.
    """
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    
    # Не отвечаем, если пользователь находится в FSM-состоянии
    if USER.get(chat_id, {}).get("state") is not None:
        return

    # Не отвечаем, если не задан клиент AI
    if not HF_CLIENT:
        return
        
    lang = USER.get(chat_id, {}).get("lang") or "Русский"
    
    # Отправляем запрос в модель, показывая, что бот "печатает"
    await context.bot.send_chat_action(chat_id, "typing")

    try:
        prompt = f"Ответь на русском языке на следующий вопрос: {text}"
        
        ai_text = HF_CLIENT.text_generation(
            prompt=prompt,
            max_new_tokens=500,
            do_sample=True,
            temperature=0.7
        )
        
        await update.message.reply_text(ai_text, reply_to_message_id=update.message.message_id)
        
    except Exception as e:
        log.error(f"Произошла ошибка при работе с AI: {e}")
        await update.message.reply_text(t(lang, "unknown"), reply_to_message_id=update.message.message_id)


# ====== UI HELPERS ======
def t(lang: str, key: str, **fmt):
    cfg = UI.get(lang, UI["Русский"])
    val = cfg.get(key, "")
    return val.format(**fmt) if fmt else val

def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    cfg = UI.get(lang, UI["Русский"])
    rows = [
        [KeyboardButton(cfg["about_us"]), KeyboardButton(cfg["services"])],
        [KeyboardButton(cfg["consult"]), KeyboardButton(cfg["solar_calc_button"])],
        [KeyboardButton(cfg["calc_button"]), KeyboardButton(cfg["website"])],
        [KeyboardButton(cfg["whatsapp"]), KeyboardButton(cfg["call_us"])],
        [KeyboardButton(cfg["change_lang"])]
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def back_kb(lang: str) -> ReplyKeyboardMarkup:
    cfg = UI.get(lang, UI["Русский"])
    return ReplyKeyboardMarkup([[KeyboardButton(cfg["back"])]], resize_keyboard=True)

# ====== COMMANDS ======
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Сброс
    USER[chat_id] = {"lang": None, "state": None, "lead": {}}
    kb = ReplyKeyboardMarkup([[KeyboardButton(x)] for x in LANGS], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(UI["Русский"]["welcome"], reply_markup=kb)

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = USER.get(chat_id, {}).get("lang") or "Русский"
    await update.message.reply_text(t(lang, "your_id", cid=chat_id))

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if ADMIN_CHAT_ID and chat_id == ADMIN_CHAT_ID:
        sheets = "✅" if SHEET else "—"
        users_cnt = len(USER)
        await update.message.reply_text(
            t("Русский", "admin_status", sheets=sheets, users_cnt=users_cnt)
        )
    else:
        await update.message.reply_text("No access.")

# ====== TEXT HANDLER (FSM) ======
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    # Выбор языка
    if text in LANGS:
        USER[chat_id] = {"lang": text, "state": None, "lead": {}}
        await update.message.reply_text(t(text, "menu"), reply_markup=main_menu_kb(text))
        return

    # Если язык ещё не выбран
    if chat_id not in USER or USER[chat_id].get("lang") is None:
        kb = ReplyKeyboardMarkup([[KeyboardButton(x)] for x in LANGS], resize_keyboard=True)
        await update.message.reply_text(UI["Русский"]["welcome"], reply_markup=kb)
        return

    lang = USER[chat_id]["lang"]
    state = USER[chat_id].get("state")
    cfg = UI[lang]

    # Общие кнопки
    if text == cfg["change_lang"]:
        kb = ReplyKeyboardMarkup([[KeyboardButton(x)] for x in LANGS], resize_keyboard=True, one_time_keyboard=True)
        USER[chat_id]["state"] = None
        await update.message.reply_text(UI["Русский"]["welcome"], reply_markup=kb)
        return

    if text == cfg["back"]:
        USER[chat_id]["state"] = None
        await update.message.reply_text(t(lang, "menu"), reply_markup=main_menu_kb(lang))
        return

    if text == cfg["about_us"]:
        await update.message.reply_text(cfg["about_us_text"].format(company=COMPANY_NAME), reply_markup=main_menu_kb(lang))
        return

    if text == cfg["services"]:
        await update.message.reply_text(cfg["services_info"], reply_markup=main_menu_kb(lang))
        return

    if text == cfg["website"]:
        await update.message.reply_text(t(lang, "website_text", url=WEBSITE_URL), reply_markup=main_menu_kb(lang))
        return

    if text == cfg["whatsapp"]:
        wa = WHATSAPP_NUMBER.replace("+", "").replace(" ", "")
        await update.message.reply_text(t(lang, "whatsapp_text", wa=wa), reply_markup=main_menu_kb(lang))
        return

    if text == cfg["call_us"]:
        await update.message.reply_text(t(lang, "call_us_text", phone=COMPANY_PHONE), reply_markup=main_menu_kb(lang))
        return

    # Кредитный калькулятор
    if text == cfg["calc_button"]:
        USER[chat_id]["state"] = "calc"
        await update.message.reply_text(cfg["calc_prompt"], reply_markup=back_kb(lang))
        return

    if state == "calc":
        try:
            p_s_r = text.split()
            if len(p_s_r) != 3:
                raise ValueError
            principal = float(p_s_r[0])
            years = int(p_s_r[1])
            rate = float(p_s_r[2]) / 100.0
            if principal <= 0 or years <= 0 or rate <= 0:
                await update.message.reply_text(cfg["calc_invalid_input"], reply_markup=back_kb(lang))
                return
            m_rate = rate / 12.0
            n = years * 12
            monthly = principal * (m_rate * (1 + m_rate) ** n) / ((1 + m_rate) ** n - 1)
            total = monthly * n
            over = total - principal
            await update.message.reply_text(
                cfg["calc_result"].format(
                    monthly=f"{monthly:,.2f}", total=f"{total:,.2f}", over=f"{over:,.2f}"
                ).replace(",", " "),
                reply_markup=main_menu_kb(lang)
            )
            USER[chat_id]["state"] = None
        except Exception:
            await update.message.reply_text(cfg["calc_format_error"], reply_markup=back_kb(lang))
        return

    # Солнечный калькулятор
    if text == cfg["solar_calc_button"]:
        USER[chat_id]["state"] = "solar_calc"
        await update.message.reply_text(cfg["solar_calc_prompt"], reply_markup=back_kb(lang))
        return

    if state == "solar_calc":
        try:
            parts = text.split()
            if len(parts) not in (2, 3):
                raise ValueError
            consumption = float(parts[0])          # кВт·ч/мес
            tariff = float(parts[1])               # €/кВт·ч
            psh = float(parts[2]) if len(parts) == 3 else DEFAULT_PSH
            if min(consumption, tariff, psh) <= 0:
                await update.message.reply_text(cfg["solar_invalid_input"], reply_markup=back_kb(lang))
                return

            # kW = (kWh/мес)/30 / PSH / PR
            kw = round(consumption / 30.0 / psh / PERFORMANCE_RATIO, 2)
            cost = round(kw * COST_PER_KW_EUR, 2)
            yearly_gen = round(kw * psh * 365 * PERFORMANCE_RATIO, 0)
            yearly_save = round(yearly_gen * tariff, 2)
            payback = round(cost / yearly_save, 2) if yearly_save > 0 else 0.0

            await update.message.reply_text(
                cfg["solar_calc_result"].format(
                    kw=f"{kw:.2f}",
                    cost=f"{cost:,.2f}".replace(",", " "),
                    cost_per_kw=f"{COST_PER_KW_EUR:,.0f}".replace(",", " "),
                    gen=f"{yearly_gen:,.0f}".replace(",", " "),
                    save=f"{yearly_save:,.2f}".replace(",", " "),
                    payback=f"{payback:,.2f}".replace(",", " ")
                ),
                reply_markup=main_menu_kb(lang)
            )

            # лог в таблицу
            uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
            ts = datetime.datetime.utcnow().isoformat()
            sheet_append([ts, uname, str(chat_id), lang, "SolarCalc",
                          f"{consumption} kWh/mo; {tariff} €/kWh; PSH {psh} -> {kw} kW (~{cost} €)"])

            USER[chat_id]["state"] = None
        except Exception:
            await update.message.reply_text(cfg["solar_format_error"], reply_markup=back_kb(lang))
        return

    # Заявка/консультация — пошагово
    if text == cfg["consult"]:
        USER[chat_id]["state"] = "lead_name"
        USER[chat_id]["lead"] = {}
        await update.message.reply_text(cfg["consult_prompt_name"], reply_markup=back_kb(lang))
        return

    if state == "lead_name":
        USER[chat_id]["lead"]["name"] = text
        USER[chat_id]["state"] = "lead_phone"
        await update.message.reply_text(cfg["consult_prompt_phone"], reply_markup=back_kb(lang))
        return

    if state == "lead_phone":
        # нормализуем телефон
        phone_raw = text
        phone_fmt = ""
        for token in text.split():
            try:
                pn = phonenumbers.parse(token, None)
                if phonenumbers.is_valid_number(pn):
                    phone_fmt = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                    break
            except Exception:
                continue
        USER[chat_id]["lead"]["phone"] = phone_fmt or phone_raw
        USER[chat_id]["state"] = "lead_city"
        await update.message.reply_text(cfg["consult_prompt_city"], reply_markup=back_kb(lang))
        return

    if state == "lead_city":
        USER[chat_id]["lead"]["city"] = text
        USER[chat_id]["state"] = "lead_note"
        await update.message.reply_text(cfg["consult_prompt_note"], reply_markup=back_kb(lang))
        return

    if state == "lead_note":
        USER[chat_id]["lead"]["note"] = text
        USER[chat_id]["state"] = None

        lead = USER[chat_id]["lead"]
        uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
        ts = datetime.datetime.utcnow().isoformat()

        # Сообщение с лидом
        lead_text = (
            f"🆕 Лид ({COMPANY_NAME})\n\n"
            f"👤 Имя: {lead.get('name','')}\n"
            f"📞 Телефон: {lead.get('phone','')}\n"
            f"📍 Город/адрес: {lead.get('city','')}\n"
            f"📝 Комментарий: {lead.get('note','')}\n"
            f"👤 От: {uname or chat_id}\n"
            f"🌐 Язык: {lang}\n"
        )

        # Админу в Telegram
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(ADMIN_CHAT_ID, lead_text)
            except Exception:
                pass

        # В Google Sheets
        sheet_append([
            ts, uname, str(chat_id), lang, "Consult",
            f"Name={lead.get('name','')}; Phone={lead.get('phone','')}; City={lead.get('city','')}; Note={lead.get('note','')}"
        ])

        # На почту
        send_email("SUNERA: новая заявка", lead_text)

        await update.message.reply_text(cfg["consult_ok"], reply_markup=main_menu_kb(lang))
        # CTA WhatsApp
        wa = WHATSAPP_NUMBER.replace("+", "").replace(" ", "")
        await update.message.reply_text(t(lang, "whatsapp_text", wa=wa))
        return

    # По умолчанию
    await update.message.reply_text(cfg["unknown"], reply_markup=main_menu_kb(lang))

# ====== HEALTH HTTP SERVER (для Render free) ======
async def run_http_server():
    async def ok(request):
        return web.Response(text="OK")
    app = web.Application()
    app.add_routes([web.get("/", ok), web.get("/health", ok)])
    port = int(os.environ.get("PORT", "10000"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"Health server on 0.0.0.0:{port}")

# ====== MAIN ======
async def main():
    if not TELEGRAM_BOT_TOKEN:
        log.error("No TELEGRAM_BOT_TOKEN!")
        return

    application: Application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("id", cmd_id))
    application.add_handler(CommandHandler("admin", cmd_admin))
    # Сначала пробуем обработать сообщение AI-обработчиком
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response_handler))

# Если AI-обработчик "пропустил" сообщение, оно будет обработано вашей основной FSM-логикой
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    await application.initialize()
    await application.start()
    log.info("Telegram bot started (polling).")

    # Параллельно — health сервер для Render (иначе Web-сервис «усыпит» процесс)
    await run_http_server()

    try:
        await asyncio.Event().wait()
    finally:
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Stopped.")

