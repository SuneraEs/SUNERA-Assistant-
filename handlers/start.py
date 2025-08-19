# handlers/start.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
import config
from utils.common import pick_lang, t, main_menu, anti_flood_ok

log = logging.getLogger("start")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang") or pick_lang(user.language_code)
    context.user_data["lang"] = lang
    await update.message.reply_text(t("welcome", lang), reply_markup=main_menu(lang))

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"chat_id: {user.id}")

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin OK")

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.effective_user
    if not anti_flood_ok(user.id, config.ANTI_FLOOD_WINDOW_SEC):
        return
    lang = context.user_data.get("lang") or pick_lang(user.language_code)
    txt = (update.message.text or "").strip()

    if txt == t("menu_about", lang):
        await update.message.reply_text(t("about_text", lang))
        return
    if txt == t("menu_services", lang):
        await update.message.reply_text("• Grid-tied\n• Hybrid (with batteries)\n• Off-grid\n• O&M")
        return
    if txt == t("menu_site", lang):
        await update.message.reply_text(config.WEBSITE_URL)
        return
    if txt == t("menu_whatsapp", lang):
        await update.message.reply_text(f"https://wa.me/{config.WHATSAPP_NUMBER}")
        return
    if txt == t("menu_call", lang):
        await update.message.reply_text(f"☎ {config.COMPANY_PHONE}")
        return
    if txt == t("menu_lang", lang):
        from .lang import lang_menu
        await lang_menu(update, context)
        return

    await update.message.reply_text(t("unknown", lang))
