# config.py
import os

# TELEGRAM
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "PASTE_TELEGRAM_TOKEN_HERE")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))  # 0 -> disabled

# COMPANY / CONTACTS
COMPANY_NAME = os.getenv("COMPANY_NAME", "SUNERA Energy")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://sunera-energy.com")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "+48507716338").lstrip("+")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+48507716338")

# SMTP (optional)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
LEADS_EMAILS = [e.strip() for e in os.getenv("LEADS_EMAILS", "").split(",") if e.strip()]

# GOOGLE SHEETS
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "PUT_YOUR_SPREADSHEET_ID_HERE")
GSHEET_NAME = os.getenv("GSHEET_NAME", "Leads")

def get_gsheets_credentials_dict():
    import json, os
    raw = os.getenv("GSHEETS_JSON", "").strip()
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            return None
    if os.path.exists("gsheets.json"):
        try:
            import io
            with open("gsheets.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

# LANGS
SUPPORTED_LANGS = ["ru", "en", "es", "pl", "de", "uk"]
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "ru").lower()
if DEFAULT_LANG not in SUPPORTED_LANGS:
    DEFAULT_LANG = "ru"

# TUNABLES
ANTI_FLOOD_WINDOW_SEC = int(os.getenv("ANTI_FLOOD_WINDOW_SEC", "1"))
SOLAR_COST_PER_KW = float(os.getenv("SOLAR_COST_PER_KW", "1000"))
SOLAR_PERFORMANCE = float(os.getenv("SOLAR_PERFORMANCE", "0.75"))
