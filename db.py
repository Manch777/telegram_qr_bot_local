# db.py
import sqlite3
from datetime import datetime

DB_NAME = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            qr_text TEXT,
            created_at TEXT,
            checked_in INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def save_user(user_id, username, first_name, last_name, qr_text):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users (
            user_id, username, first_name, last_name, qr_text, created_at, checked_in
        )
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT checked_in FROM users WHERE user_id = ?), 0))
    """, (user_id, username, first_name, last_name, qr_text, datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def user_exists(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    rows = c.fetchall()
    conn.close()
    return rows

def mark_checked_in(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET checked_in=1 WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()

def is_checked_in(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT checked_in FROM users WHERE user_id=?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] == 1 if result else False
