# handlers/form.py
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from utils.common import pick_lang, t
from utils.validators import normalize_phone
from utils.sheets import sheets
import config

log = logging.getLogger("form")

NAME, PHONE, CITY, NOTE = range(4)

def contact_kb(lang: str):
    return ReplyKeyboardMarkup([[KeyboardButton(t("form_phone", lang), request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)

async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", pick_lang(user.language_code))
    await update.message.reply_text(t("form_name", lang))
    return NAME

async def form_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["form_name"] = (update.message.text or "").strip()
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(t("form_phone", lang), reply_markup=contact_kb(lang))
    return PHONE

async def form_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    phone_raw = ""
    if update.message.contact and update.message.contact.phone_number:
        phone_raw = update.message.contact.phone_number
    else:
        phone_raw = (update.message.text or "").strip()
    phone = normalize_phone(phone_raw)
    if not phone:
        await update.message.reply_text(t("phone_invalid", lang), reply_markup=contact_kb(lang))
        return PHONE
    context.user_data["form_phone"] = phone
    await update.message.reply_text(t("form_city", lang), reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True))
    return CITY

async def form_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["form_city"] = (update.message.text or "").strip()
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(t("form_note", lang))
    return NOTE

async def form_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["form_note"] = (update.message.text or "").strip()
    user = update.effective_user
    lang = context.user_data.get("lang", pick_lang(user.language_code))
    name = context.user_data.get("form_name", "")
    phone = context.user_data.get("form_phone", "")
    city = context.user_data.get("form_city", "")
    note = context.user_data.get("form_note", "")
    sheets.append_lead(user.username or user.full_name, user.id, lang, name, phone, city, note)
    if config.ADMIN_CHAT_ID:
        try:
            msg = f"🆕 Lead:\nName: {name}\nPhone: {phone}\nCity: {city}\nNote: {note}\nUser: @{user.username or ''} ({user.id})"
            await context.bot.send_message(config.ADMIN_CHAT_ID, msg)
        except Exception as e:
            log.error("Admin notify error: %s", e)
    await update.message.reply_text(t("form_ok", lang))
    return ConversationHandler.END

async def form_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌")
    return ConversationHandler.END

def form_conv_handler() -> ConversationHandler:
    pattern = r"^(📩|Заявка|Solicitud|Request|Zgłoszenie|Anfrage)"
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(pattern) & ~filters.COMMAND, start_form)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, form_name)],
            PHONE: [MessageHandler(filters.CONTACT, form_phone), MessageHandler(filters.TEXT & ~filters.COMMAND, form_phone)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, form_city)],
            NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, form_note)],
        },
        fallbacks=[CommandHandler("cancel", form_cancel)],
        name="form_conv",
        persistent=False,
    )
