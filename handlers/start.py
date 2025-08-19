from telegram import Update
from telegram.ext import ContextTypes

# ===== команда /start =====
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот компании SUNERA.\n"
        "Я помогу вам оставить заявку, рассчитать солнечную систему или связаться с менеджером."
    )

# ===== команда /id =====
async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 Ваш Telegram ID: {update.effective_user.id}"
    )

# ===== команда /admin =====
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # здесь можно сделать проверку admin_id из config
    await update.message.reply_text(f"⚡ Админ-панель недоступна пользователю {user_id}")

# ===== обработка обычных текстов =====
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()

    if "цена" in text or "стоимость" in text:
        await update.message.reply_text("💶 Наша команда свяжется с вами для расчёта стоимости.")
    elif "контакт" in text or "телефон" in text:
        await update.message.reply_text("📞 Вы можете позвонить нам: +49 15510 361517")
    else:
        await update.message.reply_text(
            "🙏 Спасибо за сообщение! Наш менеджер ответит вам в ближайшее время."
        )
