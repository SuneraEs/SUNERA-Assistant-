import os
import json

# === ОБЯЗАТЕЛЬНО: Храним секреты в переменных окружения (на Render) ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0").strip() or 0)

# EMAIL (опционально — если хочешь получать письма с лидами)
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()         # напр. smtp.gmail.com
SMTP_PORT = int(os.getenv("SMTP_PORT", "587").strip() or 587)
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
LEADS_EMAILS = [e.strip() for e in os.getenv("LEADS_EMAILS", "").split(",") if e.strip()]

# Google Sheets (опционально)
GSHEETS_JSON_RAW = os.getenv("GSHEETS_JSON", "").strip()  # сюда вставляется ПОЛНЫЙ JSON сервис-аккаунта
GSHEET_NAME = os.getenv("GSHEET_NAME", "Sunera Leads").strip()

def get_gsheets_credentials_dict():
    """Возвращает dict из GSHEETS_JSON_RAW или None, если не задано."""
    if not GSHEETS_JSON_RAW:
        return None
    try:
        return json.loads(GSHEETS_JSON_RAW)
    except Exception:
        return None

# Языки интерфейса
LANGS = ["Русский", "Español", "English", "Polski", "Deutsch"]

# Текстовые шаблоны по языкам
UI = {
    "Русский": {
        "welcome": "Выберите язык / Elige idioma / Choose language / Wählen Sie Sprache / Wybierz język:",
        "menu": "Меню:",
        "services": "☀️ Наши услуги",
        "calc": "💰 Расчёт мощности",
        "consult": "📞 Консультация",
        "faq": "🛠️ FAQ",
        "back": "⬅️ Назад в меню",
        "services_info": "📋 Мы устанавливаем автономные, сетевые и гибридные солнечные системы.",
        "services_list": ["Автономные системы", "Сетевые системы", "Гибридные системы"],
        "calc_prompt": "Введите ваше потребление в кВт·ч в месяц (целое или дробное число):",
        "calc_result": "Оценочно потребуется система ~ {kw} кВт (расчёт из {cons} кВт·ч/мес, 4.5 солн.ч/день, КПД 0.8).",
        "calc_error": "Пожалуйста, введите корректное число, например 450 или 612.5",
        "consult_prompt": "Введите ваше имя и номер телефона (и, по желанию, город/страну):",
        "consult_ok": "✅ Заявка принята! Мы скоро свяжемся с вами.",
        "faq_title": "Частые вопросы:",
        "faq_items": [
            ("Сколько длится установка?", "Обычно 1–3 дня, в зависимости от объекта."),
            ("Какая гарантия?", "На панели до 25 лет. На инвертор — по паспорту производителя."),
            ("Есть ли рассрочка/кредит?", "Да, возможны партнёрские программы финансирования.")
        ],
        "unknown": "Не понял команду. Пожалуйста, воспользуйтесь кнопками ниже.",
        "admin_status": "Статус: бот работает.\nGoogle Sheets: {sheets}\nКэш пользователей: {users_cnt}",
        "your_id": "Ваш chat_id: {cid}"
    },
    "Español": {
        "welcome": "Elige idioma / Choose language / Wählen Sie Sprache / Wybierz język / Выберите язык:",
        "menu": "Menú:",
        "services": "☀️ Nuestros servicios",
        "calc": "💰 Cálculo de potencia",
        "consult": "📞 Consulta",
        "faq": "🛠️ FAQ",
        "back": "⬅️ Volver al menú",
        "services_info": "📋 Instalamos sistemas solares autónomos, conectados a red e híbridos.",
        "services_list": ["Sistemas autónomos", "Sistemas conectados a red", "Sistemas híbridos"],
        "calc_prompt": "Indica tu consumo mensual en kWh:",
        "calc_result": "Necesitas ~ {kw} kW (cálculo desde {cons} kWh/mes, 4.5 h sol/día, PR 0.8).",
        "calc_error": "Por favor, escribe un número válido, p. ej. 450 o 612.5",
        "consult_prompt": "Escribe tu nombre y teléfono (y ciudad/país opcional):",
        "consult_ok": "✅ ¡Solicitud recibida! Te contactaremos pronto.",
        "faq_title": "Preguntas frecuentes:",
        "faq_items": [
            ("¿Cuánto tarda la instalación?", "Normalmente 1–3 días."),
            ("¿Garantía?", "Paneles hasta 25 años; inversor según fabricante."),
            ("¿Financiación?", "Sí, trabajamos con bancos y planes de pago.")
        ],
        "unknown": "No entendí. Usa los botones de abajo, por favor.",
        "admin_status": "Estado: bot activo.\nGoogle Sheets: {sheets}\nUsuarios en caché: {users_cnt}",
        "your_id": "Tu chat_id: {cid}"
    },
    "English": {
        "welcome": "Choose language / Elige idioma / Wählen Sie Sprache / Wybierz język / Выберите язык:",
        "menu": "Menu:",
        "services": "☀️ Our Services",
        "calc": "💰 Power Sizing",
        "consult": "📞 Consultation",
        "faq": "🛠️ FAQ",
        "back": "⬅️ Back to menu",
        "services_info": "📋 We install off-grid, grid-tied and hybrid solar systems.",
        "services_list": ["Off-grid systems", "Grid-tied systems", "Hybrid systems"],
        "calc_prompt": "Enter your monthly consumption in kWh:",
        "calc_result": "You need ~ {kw} kW (from {cons} kWh/month, 4.5 sun-hours/day, PR 0.8).",
        "calc_error": "Please enter a valid number, e.g. 450 or 612.5",
        "consult_prompt": "Enter your name and phone (optionally city/country):",
        "consult_ok": "✅ Got it! We will contact you shortly.",
        "faq_title": "FAQ:",
        "faq_items": [
            ("How long is installation?", "Usually 1–3 days."),
            ("Warranty?", "Panels up to 25 years; inverter per manufacturer."),
            ("Financing?", "Yes, partner banks and payment plans available.")
        ],
        "unknown": "I didn't get that. Use the buttons below, please.",
        "admin_status": "Status: running.\nGoogle Sheets: {sheets}\nUsers cached: {users_cnt}",
        "your_id": "Your chat_id: {cid}"
    },
    "Polski": {
        "welcome": "Wybierz język / Choose language / Elige idioma / Wählen Sie Sprache / Выберите язык:",
        "menu": "Menu:",
        "services": "☀️ Nasze usługi",
        "calc": "💰 Dobór mocy",
        "consult": "📞 Konsultacja",
        "faq": "🛠️ FAQ",
        "back": "⬅️ Powrót do menu",
        "services_info": "📋 Montujemy systemy off-grid, on-grid i hybrydowe.",
        "services_list": ["Systemy autonomiczne", "Systemy sieciowe", "Systemy hybrydowe"],
        "calc_prompt": "Podaj zużycie miesięczne w kWh:",
        "calc_result": "Potrzebujesz ~ {kw} kW (na podstawie {cons} kWh/mies., 4.5 h słońca/dzień, PR 0.8).",
        "calc_error": "Wpisz poprawną liczbę, np. 450 lub 612.5",
        "consult_prompt": "Podaj imię i telefon (opcjonalnie miasto/kraj):",
        "consult_ok": "✅ Zgłoszenie przyjęte! Skontaktujemy się wkrótce.",
        "faq_title": "Najczęstsze pytania:",
        "faq_items": [
            ("Jak długo trwa montaż?", "Zwykle 1–3 dni."),
            ("Gwarancja?", "Panele do 25 lat; inwerter wg producenta."),
            ("Finansowanie?", "Tak, dostępne programy ratalne.")
        ],
        "unknown": "Nie zrozumiałem. Użyj proszę przycisków poniżej.",
        "admin_status": "Status: działa.\nGoogle Sheets: {sheets}\nUżytkownicy w pamięci: {users_cnt}",
        "your_id": "Twój chat_id: {cid}"
    },
    "Deutsch": {
        "welcome": "Wählen Sie Sprache / Choose language / Elige idioma / Wybierz język / Выберите язык:",
        "menu": "Menü:",
        "services": "☀️ Unsere Leistungen",
        "calc": "💰 Leistungsberechnung",
        "consult": "📞 Beratung",
        "faq": "🛠️ FAQ",
        "back": "⬅️ Zurück zum Menü",
        "services_info": "📋 Wir installieren Off-Grid, On-Grid und Hybrid-Solarsysteme.",
        "services_list": ["Autonome Systeme", "Netzgekoppelte Systeme", "Hybridsysteme"],
        "calc_prompt": "Geben Sie Ihren Monatsverbrauch in kWh ein:",
        "calc_result": "Sie benötigen ~ {kw} kW (aus {cons} kWh/Monat, 4.5 Sonnenstunden/Tag, PR 0.8).",
        "calc_error": "Bitte gültige Zahl eingeben, z. B. 450 oder 612.5",
        "consult_prompt": "Geben Sie Name und Telefonnummer ein (optional Stadt/Land):",
        "consult_ok": "✅ Anfrage erhalten! Wir kontaktieren Sie bald.",
        "faq_title": "Häufige Fragen:",
        "faq_items": [
            ("Wie lange dauert die Installation?", "Meist 1–3 Tage."),
            ("Garantie?", "Module bis 25 Jahre; Wechselrichter je Hersteller."),
            ("Finanzierung?", "Ja, Partnerbanken und Zahlungspläne.")
        ],
        "unknown": "Unklar. Bitte nutzen Sie die Tasten unten.",
        "admin_status": "Status: aktiv.\nGoogle Sheets: {sheets}\nBenutzer im Cache: {users_cnt}",
        "your_id": "Ihre chat_id: {cid}"
    }
}
