import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")


def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


conn = get_connection()

conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        done BOOLEAN NOT NULL
    )
""")

cursor = conn.execute("SELECT COUNT(*) FROM tasks")
task_count = cursor.fetchone()["count"]

if task_count == 0:
    with conn.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [
                ("Buy groceries", False),
                ("Study Python", False),
                ("Finish CRUD API", False)
            ]
        )

conn.commit()
conn.close()