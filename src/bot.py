lang))
        return

    if text == cfg["whatsapp"]:
        await update.message.reply_text(t(lang, "whatsapp_text", phone=WHATSAPP_PHONE), reply_markup=main_menu_kb(lang))
        return

    if state == "consult":
        phone = ""
        for token in text.split():
            try:
                pn = phonenumbers.parse(token, None)
                if phonenumbers.is_valid_number(pn):
                    phone = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                    break
            except Exception:
                continue

        lead_text = f"Новая заявка: {text}\nТелефон: {phone or 'не распознан'}\nОт: @{update.effective_user.username or ''} ({chat_id})"
        await update.message.reply_text(UI[lang]["consult_ok"], reply_markup=main_menu_kb(lang))
        USER[chat_id]["state"] = None

        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(ADMIN_CHAT_ID, f"📝 {lead_text}")
            except Exception:
                pass

        uname = f"@{update.effective_user.username}" if update.effective_user and update.effective_user.username else ""
        ts = datetime.datetime.utcnow().isoformat()
        sheet_append([ts, uname, str(chat_id), "Consult", text])
        send_email("Sunera: новая заявка", lead_text)
        return

    await update.message.reply_text(cfg["unknown"], reply_markup=main_menu_kb(lang))

# ---------- ЗАПУСК: Telegram + HTTP-сервер (для Render) ----------
async def run_http_server():
    async def handle_health(request):
        return web.Response(text="OK")
    app = web.Application()
    app.add_routes([web.get("/", handle_health), web.get("/health", handle_health)])
    port = int(web.os.environ.get("PORT", "10000"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"HTTP server started on 0.0.0.0:{port}")

async def main():
    if not TELEGRAM_BOT_TOKEN:
        log.error("No TELEGRAM_BOT_TOKEN in env!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    await app.initialize()
    await app.start()
    log.info("Telegram bot started")

    await run_http_server()

    try:
        await asyncio.Event().wait()
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":  # Обратите внимание на правильное имя
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Stopped.")


