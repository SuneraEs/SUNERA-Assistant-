# handlers/lang.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from utils.common import t
import config

LANG_LABELS = {
    "ru": "Русский 🇷🇺",
    "en": "English 🇬🇧",
    "es": "Español 🇪🇸",
    "pl": "Polski 🇵🇱",
    "de": "Deutsch 🇩🇪",
    "uk": "Українська 🇺🇦",
}

def build_lang_kb(curr: str) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for code, label in LANG_LABELS.items():
        prefix = "✅ " if code == curr else ""
        row.append(InlineKeyboardButton(f"{prefix}{label}", callback_data=f"lang:{code}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(rows)

async def lang_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", config.DEFAULT_LANG)
    await update.message.reply_text("Choose language / Выберите язык:", reply_markup=build_lang_kb(lang))

async def lang_pick_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""
    if not data.startswith("lang:"):
        return
    new_lang = data.split(":", 1)[1]
    if new_lang not in config.SUPPORTED_LANGS:
        return
    context.user_data["lang"] = new_lang
    await q.edit_message_text("✅ Language updated.", reply_markup=build_lang_kb(new_lang))
    # и сразу покажем меню:
    from utils.common import main_menu, t
    await q.message.chat.send_message(t("welcome", new_lang), reply_markup=main_menu(new_lang))

async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await lang_menu(update, context)

def lang_handlers():
    return [
        CallbackQueryHandler(lang_pick_cb, pattern=r"^lang:(ru|en|es|pl|de|uk)$"),
        CommandHandler("lang", cmd_lang),
    ]
