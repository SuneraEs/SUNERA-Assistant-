import logging
import datetime
import math
import os
import phonenumbers
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import Dict, Any, List

from services import get_services
from utils import guess_lang_by_telegram, parse_phone

log = logging.getLogger("sunera-bot")

# ====== COMMANDS ======
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    services = get_services()
    chat_id = update.effective_chat.id
    user = update.effective_user
    lang = services.db.get_user_lang(chat_id) or guess_lang_by_telegram(update)
    
    services.db.save_user(chat_id, user.first_name, user.username, lang)
    services.db.save_dialog(chat_id, lang, "user", "/start")
    
    await update.message.reply_text(services.t.t(lang, "welcome"), reply_markup=services.t.main_menu_kb(lang))
    services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "welcome"))

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /id."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your chat ID is: `{chat_id}`", parse_mode=ParseMode.MARKDOWN_V2)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin."""
    services = get_services()
    chat_id = update.effective_chat.id
    if services.admin_chat_id and chat_id == int(services.admin_chat_id):
        sheets_status = "✅" if services.sheets_client else "❌"
        conn, cursor = services.db._get_connection()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        await update.message.reply_text(f"Статус: OK\nSheets: {sheets_status}\nПользователей в БД: {user_count}")
    else:
        await update.message.reply_text("No access.")

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения контакта."""
    services = get_services()
    chat_id = update.effective_chat.id
    user_data = context.user_data
    lang = services.db.get_user_lang(chat_id)
    
    if user_data.get("state") == "consult_phone" and update.message.contact:
        contact = update.message.contact
        user_data["lead"]["phone"] = parse_phone(contact.phone_number)
        if not user_data["lead"].get("name"):
            user_data["lead"]["name"] = contact.first_name or contact.last_name or ""
        
        user_data["state"] = "consult_city"
        services.db.save_dialog(chat_id, lang, "user", f"Contact shared: {user_data['lead']['phone']}")
        await update.message.reply_text(services.t.t(lang, "consult_prompt_city"), reply_markup=services.t.back_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "consult_prompt_city"))

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений, который объединяет логику меню и LLM."""
    services = get_services()
    if not update.message: return
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    
    user_data = context.user_data
    lang = services.db.get_user_lang(chat_id)
    state = user_data.get("state")

    # Обработка смены языка
    if text in services.t.LANGS:
        services.db.save_user(chat_id, update.effective_user.first_name, update.effective_user.username, text)
        await update.message.reply_text(services.t.t(text, "welcome"), reply_markup=services.t.main_menu_kb(text))
        services.db.save_dialog(chat_id, text, "user", text)
        services.db.save_dialog(chat_id, text, "assistant", services.t.t(text, "welcome"))
        return

    # Логируем сообщение пользователя
    services.db.save_dialog(chat_id, lang, "user", text)
    
    # Обработка кнопки "Назад"
    if text == services.t.t(lang, "back"):
        user_data["state"] = None
        user_data["lead"] = {}
        await update.message.reply_text(services.t.t(lang, "menu"), reply_markup=services.t.main_menu_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "menu"))
        return
    
    # Обработка состояний для лида
    if state == "consult_name":
        user_data["lead"]["name"] = text
        user_data["state"] = "consult_phone"
        await update.message.reply_text(services.t.t(lang, "consult_prompt_phone"), reply_markup=services.t.back_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "consult_prompt_phone"))
        return
    
    if state == "consult_phone":
        user_data["lead"]["phone"] = parse_phone(text)
        user_data["state"] = "consult_city"
        await update.message.reply_text(services.t.t(lang, "consult_prompt_city"), reply_markup=services.t.back_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "consult_prompt_city"))
        return
    
    if state == "consult_city":
        user_data["lead"]["city"] = text
        user_data["state"] = "consult_note"
        await update.message.reply_text(services.t.t(lang, "consult_prompt_note"), reply_markup=services.t.back_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "consult_prompt_note"))
        return
    
    if state == "consult_note":
        user_data["state"] = None
        user_data["lead"]["note"] = text
        lead = user_data["lead"]
        uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
        ts = datetime.datetime.utcnow().isoformat()
        
        lead_text = (
            f"🆕 Лид ({services.company_name})\n"
            f"Имя: {lead.get('name','')}\n"
            f"Тел: {lead.get('phone','')}\n"
            f"Город: {lead.get('city','')}\n"
            f"Комментарий: {lead.get('note','')}\n"
            f"От: {uname or chat_id}\n"
            f"Язык: {lang}"
        )
        if services.admin_chat_id:
            try: await context.bot.send_message(services.admin_chat_id, lead_text)
            except Exception as e: log.error(f"Failed to notify admin: {e}")
        
        if services.sheets_client:
            services.sheet_append([ts, uname, str(chat_id), lang, "Consult", f"Name={lead.get('name')};Phone={lead.get('phone')};City={lead.get('city')};Note={lead.get('note')}"])
        services.send_email(f"SUNERA lead: {lead.get('name')}", lead_text)
        await update.message.reply_text(services.t.t(lang, "consult_ok"), reply_markup=services.t.main_menu_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "consult_ok"))
        return

    # Логика для калькуляторов
    if state == "calc":
        try:
            parts = text.replace(",", ".").split()
            if len(parts) != 3: raise ValueError(services.t.t(lang, "calc_format_error"))
            amount, years, rate = float(parts[0]), int(parts[1]), float(parts[2])
            if min(amount, years, rate) <= 0: raise ValueError(services.t.t(lang, "calc_invalid_input"))
            rate_monthly, months = rate / 100 / 12, years * 12
            monthly_payment = (amount * rate_monthly) / (1 - math.pow(1 + rate_monthly, -months))
            total_payment = monthly_payment * months
            overpayment = total_payment - amount
            out = services.t.t(lang, "calc_result", monthly=round(monthly_payment, 2), total=round(total_payment, 2), over=round(overpayment, 2))
            await update.message.reply_text(out, reply_markup=services.t.main_menu_kb(lang))
            user_data["state"] = None
            uname = f"@{update.effective_user.username}" if update.effective_user.username else ""
            ts = datetime.datetime.utcnow().isoformat()
            if services.sheets_client:
                services.sheet_append([ts, uname, str(chat_id), lang, "LoanCalc", f"{text} -> {out}"])
            services.db.save_dialog(chat_id, lang, "assistant", out)
        except (ValueError, IndexError):
            await update.message.reply_text(services.t.t(lang, "calc_format_error"), reply_markup=services.t.back_kb(lang))
            services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "calc_format_error"))
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
            out = services.t.t(lang, "solar_calc_result", kw=kw, cost=cost, gen=yearly_gen, save=yearly_save, payback=payback, cost_per_kw=cost_per_kw)
            await update.message.reply_text(out, reply_markup=services.t.main_menu_kb(lang))
            user_data["state"] = None
            uname = f"@{update.effective_user.username}" if update.effective_user.username else ""
            ts = datetime.datetime.utcnow().isoformat()
            if services.sheets_client:
                services.sheet_append([ts, uname, str(chat_id), lang, "SolarCalc", f"{text} -> {out}"])
            services.db.save_dialog(chat_id, lang, "assistant", out)
        except (ValueError, IndexError):
            await update.message.reply_text(services.t.t(lang, "solar_format_error"), reply_markup=services.t.back_kb(lang))
            services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "solar_format_error"))
        return

    # Обработка кнопок главного меню
    if text == services.t.t(lang, "about_us"):
        txt = services.t.t(lang, "about_us_text").format(company=services.company_name, phone=services.company_phone, url=services.website_url)
        await update.message.reply_text(txt, reply_markup=services.t.main_menu_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", txt)
        return
    if text == services.t.t(lang, "services"):
        txt = services.t.t(lang, "services_info")
        await update.message.reply_text(txt, reply_markup=services.t.main_menu_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", txt)
        return
    if text == services.t.t(lang, "consult"):
        user_data["state"] = "consult_name"
        user_data["lead"] = {}
        await update.message.reply_text(services.t.t(lang, "consult_prompt_name"), reply_markup=services.t.back_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "consult_prompt_name"))
        return
    if text == services.t.t(lang, "solar_calc_button"):
        user_data["state"] = "solar_calc"
        await update.message.reply_text(services.t.t(lang, "solar_calc_prompt"), reply_markup=services.t.back_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "solar_calc_prompt"))
        return
    if text == services.t.t(lang, "calc_button"):
        user_data["state"] = "calc"
        await update.message.reply_text(services.t.t(lang, "calc_prompt"), reply_markup=services.t.back_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "calc_prompt"))
        return
    if text == services.t.t(lang, "website"):
        await update.message.reply_text(services.t.t(lang, "website_text", url=services.website_url))
        return
    if text == services.t.t(lang, "whatsapp"):
        await update.message.reply_text(services.t.t(lang, "whatsapp_text", wa=services.whatsapp_number.replace('+', '')))
        return
    if text == services.t.t(lang, "call_us"):
        await update.message.reply_text(services.t.t(lang, "call_us_text", phone=services.company_phone))
        return

    # Если бот не понял команду, используем LLM
    if services.llm_client and user_data.get("state") is None:
        try:
            await context.bot.send_chat_action(chat_id, "typing")
            dialog_history = services.db.get_dialog_history(chat_id)
            llm_response = services.llm_client.generate_response(dialog_history, text)
            
            if llm_response:
                await update.message.reply_text(llm_response, reply_to_message_id=update.message.message_id)
                services.db.save_dialog(chat_id, lang, "assistant", llm_response)
            else:
                await update.message.reply_text(services.t.t(lang, "unknown"), reply_to_message_id=update.message.message_id, reply_markup=services.t.main_menu_kb(lang))
                services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "unknown"))
        except Exception as e:
            log.error(f"LLM query failed: {e}")
            await update.message.reply_text(services.t.t(lang, "unknown"), reply_to_message_id=update.message.message_id, reply_markup=services.t.main_menu_kb(lang))
            services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "unknown"))
    else:
        await update.message.reply_text(services.t.t(lang, "unknown"), reply_markup=services.t.main_menu_kb(lang))
        services.db.save_dialog(chat_id, lang, "assistant", services.t.t(lang, "unknown"))

