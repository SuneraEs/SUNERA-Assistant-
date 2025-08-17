import logging
import asyncio
import os
import math
import phonenumbers
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from sunera_db import DB
from sunera_t import T
from sunera_kb import main_menu_kb, back_kb
from email_sender import send_email
from huggingface_client import HuggingFaceClient
from google_sheets import GoogleSheets

# ======== КОНСТАНТЫ И НАСТРОЙКИ ========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
COMPANY_NAME = os.getenv("COMPANY_NAME", "SUNERA")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+34637722759")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://sunera.es")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "+34637722759")

# Настройка логирования
log = logging.getLogger("sunera-bot")
log.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

# Инициализация сервисов
db = DB()
t = T()
llm_client = HuggingFaceClient(HUGGING_FACE_TOKEN, LLM_MODEL)
sheets_client = GoogleSheets(GOOGLE_SHEETS_ID)

# ======== ОБРАБОТЧИКИ СООБЩЕНИЙ ========
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    log.info(f"Received /start from {user.id} (@{user.username} - {user.first_name})")
    db.save_user(user.id, user.first_name, user.username, user.language_code)
    db.save_dialog(chat_id, user.language_code, "user", "/start")
    
    await update.message.reply_text(t(user.language_code, "greeting"), reply_markup=main_menu_kb(user.language_code))
    db.save_dialog(chat_id, user.language_code, "assistant", t(user.language_code, "greeting"))

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /id."""
    await update.message.reply_text(f"Your chat ID is: {update.effective_chat.id}")

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /admin."""
    await update.message.reply_text("Admin access granted.", parse_mode=ParseMode.HTML)
    
async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для получения контакта."""
    chat_id = update.effective_chat.id
    user_data = context.user_data
    lang = db.get_user_lang(chat_id)
    contact = update.message.contact
    
    if user_data.get("state") != "consult_phone":
        await update.message.reply_text(t(lang, "unknown"), reply_markup=main_menu_kb(lang))
        return

    user_data["lead"]["phone"] = contact.phone_number
    
    lead = user_data["lead"]
    
    # Сохранение лида
    db.save_lead({
        "name": lead.get("name"),
        "phone": lead.get("phone"),
        "city": lead.get("city"),
        "note": lead.get("note")
    })
    
    # Отправка администратору
    uname = f"@{update.effective_user.username}" if update.effective_user.username else ""
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
            
    # Сохранение в Google Sheets
    if sheets_client.is_configured:
        try:
            sheets_client.save_lead({
                "name": lead.get("name"),
                "phone": lead.get("phone"),
                "city": lead.get("city"),
                "note": lead.get("note")
            })
            log.info("Lead saved to Google Sheets.")
        except Exception as e:
            log.warning(f"Failed to save to Google Sheets: {e}")
            
    # Отправка email
    send_email(f"SUNERA lead: {lead.get('name')}", lead_text)
    
    await update.message.reply_text(t(lang, "consult_ok"), reply_markup=main_menu_kb(lang))
    db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_ok"))
    user_data["state"] = None
    user_data["lead"] = {}
    return
    
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    chat_id = update.effective_chat.id
    text = update.message.text
    user_data = context.user_data
    
    lang = db.get_user_lang(chat_id)
    state = user_data.get("state")
    uname = f"@{update.effective_user.username}" if update.effective_user.username else ""

    # Обработка состояний для лида
    if text == t(lang, "back"):
        user_data["state"] = None
        await update.message.reply_text(t(lang, "greeting"), reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "greeting"))
        return
        
    if state == "consult_name":
        user_data["lead"]["name"] = text
        user_data["state"] = "consult_city"
        db.save_dialog(chat_id, lang, "user", text)
        await update.message.reply_text(t(lang, "consult_prompt_city"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_city"))
        return

    if state == "consult_city":
        user_data["lead"]["city"] = text
        user_data["state"] = "consult_note"
        db.save_dialog(chat_id, lang, "user", text)
        await update.message.reply_text(t(lang, "consult_prompt_note"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_note"))
        return

    if state == "consult_note":
        user_data["lead"]["note"] = text
        user_data["state"] = "consult_phone"
        db.save_dialog(chat_id, lang, "user", text)
        await update.message.reply_text(t(lang, "consult_prompt_phone"), reply_markup=back_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_prompt_phone"))
        return

    if state == "consult_phone":
        # Проверка номера телефона
        try:
            parsed_number = phonenumbers.parse(text, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError
            user_data["lead"]["phone"] = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except (phonenumbers.NumberParseException, ValueError):
            await update.message.reply_text(t(lang, "consult_invalid_phone"), reply_markup=back_kb(lang))
            db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_invalid_phone"))
            return
            
        db.save_dialog(chat_id, lang, "user", text)
        
        # Сохранение лида
        lead = user_data["lead"]
        db.save_lead({
            "name": lead.get("name"),
            "phone": lead.get("phone"),
            "city": lead.get("city"),
            "note": lead.get("note")
        })
        
        # Отправка администратору
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
                
        # Сохранение в Google Sheets
        if sheets_client.is_configured:
            try:
                sheets_client.save_lead({
                    "name": lead.get("name"),
                    "phone": lead.get("phone"),
                    "city": lead.get("city"),
                    "note": lead.get("note")
                })
                log.info("Lead saved to Google Sheets.")
            except Exception as e:
                log.warning(f"Failed to save to Google Sheets: {e}")
                
        # Отправка email
        send_email(f"SUNERA lead: {lead.get('name')}", lead_text)
        
        await update.message.reply_text(t(lang, "consult_ok"), reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", t(lang, "consult_ok"))
        user_data["state"] = None
        user_data["lead"] = {}
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

    # Если бот не понял команду, отправляем сообщение и ищем ответ в LLM
    try:
        dialog = db.get_dialog_history(chat_id, 10)
        llm_response = llm_client.generate_response(dialog, text)
        await update.message.reply_text(llm_response, reply_markup=main_menu_kb(lang))
        db.save_dialog(chat_id, lang, "assistant", llm_response)
    except Exception as e:
        log.error(f"LLM query failed: {e}")
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
