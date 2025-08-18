import os
import logging
from typing import Dict, Any, List
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from huggingface_hub import InferenceClient

from db import DB
from utils import T
from config import (
    get_gsheets_credentials_dict, SPREADSHEET_ID, GSHEET_NAME,
    HUGGING_FACE_TOKEN, LLM_MODEL,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, LEADS_EMAILS,
    COMPANY_NAME, COMPANY_PHONE, WEBSITE_URL, WHATSAPP_NUMBER, ADMIN_CHAT_ID
)

log = logging.getLogger("services")

class Services:
    """Класс для хранения всех инициализированных сервисов."""
    def __init__(self):
        self.db = None
        self.t = None
        self.llm_client = None
        self.sheets_client = None
        
        # Переносим константы в класс для удобства доступа
        self.company_name = COMPANY_NAME
        self.company_phone = COMPANY_PHONE
        self.website_url = WEBSITE_URL
        self.whatsapp_number = WHATSAPP_NUMBER
        self.admin_chat_id = ADMIN_CHAT_ID
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_pass = SMTP_PASS
        self.leads_emails = LEADS_EMAILS

    def sheet_append(self, row: List[str]):
        """Добавляет строку в лист Google Sheets."""
        try:
            if self.sheets_client:
                self.sheets_client.append_row(row)
        except Exception as e:
            log.error("Append to sheet failed: %s", e)

    def send_email(self, subject: str, body: str):
        """Отправляет email-уведомление."""
        if not (self.smtp_host and self.smtp_user and self.smtp_pass and self.leads_emails):
            log.warning("Email disabled or not configured.")
            return
        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = ", ".join(self.leads_emails)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as s:
                s.starttls()
                s.login(self.smtp_user, self.smtp_pass)
                s.sendmail(self.smtp_user, self.leads_emails, msg.as_string())
            log.info("Email sent successfully.")
        except Exception as e:
            log.error("Email send error: %s", e)

services = Services()

async def init_services():
    """Инициализирует все необходимые сервисы."""
    log.info("Initializing services...")

    # Инициализация DB
    services.db = DB()
    services.db.init_db()

    # Инициализация переводов и утилит
    services.t = T()

    # Инициализация LLM
    if HUGGING_FACE_TOKEN:
        try:
            services.llm_client = InferenceClient(model=LLM_MODEL, token=HUGGING_FACE_TOKEN)
            # Временно заглушим RAG-функционал, чтобы бот заработал
            def generate_response(dialog_history, prompt):
                return services.llm_client.text_generation(prompt=prompt, max_new_tokens=250)
            services.llm_client.generate_response = generate_response
            log.info("Hugging Face client initialized.")
        except Exception as e:
            log.error(f"Failed to initialize Hugging Face client: {e}")
            services.llm_client = None
    else:
        log.warning("HUGGING_FACE_TOKEN not set. AI functionality disabled.")

    # Инициализация Google Sheets
    creds_dict = get_gsheets_credentials_dict()
    if creds_dict and SPREADSHEET_ID:
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)
            sh = client.open_by_key(SPREADSHEET_ID)
            try:
                services.sheets_client = sh.worksheet(GSHEET_NAME)
            except gspread.WorksheetNotFound:
                services.sheets_client = sh.add_worksheet(title=GSHEET_NAME, rows=2000, cols=12)
            if not services.sheets_client.row_values(1):
                services.sheets_client.append_row(["TimestampUTC", "Username", "ChatID", "Lang", "Type", "Data"])
            log.info("Google Sheets client initialized.")
        except Exception as e:
            log.error("Failed to initialize Google Sheets client: %s", e)
            services.sheets_client = None
    else:
        log.warning("Google Sheets not configured.")

def get_services():
    return services
