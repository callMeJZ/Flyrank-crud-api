import sqlite3

DATABASE = "tasks.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_connection()

conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        done BOOLEAN NOT NULL
    )
""")

cursor = conn.execute("SELECT COUNT(*) FROM tasks")
task_count = cursor.fetchone()[0]

if task_count == 0:
    conn.executemany(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        [
            ("Buy groceries", False),
            ("Study Python", False),
            ("Finish CRUD API", False)
        ]
    )

conn.commit()
conn.close()