# handlers/credit.py
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from utils.common import pick_lang, t, loan_calc

ASK = range(1)

async def start_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", pick_lang(update.effective_user.language_code))
    await update.message.reply_text(t("credit_prompt", lang))
    return ASK

async def credit_parse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", pick_lang(update.effective_user.language_code))
    parts = (update.message.text or "").replace(",", ".").split()
    if len(parts) != 3:
        await update.message.reply_text(t("credit_badfmt", lang))
        return ASK
    try:
        amount = float(parts[0]); years = float(parts[1]); rate = float(parts[2])
        m, total, over = loan_calc(amount, years, rate)
        await update.message.reply_text(t("credit_result", lang).format(monthly=m, total=total, over=over))
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(t("credit_badfmt", lang))
        return ASK

async def credit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌")
    return ConversationHandler.END

def credit_conv_handler() -> ConversationHandler:
    pattern = r"(Кредит|Loan|crédito|Kredyt|Kredit|Кредитний)"
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(pattern) & ~filters.COMMAND, start_credit)],
        states={ASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, credit_parse)]},
        fallbacks=[CommandHandler("cancel", credit_cancel)],
        name="credit_conv",
        persistent=False,
    )
