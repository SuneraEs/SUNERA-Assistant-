# handlers/solar.py
from telegram import Update
from telegram.ext import ConversationHandler, MessageHandler, CommandHandler, filters
from utils.common import pick_lang, t
import config

ASK = range(1)

async def start_solar(update: Update, context):
    lang = context.user_data.get("lang", pick_lang(update.effective_user.language_code))
    await update.message.reply_text(t("solar_prompt", lang))
    return ASK

async def solar_parse(update: Update, context):
    lang = context.user_data.get("lang", pick_lang(update.effective_user.language_code))
    parts = (update.message.text or "").replace(",", ".").split()
    if len(parts) not in (2,3):
        await update.message.reply_text(t("solar_badfmt", lang)); return ASK
    try:
        consumption = float(parts[0]); tariff = float(parts[1]); psh = float(parts[2]) if len(parts)==3 else 4.5
        if consumption <=0 or tariff <=0 or psh <=0:
            raise ValueError
        perf = config.SOLAR_PERFORMANCE
        kw_needed = consumption / (psh * 30 * perf)
        cost_per_kw = config.SOLAR_COST_PER_KW
        cost = kw_needed * cost_per_kw
        yearly_gen = kw_needed * psh * 365 * perf
        yearly_save = yearly_gen * tariff
        payback = cost / yearly_save if yearly_save>0 else 0
        msg = t("solar_result", lang).format(kw=round(kw_needed,2), cost=round(cost,0), cperkW=int(cost_per_kw), gen=int(yearly_gen), save=int(yearly_save), payback=round(payback,1))
        await update.message.reply_text(msg)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text(t("solar_badfmt", lang))
        return ASK

async def solar_cancel(update: Update, context):
    await update.message.reply_text("❌")
    return ConversationHandler.END

def solar_conv_handler() -> ConversationHandler:
    pattern = r"(Солнечный|Solar|Słoneczny|PV|Сонячний)"
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(pattern) & ~filters.COMMAND, start_solar)],
        states={ASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, solar_parse)]},
        fallbacks=[CommandHandler("cancel", solar_cancel)],
        name="solar_conv",
        persistent=False,
    )
