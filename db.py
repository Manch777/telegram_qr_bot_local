import sqlite3

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            checked_in INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def save_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def check_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "checked_in": row[2]
        }
    else:
        return None

def user_exists(user_id):
    return check_user(user_id) is not None

def is_checked_in(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT checked_in FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] == 1 if result else False

def mark_checked_in(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET checked_in=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def get_report():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE checked_in = 1")
    checked_in = c.fetchone()[0]
    conn.close()
    return total, checked_in
