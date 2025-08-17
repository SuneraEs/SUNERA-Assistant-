import os
import asyncio
import logging
import datetime
import math
from typing import Dict, Any, List, Optional, Set
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from langdetect import detect as lang_detect, DetectorFactory

import db
from config import (
    TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, UI, LANGS,
    COMPANY_NAME, WEBSITE_URL, WHATSAPP_NUMBER, COMPANY_PHONE,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, LEADS_EMAILS
)
from utils import t, main_menu_kb, back_kb, parse_phone

# ======== НАСТРОЙКИ ЛОГГИРОВАНИЯ И ПЕРЕМЕННЫЕ СОСТОЯНИЯ ========
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("sunera-bot")

# Используем in-memory хранилище для состояний пользователей
USER: Dict[int, Dict[str, Any]] = {}
KNOWN_CHATS: Set[int] = set()

# Настройка langdetect для детерминированного поведения
DetectorFactory.seed = 0

# ======== E-MAIL ========
def send_email(subject: str, body: str):
    """Отправляет email-уведомление."""
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

# ======== ЛОГИКА БОТА ========
async def get_or_create_user_state(chat_id: int, update: Update) -> Dict[str, Any]:
    """Получает или создает состояние пользователя."""
    if chat_id not in USER:
        lang = guess_lang_by_telegram(update)
        USER[chat_id] = {"lang": lang, "state": None, "lead": {}}
    return USER[chat_id]

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    chat_id = update.effective_chat.id
    user_data = await get_or_create_user_state(chat_id, update)
    lang = user_data["lang"]
    await update.message.reply_text(t(lang, "welcome"), reply_markup=main_menu_kb(lang))

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /id."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"chat_id: {chat_id}")

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin."""
    chat_id = update.effective_chat.id
    if ADMIN_CHAT_ID and chat_id == ADMIN_CHAT_ID:
        await update.message.reply_text(f"Статус: OK\nПользователей в памяти: {len(USER)}")
    else:
        await update.message.reply_text("No access.")

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения контакта."""
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
    """Обработчик текстовых сообщений."""
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
        db.save_dialog(chat_id, lang, "user", text)
        db.save_dialog(chat_id, text, "assistant", t(text, "welcome"))
        return

    if text == t(lang, "back"):
        user_data["state"] = None
        user_data["lead"] = {}
        await update.message.reply_text(t(lang, "menu"), reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "user", text)
        db.save_dialog(chat_id, lang, "assistant", t(lang, "menu"))
        return

    # Логика для состояния "Заявка/Консультация"
    if state == "consult_name":
        user_data["lead"]["name"] = text
        user_data["state"] = "consult_phone"
        await update.message.reply_text(t(lang, "consult_prompt_phone"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "user", text)
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_phone"))
        return
    if state == "consult_phone":
        user_data["lead"]["phone"] = parse_phone(text)
        user_data["state"] = "consult_city"
        await update.message.reply_text(t(lang, "consult_prompt_city"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "user", text)
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_city"))
        return
    if state == "consult_city":
        user_data["lead"]["city"] = text
        user_data["state"] = "consult_note"
        await update.message.reply_text(t(lang, "consult_prompt_note"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "user", text)
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_note"))
        return
    if state == "consult_note":
        user_data["lead"]["note"] = text
        user_data["state"] = None
        lead = user_data["lead"]
        uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
        
        lead_data_to_save = {
            "username": uname,
            "chat_id": chat_id,
            "lang": lang,
            "name": lead.get("name"),
            "phone": lead.get("phone"),
            "city": lead.get("city"),
            "note": lead.get("note")
        }
        db.save_lead(lead_data_to_save)
        
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
            try:
                await context.bot.send_message(ADMIN_CHAT_ID, lead_text)
            except Exception as e:
                log.error(f"Failed to notify admin: {e}")
        
        send_email(f"SUNERA lead: {lead.get('name')}", lead_text)
        
        await update.message.reply_text(t(lang, "consult_ok"), reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "user", text)
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_ok"))
        return

    # Логика для кредитного калькулятора
    if state == "calc":
        db.save_dialog(chat_id, lang, "user", text)
        try:
            parts = text.replace(",", ".").split()
            if len(parts) != 3: raise ValueError(t(lang, "calc_format_error"))
            amount = float(parts[0])
            years = int(parts[1])
            rate = float(parts[2])
            if min(amount, years, rate) <= 0: raise ValueError(t(lang, "calc_invalid_input"))

            rate_monthly = rate / 100 / 12
            months = years * 12
            monthly_payment = (amount * rate_monthly) / (1 - math.pow(1 + rate_monthly, -months))
            total_payment = monthly_payment * months
            overpayment = total_payment - amount

            out = t(lang, "calc_result", monthly=round(monthly_payment, 2), total=round(total_payment, 2), over=round(overpayment, 2))
            await update.message.reply_text(out, reply_markup=main_menu_kb(lang))
            user_data["state"] = None
            db.save_calculation(chat_id, lang, "", "loan", text, out)
            db.save_dialog(chat_id, lang, "assistant", out)
        except ValueError:
            await update.message.reply_text(t(lang, "calc_format_error"), reply_markup=back_kb(lang))
            db.save_dialog(chat_id, lang, "assistant", t(lang, "calc_format_error"))
        return

    # Логика для солнечного калькулятора
    if state == "solar_calc":
        db.save_dialog(chat_id, lang, "user", text)
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
            user_data["state"] = None
            uname = f"@{update.effective_user.username}" if update.effective_user.username else ""
            db.save_calculation(chat_id, lang, uname, "solar", text, out)
            db.save_dialog(chat_id, lang, "assistant", out)
        except (ValueError, IndexError):
            await update.message.reply_text(t(lang, "solar_format_error"), reply_markup=back_kb(lang))
            db.save_dialog(chat_id, lang, "assistant", t(lang, "solar_format_error"))
        return

    # Обработка кнопок главного меню
    db.save_dialog(chat_id, lang, "user", text)
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

    # Если бот не понял команду
    await update.message.reply_text(t(lang, "unknown"), reply_markup=main_menu_kb(lang))
    db.save_dialog(chat_id, lang, "assistant", t(lang, "unknown"))

# ======== ТОЧКА ВХОДА ========
async def main():
    """Главная функция для запуска бота."""
    if not TELEGRAM_BOT_TOKEN:
        log.error("No TELEGRAM_BOT_TOKEN set in env!")
        return
    
    db.init_db()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("id", cmd_id))
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, on_text))
    application.add_handler(MessageHandler(filters.CONTACT & filters.ChatType.PRIVATE, on_contact))
    
    await application.initialize()
    await application.start()
    log.info("Bot started")
    try:
        # Удерживаем программу запущенной
        await asyncio.Event().wait()
    finally:
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Stopped")
