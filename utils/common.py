# utils/common.py
import time
from typing import Tuple, Dict
from telegram import ReplyKeyboardMarkup, KeyboardButton
from .texts import TEXTS

# simple per-user anti-flood cache
_last_msgs: Dict[int, float] = {}

def anti_flood_ok(user_id: int, window_sec: int) -> bool:
    now = time.time()
    last = _last_msgs.get(user_id, 0)
    if now - last >= window_sec:
        _last_msgs[user_id] = now
        return True
    return False

def pick_lang(lang_code: str) -> str:
    if not lang_code:
        return "ru"
    code = lang_code.lower()
    for k in ["ru","en","es","pl","de","uk"]:
        if code.startswith(k):
            return k
    return "ru"

def t(key: str, lang: str) -> str:
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ru", ""))

def main_menu(lang: str) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(t("menu_about", lang)), KeyboardButton(t("menu_services", lang))],
        [KeyboardButton(t("menu_form", lang))],
        [KeyboardButton(t("menu_credit", lang)), KeyboardButton(t("menu_solar", lang))],
        [KeyboardButton(t("menu_site", lang)), KeyboardButton(t("menu_whatsapp", lang))],
        [KeyboardButton(t("menu_call", lang)), KeyboardButton(t("menu_lang", lang))],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def loan_calc(amount: float, years: float, rate_pct: float) -> Tuple[float, float, float]:
    n = int(years * 12)
    r = (rate_pct / 100) / 12
    if n <= 0 or amount <= 0 or rate_pct <= 0:
        raise ValueError("bad values")
    m = amount * r * (1 + r) ** n / ((1 + r) ** n - 1)
    total = m * n
    over = total - amount
    return (round(m, 2), round(total, 2), round(over, 2))
