# utils/sheets.py
import logging
import time
import gspread
from google.oauth2.service_account import Credentials
from typing import List
from config import get_gsheets_credentials_dict, SPREADSHEET_ID, GSHEET_NAME

log = logging.getLogger("sheets")

class SheetClient:
    def __init__(self):
        self.ws = None

    def init(self):
        creds_dict = get_gsheets_credentials_dict()
        if not (creds_dict and SPREADSHEET_ID):
            log.warning("Google Sheets not configured.")
            return False
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)
            sh = client.open_by_key(SPREADSHEET_ID)
            try:
                self.ws = sh.worksheet(GSHEET_NAME)
            except gspread.WorksheetNotFound:
                self.ws = sh.add_worksheet(title=GSHEET_NAME, rows=2000, cols=12)
            if not self.ws.row_values(1):
                self.ws.append_row(["TimestampUTC","Username","ChatID","Lang","Type","Name","Phone","City","Note"])
            log.info("Google Sheets initialized.")
            return True
        except Exception as e:
            log.error("Sheets init error: %s", e)
            self.ws = None
            return False

    def append_lead(self, username: str, chat_id: int, lang: str, name: str, phone: str, city: str, note: str):
        if not self.ws:
            return False
        try:
            ts = int(time.time())
            self.ws.append_row([str(ts), username or "", str(chat_id), lang, "lead", name, phone, city, note])
            return True
        except Exception as e:
            log.error("Append lead error: %s", e)
            return False

sheets = SheetClient()
