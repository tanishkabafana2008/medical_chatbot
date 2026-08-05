import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "chat_history.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def create_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def save_chat(user_message, bot_response):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO chat_history(user_message, bot_response)
        VALUES (?, ?)
    """, (user_message, bot_response))

    connection.commit()
    connection.close()


def get_chat_history():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_message,
               bot_response,
               created_at
        FROM chat_history
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    connection.close()

    return rows


def create_user(username, email, password):
    connection = get_connection()
    cursor = connection.cursor()

    hashed = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users (username, email, password)
        VALUES (?, ?, ?)
    """, (username, email, hashed))

    connection.commit()
    connection.close()


def get_user_by_email(email):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, email, password
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()
    connection.close()

    return user


def create_admin_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_default_admin():
    import os

    conn = get_connection()
    cursor = conn.cursor()

    # Default admin password can be overridden via env var. Change it
    # immediately after first login either way.
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    cursor.execute("""
        INSERT OR IGNORE INTO admins (username, password)
        VALUES (?, ?)
    """, ("admin", generate_password_hash(default_password)))

    conn.commit()
    conn.close()


def get_admin_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, password
        FROM admins
        WHERE username = ?
    """, (username,))

    admin = cursor.fetchone()
    conn.close()

    return admin
