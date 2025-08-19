import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN
# ===== ИСПРАВЛЕННЫЕ ИМПОРТЫ =====
from handlers.start import cmd_start, cmd_id, cmd_admin, on_text
from handlers.form import form_conv_handler
from handlers.credit import credit_conv_handler
from handlers.solar import solar_conv_handler
from handlers.lang import lang_handlers

# ======== НАСТРОЙКА ЛОГГИРОВАНИЯ ========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
log = logging.getLogger("sunera-bot")

# ======== ТОЧКА ВХОДА ========
async def main():
    """Запуск Telegram-бота"""

    if not TELEGRAM_BOT_TOKEN:
        log.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return

    # создаём приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # команды
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("id", cmd_id))
    application.add_handler(CommandHandler("admin", cmd_admin))

    # текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    # разговорные сценарии
    application.add_handler(form_conv_handler)
    application.add_handler(credit_conv_handler)
    application.add_handler(solar_conv_handler)

    # языковые команды
    for handler in lang_handlers:
        application.add_handler(handler)

    log.info("🤖 Sunera Telegram Bot запущен и ждёт сообщения...")

    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import telegram
    log.info(f"Используется python-telegram-bot версии: {telegram.__version__}")
    asyncio.run(main())
