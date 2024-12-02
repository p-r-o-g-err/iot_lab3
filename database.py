import sqlite3
from config import *
from utils import hash_password

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Создаем таблицу пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    
    # Таблица настроек полива
    c.execute('''CREATE TABLE IF NOT EXISTS moisture_settings 
                 (id INTEGER PRIMARY KEY, 
                  min_moisture REAL, 
                  max_moisture REAL)''')
    
    # Таблица истории измерений влажности
    c.execute('''CREATE TABLE IF NOT EXISTS moisture_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        moisture_level REAL,
        pump_status TEXT
    )''')
    
    # Очищаем таблицу истории
    c.execute("DELETE FROM moisture_history")

    # Начальные настройки полива
    c.execute("INSERT OR IGNORE INTO moisture_settings (min_moisture, max_moisture) VALUES (?, ?)",
             (MIN_MOISTURE, MAX_MOISTURE))

    # Добавляем тестового пользователя (admin/admin)
    hashed_pwd = hash_password("admin")
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
             ("admin", hashed_pwd))
    
    conn.commit()
    conn.close()

def save_moisture_data(timestamp, moisture_level):
    """Сохранение данных о влажности"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''INSERT INTO moisture_history 
                 (timestamp, moisture_level) 
                 VALUES (?, ?)''', 
              (timestamp, moisture_level))
    
    conn.commit()
    conn.close()

def get_moisture_history():
    """Получение истории изменений влажности"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Получаем последние 30 записей
    c.execute('''SELECT timestamp, moisture_level
                 FROM moisture_history 
                 ORDER BY timestamp DESC 
                 LIMIT 30''')
    
    history = [
        {
            'timestamp': row[0], 
            'moisture_level': row[1]
        } for row in c.fetchall()
    ]
    
    conn.close()
    return list(reversed(history))

def get_moisture_settings():
    """Получение настроек влажности"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT min_moisture, max_moisture FROM moisture_settings WHERE id = 1")
    settings = c.fetchone()
    conn.close()
    return settings if settings else (MIN_MOISTURE, MAX_MOISTURE)