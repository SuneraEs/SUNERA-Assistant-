import phonenumbers
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from langdetect import detect as lang_detect, DetectorFactory
DetectorFactory.seed = 0

from config import UI, LANGS, WEBSITE_URL, WHATSAPP_NUMBER, COMPANY_PHONE, COMPANY_NAME

def t(lang: str, key: str, **fmt):
    cfg = UI.get(lang, UI["Русский"])
    val = cfg.get(key, "")
    return val.format(**fmt) if fmt else val

def main_menu_kb(lang: str):
    cfg = UI.get(lang, UI["Русский"])
    rows = [
        [KeyboardButton(cfg["about_us"]), KeyboardButton(cfg["services"])],
        [KeyboardButton(cfg["consult"]), KeyboardButton(cfg["solar_calc_button"])],
        [KeyboardButton(cfg["calc_button"]), KeyboardButton(cfg["website"])],
        [KeyboardButton(cfg["whatsapp"]), KeyboardButton(cfg["call_us"])],
        [KeyboardButton(cfg["change_lang"])]
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def back_kb(lang: str):
    cfg = UI.get(lang, UI["Русский"])
    return ReplyKeyboardMarkup([[KeyboardButton(cfg["back"])]], resize_keyboard=True)

def socials_inline():
    rows = [
        [InlineKeyboardButton(text="Website", url=WEBSITE_URL), InlineKeyboardButton(text="WhatsApp", url=f"https://wa.me/{WHATSAPP_NUMBER.replace('+','').replace(' ','')}")],
    ]
    return InlineKeyboardMarkup(rows)

def guess_lang_by_telegram(update) -> str:
    try:
        code = (update.effective_user.language_code or "").lower()
        if code.startswith("ru") or code.startswith("uk") or code.startswith("be"):
            return "Русский"
        if code.startswith("es"):
            return "Español"
        if code.startswith("pl"):
            return "Polski"
        if code.startswith("de"):
            return "Deutsch"
    except Exception:
        pass
    return "English"

def guess_lang_by_text(text: str) -> str:
    try:
        code = lang_detect(text or "")
        if code.startswith("ru"): return "Русский"
        if code.startswith("es"): return "Español"
        if code.startswith("pl"): return "Polski"
        if code.startswith("de"): return "Deutsch"
    except Exception:
        pass
    return "English"

def parse_phone(text: str) -> str:
    phone_fmt = ""
    for token in text.split():
        try:
            pn = phonenumbers.parse(token, None)
            if phonenumbers.is_valid_number(pn):
                phone_fmt = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                break
        except Exception:
            continue
    return phone_fmt
