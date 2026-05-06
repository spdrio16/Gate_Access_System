import sqlite3
import bcrypt

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

users = [
    ("admin", bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()), "admin"),
    ("guard", bcrypt.hashpw("guard123".encode(), bcrypt.gensalt()), "security")
]

for user in users:
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        user
    )

conn.commit()
conn.close()

print("Database initialized successfully!")