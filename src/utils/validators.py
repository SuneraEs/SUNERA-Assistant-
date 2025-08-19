# utils/validators.py
import phonenumbers

DEFAULT_REGION = "PL"  # можно поменять

def normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    txt = raw.strip().replace(" ", "").replace("-", "")
    try:
        if txt.startswith("+"):
            num = phonenumbers.parse(txt, None)
        else:
            num = phonenumbers.parse(txt, DEFAULT_REGION)
        if phonenumbers.is_valid_number(num):
            return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
        return None
    except Exception:
        return None
