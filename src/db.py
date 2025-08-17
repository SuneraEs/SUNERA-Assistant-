import sqlite3
import datetime
import logging
from typing import List, Dict, Any

log = logging.getLogger("db")
DB_FILE = "bot.sqlite"

def init_db():
    """Инициализирует базу данных и создает необходимые таблицы."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Таблица для лидов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                username TEXT,
                chat_id INTEGER,
                lang TEXT,
                name TEXT,
                phone TEXT,
                city TEXT,
                note TEXT
            )
        """)
        
        # Таблица для истории диалогов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                chat_id INTEGER,
                lang TEXT,
                role TEXT,
                content TEXT
            )
        """)

        # Таблица для калькуляторов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                username TEXT,
                chat_id INTEGER,
                lang TEXT,
                calc_type TEXT,
                input_data TEXT,
                result_data TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        log.info("Database initialized successfully.")
    except Exception as e:
        log.error("Database initialization failed: %s", e)

def save_lead(lead_data: Dict[str, Any]):
    """Сохраняет данные лида в таблицу leads."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leads (timestamp, username, chat_id, lang, name, phone, city, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.datetime.utcnow().isoformat(),
            lead_data.get("username"),
            lead_data.get("chat_id"),
            lead_data.get("lang"),
            lead_data.get("name"),
            lead_data.get("phone"),
            lead_data.get("city"),
            lead_data.get("note")
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log.error("Failed to save lead: %s", e)

def save_dialog(chat_id: int, lang: str, role: str, content: str):
    """Сохраняет сообщение диалога в таблицу dialogs."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dialogs (timestamp, chat_id, lang, role, content)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.datetime.utcnow().isoformat(),
            chat_id,
            lang,
            role,
            content
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log.error("Failed to save dialog: %s", e)

def save_calculation(chat_id: int, lang: str, username: str, calc_type: str, input_data: str, result_data: str):
    """Сохраняет данные калькулятора в таблицу calculations."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO calculations (timestamp, username, chat_id, lang, calc_type, input_data, result_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.datetime.utcnow().isoformat(),
            username,
            chat_id,
            lang,
            calc_type,
            input_data,
            result_data
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log.error("Failed to save calculation: %s", e)
