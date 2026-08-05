import sqlite3

from flask_login import UserMixin

DATABASE = "chat_history.db"


class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, email, password
            FROM users
            WHERE id = ?
        """, (user_id,))

        user = cursor.fetchone()
        conn.close()

        if user:
            return User(user[0], user[1], user[2], user[3])

        return None


class Admin(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def create_user_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()
