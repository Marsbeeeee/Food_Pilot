import sqlite3

db_path = 'backend/database/foodpilot.db'

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

