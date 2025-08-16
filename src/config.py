# config.py

# ========= TELEGRAM =========
TELEGRAM_BOT_TOKEN = "7899846022:AAGQUoQYXmSFIc79knLYvZJfNkEmz6zHM_U"
ADMIN_CHAT_ID = 7721420208  # твой ID

# ========= COMPANY / CONTACTS =========
COMPANY_NAME = "SUNERA Energy"
WEBSITE_URL = "https://sunera-energy.com"    # временно так; поменяешь на свой сайт
WHATSAPP_NUMBER = "+48507716338"
COMPANY_PHONE = "+48507716338"               # можно вывести кнопкой “Позвонить”

# ========= EMAIL (SMTP) =========
# Gmail: нужно создать пароль приложения (App Password) в аккаунте Google.
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "sunera.eu@gmail.com"
SMTP_PASS = "APP_PASSWORD_HERE"  # ← сюда вставь пароль приложения Gmail

LEADS_EMAILS = ["sunera.eu@gmail.com"]  # можно список

# ========= GOOGLE SHEETS =========
# 1) Создай гугл-таблицу (пустую), скопируй её ID из URL
#    https://docs.google.com/spreadsheets/d/<ID>/edit
SPREADSHEET_ID = "PUT_YOUR_SPREADSHEET_ID_HERE"
GSHEET_NAME = "Leads"  # лист, куда пишем

# 2) Сервисный аккаунт: JSON положи в переменную окружения GSHEETS_JSON на Render,
#    либо файл gsheets.json в корень репо.
def get_gsheets_credentials_dict():
    import os, json
    raw = os.environ.get("GSHEETS_JSON", "").strip()
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            return None
    # Фолбэк: файл в репозитории (если решишь хранить локально)
    if os.path.exists("gsheets.json"):
        try:
            with open("gsheets.json", "r", encoding="utf-8") as f:
                return __import__("json").load(f)
        except Exception:
            return None
    return None

# ========= UI / LANGS =========
LANGS = ["Русский", "English", "Español", "Polski", "Deutsch"]

UI = {
    "Русский": {
        "welcome": "🌍 Выберите язык / Choose language / Elige idioma / Wybierz język / Sprache wählen:",
        "menu": "Главное меню:",
        "about_us": "ℹ️ О компании",
        "services": "☀️ Услуги",
        "consult": "📩 Заявка/Консультация",
        "calc_button": "💳 Кредитный калькулятор",
        "solar_calc_button": "🔆 Солнечный калькулятор",
        "website": "🌐 Сайт",
        "whatsapp": "💬 WhatsApp",
        "call_us": "📞 Позвонить",
        "change_lang": "🌍 Сменить язык",
        "back": "⬅️ Назад",

        "about_us_text": (
            "☀️ {company} — проектирование и установка солнечных электростанций.\n"
            "• Сетевые, автономные, гибридные решения\n"
            "• Гарантия до 25 лет на панели\n"
            "• Помощь с субсидиями и финансированием\n\n"
            "Напишите нам — подберем систему под ваш объект."
        ),
        "services_info": (
            "Мы предлагаем:\n"
            "• Сетевые СЭС — экономия на счете за электричество\n"
            "• Гибридные СЭС — + аккумуляторы, работа при отключении сети\n"
            "• Автономные СЭС — полная независимость\n"
            "• Мониторинг, обслуживание, апгрейд"
        ),

        "consult_prompt_name": "Как вас зовут?",
        "consult_prompt_phone": "Ваш телефон (с кодом страны)?",
        "consult_prompt_city": "Город/адрес установки?",
        "consult_prompt_note": "Кратко опишите задачу (мощность, бюджет, сроки) — по желанию:",
        "consult_ok": "✅ Спасибо! Заявка принята. Менеджер свяжется с вами.",

        "calc_prompt": "Введи через пробел: СУММА(€) СРОК_ЛЕТ СТАВКА_%\nНапример: 8000 5 8",
        "calc_result": "Ежемесячный платёж: {monthly} €\nСумма выплат: {total} €\nПереплата: {over} €",
        "calc_invalid_input": "Сумма, срок и ставка должны быть > 0.",
        "calc_format_error": "Формат неверный. Пример: 8000 5 8",

        "solar_calc_prompt": (
            "Введи через пробел: ПОТРЕБЛЕНИЕ_кВт·ч_в_месяц ТАРИФ_€/кВт·ч [PSH]\n"
            "PSH — средние солнечные часы/день (по умолчанию 4.5). Пример: 450 0.22 4.2"
        ),
        "solar_calc_result": (
            "Рекомендованная мощность системы: ~{kw} кВт\n"
            "Оценочная стоимость: ~{cost} € (по {cost_per_kw} €/кВт)\n"
            "Годовая генерация: ~{gen} кВт·ч\n"
            "Годовая экономия: ~{save} €\n"
            "Окупаемость: ~{payback} лет"
        ),
        "solar_format_error": "Формат неверный. Пример: 450 0.22 4.2",
        "solar_invalid_input": "Все значения должны быть > 0.",

        "website_text": "Наш сайт: {url}",
        "call_us_text": "Позвонить: {phone}",
        "whatsapp_text": "Напишите нам в WhatsApp: https://wa.me/{wa}",

        "faq_title": "Частые вопросы:",
        "faq_items": [
            ("Сколько длится установка?", "Обычно 1–3 дня в зависимости от сложности."),
            ("Какая гарантия?", "На панели — до 25 лет, на инверторы — до 10 лет."),
            ("Нужны ли разрешения?", "Помогаем с оформлением согласований и документами."),
            ("Есть ли рассрочка/кредит?", "Да, подберем финансовое решение.")
        ],

        "your_id": "Ваш chat_id: {cid}",
        "admin_status": "Статус: OK\nSheets: {sheets}\nПользователей в памяти: {users_cnt}",
        "unknown": "Не понял. Пожалуйста, выберите пункт меню."
    },

    # Остальные языки — краткие (чтобы не раздувать код). При желании дополним.
    "English": {
        "welcome": "🌍 Choose language:",
        "menu": "Main menu:",
        "about_us": "ℹ️ About us",
        "services": "☀️ Services",
        "consult": "📩 Request/Consultation",
        "calc_button": "💳 Loan calculator",
        "solar_calc_button": "🔆 Solar calculator",
        "website": "🌐 Website",
        "whatsapp": "💬 WhatsApp",
        "call_us": "📞 Call us",
        "change_lang": "🌍 Change language",
        "back": "⬅️ Back",
        "about_us_text": "☀️ {company} — solar PV solutions. Grid-tied, hybrid, off-grid.",
        "services_info": "Grid-tied, Hybrid (with batteries), Off-grid, O&M.",
        "consult_prompt_name": "Your name?",
        "consult_prompt_phone": "Your phone (with country code)?",
        "consult_prompt_city": "City/address?",
        "consult_prompt_note": "Short note (optional):",
        "consult_ok": "✅ Thanks! We'll contact you shortly.",
        "calc_prompt": "Enter: AMOUNT YEARS RATE_% (e.g. 8000 5 8)",
        "calc_result": "Monthly: {monthly} €\nTotal: {total} €\nOverpayment: {over} €",
        "calc_invalid_input": "All values must be > 0.",
        "calc_format_error": "Wrong format. Example: 8000 5 8",
        "solar_calc_prompt": "Enter: CONSUMPTION_kWh_month TARIFF_€/kWh [PSH=4.5]",
        "solar_calc_result": (
            "Recommended system: ~{kw} kW\n"
            "Estimated cost: ~{cost} € (at {cost_per_kw} €/kW)\n"
            "Yearly generation: ~{gen} kWh\n"
            "Yearly savings: ~{save} €\n"
            "Payback: ~{payback} years"
        ),
        "solar_format_error": "Wrong format. Example: 450 0.22 4.2",
        "solar_invalid_input": "All values must be > 0.",
        "website_text": "Website: {url}",
        "call_us_text": "Call: {phone}",
        "whatsapp_text": "WhatsApp: https://wa.me/{wa}",
        "faq_title": "FAQ:",
        "faq_items": [
            ("Install time?", "Usually 1–3 days."),
            ("Warranty?", "Panels up to 25 years."),
            ("Permits?", "We help with paperwork."),
            ("Financing?", "Yes, we help with financing.")
        ],
        "your_id": "Your chat_id: {cid}",
        "admin_status": "Status: OK\nSheets: {sheets}\nUsers in memory: {users_cnt}",
        "unknown": "Please use the menu."
    },

    "Español": {
        "welcome": "🌍 Elige idioma:",
        "menu": "Menú:",
        "about_us": "ℹ️ Sobre la empresa",
        "services": "☀️ Servicios",
        "consult": "📩 Solicitud/Consulta",
        "calc_button": "💳 Calculadora de crédito",
        "solar_calc_button": "🔆 Calculadora solar",
        "website": "🌐 Sitio web",
        "whatsapp": "💬 WhatsApp",
        "call_us": "📞 Llamar",
        "change_lang": "🌍 Cambiar idioma",
        "back": "⬅️ Atrás",
        "about_us_text": "☀️ {company} — sistemas fotovoltaicos.",
        "services_info": "Conectadas a red, híbridas, aisladas.",
        "consult_prompt_name": "¿Cómo te llamas?",
        "consult_prompt_phone": "¿Tu teléfono (con prefijo)?",
        "consult_prompt_city": "Ciudad/dirección:",
        "consult_prompt_note": "Nota (opcional):",
        "consult_ok": "✅ ¡Gracias! Te contactaremos.",
        "calc_prompt": "Ingresa: MONTO AÑOS TASA_% (ej: 8000 5 8)",
        "calc_result": "Mensual: {monthly} €\nTotal: {total} €\nIntereses: {over} €",
        "calc_invalid_input": "Todos los valores > 0.",
        "calc_format_error": "Formato incorrecto. Ej: 8000 5 8",
        "solar_calc_prompt": "Ingresa: CONSUMO_kWh_mes TARIFA_€/kWh [PSH=4.5]",
        "solar_calc_result": "Sistema: ~{kw} kW\nCosto: ~{cost} €\nAhorro anual: ~{save} €\nRetorno: ~{payback} años",
        "solar_format_error": "Formato incorrecto.",
        "solar_invalid_input": "Valores > 0.",
        "website_text": "Sitio: {url}",
        "call_us_text": "Llamar: {phone}",
        "whatsapp_text": "WhatsApp: https://wa.me/{wa}",
        "faq_title": "FAQ:",
        "faq_items": [
            ("¿Tiempo de instalación?", "Normalmente 1–3 días."),
            ("¿Garantía?", "Paneles hasta 25 años."),
            ("¿Permisos?", "Te ayudamos con trámites."),
            ("¿Financiación?", "Sí, opciones disponibles.")
        ],
        "your_id": "chat_id: {cid}",
        "admin_status": "Estado: OK\nSheets: {sheets}\nUsuarios: {users_cnt}",
        "unknown": "Usa el menú, por favor."
    },

    "Polski": {
        "welcome": "🌍 Wybierz język:",
        "menu": "Menu główne:",
        "about_us": "ℹ️ O firmie",
        "services": "☀️ Usługi",
        "consult": "📩 Zgłoszenie/Konsultacja",
        "calc_button": "💳 Kalkulator kredytu",
        "solar_calc_button": "🔆 Kalkulator PV",
        "website": "🌐 Strona",
        "whatsapp": "💬 WhatsApp",
        "call_us": "📞 Zadzwoń",
        "change_lang": "🌍 Zmień język",
        "back": "⬅️ Wstecz",
        "about_us_text": "☀️ {company} — instalacje fotowoltaiczne.",
        "services_info": "On-grid, hybrydowe, off-grid.",
        "consult_prompt_name": "Jak masz na imię?",
        "consult_prompt_phone": "Telefon (z kierunkowym)?",
        "consult_prompt_city": "Miasto/adres:",
        "consult_prompt_note": "Krótka notatka (opcjonalnie):",
        "consult_ok": "✅ Dziękujemy! Skontaktujemy się.",
        "calc_prompt": "Podaj: KWOTA LATA OPROC_% (np. 8000 5 8)",
        "calc_result": "Miesięcznie: {monthly} €\nRazem: {total} €\nNadpłata: {over} €",
        "calc_invalid_input": "Wartości muszą być > 0.",
        "calc_format_error": "Błędny format. Np. 8000 5 8",
        "solar_calc_prompt": "Podaj: ZUŻYCIE_kWh/mies TARYFA_€/kWh [PSH=4.5]",
        "solar_calc_result": "System: ~{kw} kW\nKoszt: ~{cost} €\nOszczędności/rok: ~{save} €\nZwrot: ~{payback} lat",
        "solar_format_error": "Błędny format.",
        "solar_invalid_input": "Wartości > 0.",
        "website_text": "Strona: {url}",
        "call_us_text": "Zadzwoń: {phone}",
        "whatsapp_text": "WhatsApp: https://wa.me/{wa}",
        "faq_title": "FAQ:",
        "faq_items": [
            ("Czas montażu?", "Zazwyczaj 1–3 dni."),
            ("Gwarancja?", "Panele do 25 lat."),
            ("Pozwolenia?", "Pomagamy w formalnościach."),
            ("Finansowanie?", "Tak, dostępne opcje.")
        ],
        "your_id": "Twój chat_id: {cid}",
        "admin_status": "Status: OK\nSheets: {sheets}\nUżytk.: {users_cnt}",
        "unknown": "Wybierz z menu."
    },

    "Deutsch": {
        "welcome": "🌍 Sprache wählen:",
        "menu": "Hauptmenü:",
        "about_us": "ℹ️ Über uns",
        "services": "☀️ Leistungen",
        "consult": "📩 Anfrage/Beratung",
        "calc_button": "💳 Kreditrechner",
        "solar_calc_button": "🔆 PV-Rechner",
        "website": "🌐 Website",
        "whatsapp": "💬 WhatsApp",
        "call_us": "📞 Anrufen",
        "change_lang": "🌍 Sprache ändern",
        "back": "⬅️ Zurück",
        "about_us_text": "☀️ {company} — PV-Anlagen.",
        "services_info": "Netzgekoppelt, Hybrid, Insel.",
        "consult_prompt_name": "Wie heißen Sie?",
        "consult_prompt_phone": "Telefon (mit Ländervorwahl)?",
        "consult_prompt_city": "Stadt/Adresse:",
        "consult_prompt_note": "Kurzbeschreibung (optional):",
        "consult_ok": "✅ Danke! Wir melden uns.",
        "calc_prompt": "Eingabe: BETRAG JAHRE ZINS_% (z.B. 8000 5 8)",
        "calc_result": "Monatlich: {monthly} €\nGesamt: {total} €\nZinsen: {over} €",
        "calc_invalid_input": "Alle Werte > 0.",
        "calc_format_error": "Falsches Format. Bsp.: 8000 5 8",
        "solar_calc_prompt": "Eingabe: VERBRAUCH_kWh/Monat TARIF_€/kWh [PSH=4.5]",
        "solar_calc_result": "Anlage: ~{kw} kW\nKosten: ~{cost} €\nErsparnis/Jahr: ~{save} €\nAmortisation: ~{payback} Jahre",
        "solar_format_error": "Falsches Format.",
        "solar_invalid_input": "Werte > 0.",
        "website_text": "Website: {url}",
        "call_us_text": "Anrufen: {phone}",
        "whatsapp_text": "WhatsApp: https://wa.me/{wa}",
        "faq_title": "FAQ:",
        "faq_items": [
            ("Dauer der Montage?", "Meist 1–3 Tage."),
            ("Garantie?", "Module bis 25 Jahre."),
            ("Genehmigungen?", "Wir helfen bei den Unterlagen."),
            ("Finanzierung?", "Ja, verfügbar.")
        ],
        "your_id": "Ihr chat_id: {cid}",
        "admin_status": "Status: OK\nSheets: {sheets}\nNutzer im Speicher: {users_cnt}",
        "unknown": "Bitte Menü verwenden."
    },
}
