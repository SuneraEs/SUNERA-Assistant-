

import os
import json

# === ОБЯЗАТЕЛЬНО: Храним секреты в переменных окружения ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# === EMAIL (опционально - если хочешь слать email) ===
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "0"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
LEADS_EMAILS = [e.strip() for e in os.getenv("LEADS_EMAILS", "").split(",") if e]

# === Google Sheets (опционально) ===
GSHEETS_JSON_RAW = os.getenv("GSHEETS_JSON_RAW")
GSHEET_NAME = os.getenv("GSHEET_NAME")

def get_gsheets_credentials_dict():
    if not GSHEETS_JSON_RAW:
        return None
    try:
        return json.loads(GSHEETS_JSON_RAW)
    except json.JSONDecodeError:
        return None

# === Новые переменные для сайта, фото и контактов ===
WEBSITE_URL = "https://example.com"  # Временно, так как сайта пока нет
COMPANY_PHONE = "+48507716338"  # Замените на ваш номер
WHATSAPP_PHONE = "+48507716338"  # Замените на ваш номер
ABOUT_US_PHOTO_URL = "https://upload.wikimedia.org/wikipedia/commons/e/e9/Solar_panels_on_a_house_roof_in_Germany_-_2010.jpg"  # Временное фото

# === UI (пользовательский интерфейс) и языки ===
UI = {
    "Русский": {
        "welcome": "Привет! Я бот-помощник SUNERA. Пожалуйста, выберите язык:",
        "menu": "Выберите, что вас интересует:",
        "about_us": "О компании",
        "services": "Услуги",
        "consult": "Оставить заявку",
        "website": "Сайт",
        "call_us": "Позвонить нам",
        "whatsapp": "WhatsApp",
        "back": "⬅️ Назад",
        "about_us_text": "Мы - компания SUNERA. Занимаемся установкой солнечных электростанций, чтобы вы могли экономить на счетах за электроэнергию и делать свой вклад в защиту экологии.",
        "about_us_photo": ABOUT_US_PHOTO_URL,
        "services_info": "Мы предлагаем полный спектр услуг...",
        "consult_prompt": "Пожалуйста, оставьте ваш телефон или другой контакт, и наш менеджер свяжется с вами:",
        "consult_ok": "Спасибо! Мы скоро свяжемся с вами.",
        "website_text": "Наш сайт: {url}",
        "call_us_text": "Позвонить нам: {phone}",
        "whatsapp_text": "Наш WhatsApp: {phone}",
        "unknown": "Извините, я не понял. Пожалуйста, выберите опцию из меню.",
        "your_id": "Ваш Chat ID: {cid}",
        "admin_status": "📊 Статус бота:\nGoogle Sheets: {sheets}\nПользователей: {users_cnt}"
    },
    "English": {
        "welcome": "Hello! I am SUNERA assistant bot. Please select your language:",
        "menu": "Select what you are interested in:",
        "about_us": "About Us",
        "services": "Services",
        "consult": "Leave a Request",
        "website": "Website",
        "call_us": "Call Us",
        "whatsapp": "WhatsApp",
        "back": "⬅️ Back",
        "about_us_text": "We are SUNERA, a company that specializes in installing solar power plants to help you save on electricity bills and protect the environment.",
        "about_us_photo": ABOUT_US_PHOTO_URL,
        "services_info": "We offer a full range of services...",
        "consult_prompt": "Please leave your phone number or other contact, and our manager will get in touch with you:",
        "consult_ok": "Thank you! We will contact you shortly.",
        "website_text": "Our website: {url}",
        "call_us_text": "Call us: {phone}",
        "whatsapp_text": "Our WhatsApp: {phone}",
        "unknown": "Sorry, I didn't understand. Please select an option from the menu.",
        "your_id": "Your Chat ID: {cid}",
        "admin_status": "📊 Bot Status:\nGoogle Sheets: {sheets}\nUsers: {users_cnt}"
    },
    # Дополнительные языки могут быть добавлены аналогично
}

# Проверка наличия обязательных переменных
if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables.")
if not LEADS_EMAILS:
    raise ValueError("LEADS_EMAILS must contain at least one email address.")

LANGS = list(UI.keys())


