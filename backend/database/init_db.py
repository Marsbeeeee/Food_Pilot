from backend.database.connection import get_db_connection

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        age INTEGER NOT NULL,
        height REAL NOT NULL,
        weight REAL NOT NULL,
        sex TEXT NOT NULL,
        activity_level TEXT NOT NULL,
        goal TEXT NOT NULL,
        kcal_target INTEGER NOT NULL,
        diet_style TEXT NOT NULL,
        allergies TEXT NOT NULL DEFAULT '[]',
        exercise_type TEXT NOT NULL,
        pace TEXT NOT NULL
    );
                   ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
