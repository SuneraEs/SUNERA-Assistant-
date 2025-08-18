import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

from handlers import (
    cmd_start, cmd_id, cmd_admin,
    on_text, on_contact
)
from services import init_services, get_services

# ======== НАСТРОЙКИ ЛОГГИРОВАНИЯ ========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger("sunera-bot")

# ======== ТОЧКА ВХОДА ========
async def main():
    """Главная функция для запуска бота."""
    
    # Инициализация всех сервисов
    await init_services()
    services = get_services()

    if not services.telegram_bot_token:
        log.error("No TELEGRAM_BOT_TOKEN set in env!")
        return

    application = Application.builder().token(services.telegram_bot_token).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("id", cmd_id))
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, on_text))
    application.add_handler(MessageHandler(filters.CONTACT & filters.ChatType.PRIVATE, on_contact))
    
    log.info("Telegram bot started. Polling for updates...")
    
    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import telegram
    log.info(f"Running python-telegram-bot version: {telegram.__version__}")
    asyncio.run(main())
