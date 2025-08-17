import sqlite3
import logging

log = logging.getLogger("sunera-bot")

class DB:
    """Класс для управления базой данных SQLite."""
    
    def __init__(self, db_name="sunera.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def _get_connection(self):
        """Создает и возвращает соединение с базой данных."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            log.info(f"Connected to database: {self.db_name}")
        return self.conn, self.cursor

    def init_db(self):
        """Инициализирует базу данных, создавая необходимые таблицы."""
        conn, cursor = self._get_connection()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                language_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                language_code TEXT,
                speaker TEXT,
                text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        log.info("Database initialized successfully.")

    def save_user(self, user_id, first_name, username, lang_code):
        """Сохраняет или обновляет информацию о пользователе."""
        conn, cursor = self._get_connection()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, first_name, username, language_code)
            VALUES (?, ?, ?, ?)
        """, (user_id, first_name, username, lang_code))
        conn.commit()
        
    def get_user_lang(self, chat_id):
        """Возвращает язык пользователя по его chat_id."""
        conn, cursor = self._get_connection()
        cursor.execute("SELECT language_code FROM users WHERE id = ?", (chat_id,))
        result = cursor.fetchone()
        return result[0] if result else "en"

    def save_dialog(self, chat_id, lang, speaker, text):
        """Сохраняет реплику в историю диалога."""
        conn, cursor = self._get_connection()
        cursor.execute("""
            INSERT INTO dialogs (chat_id, language_code, speaker, text)
            VALUES (?, ?, ?, ?)
        """, (chat_id, lang, speaker, text))
        conn.commit()
    
    def get_dialog_history(self, chat_id, limit=10):
        """Возвращает историю диалога для LLM."""
        conn, cursor = self._get_connection()
        cursor.execute("""
            SELECT speaker, text FROM dialogs 
            WHERE chat_id = ? ORDER BY timestamp DESC LIMIT ?
        """, (chat_id, limit))
        history = cursor.fetchall()
        return [{"speaker": row[0], "text": row[1]} for row in reversed(history)]
