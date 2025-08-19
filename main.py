# main.py
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import config
from utils.sheets import sheets
from handlers import (
    cmd_start, cmd_id, cmd_admin, on_text,
    form_conv_handler, credit_conv_handler, solar_conv_handler,
    lang_pick_cb, cmd_lang
)

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger("sunera-bot")

async def on_error(update, context):
    log.exception("Update error", exc_info=context.error)
    if config.ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(config.ADMIN_CHAT_ID, f"⚠️ Error: {context.error}")
        except Exception:
            pass

async def main():
    # Sheets
    sheets.init()

    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN.startswith("PASTE_"):
        log.error("No TELEGRAM_BOT_TOKEN configured!")
        return

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("lang", cmd_lang))

    # конверсейшны (идут раньше on_text, чтобы они ловили текст-кнопки)
    app.add_handler(form_conv_handler())
    app.add_handler(credit_conv_handler())
    app.add_handler(solar_conv_handler())

    # коллбэки инлайн-языка
    app.add_handler(CallbackQueryHandler(lang_pick_cb, pattern=r"^lang:(ru|en|es|pl|de|uk)$"))

    # роутер «остального» текста
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    app.add_error_handler(on_error)

    log.info("Bot started. Polling...")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import telegram
    log.info(f"python-telegram-bot version: {telegram.__version__}")
    asyncio.run(main())
