from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_connection

app = FastAPI()

tasks = [
    {
        "id": 1,
        "title": "Learn FastAPI",
        "done": False
    },
    {
        "id": 2,
        "title": "Build CRUD API",
        "done": False
    },
    {
        "id": 3,
        "title": "Test API with Swagger",
        "done": False
    }
]


@app.get("/")
def root():
    return {
        "name": "TaskAPI",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    conn = get_connection()

    rows = conn.execute(
        "SELECT id, title, done FROM tasks"
    ).fetchall()

    conn.close()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"])
        }
        for row in rows
    ]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()

    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = %s",
        (task_id,)
    ).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }


class TaskCreate(BaseModel):
    title: str


@app.post("/tasks", status_code=201)
def create_task(task_data: TaskCreate):
    if not task_data.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    conn = get_connection()

    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
        (task_data.title, False)
    )

    new_id = cursor.fetchone()["id"]

    conn.commit()
    conn.close()

    return {
        "id": new_id,
        "title": task_data.title,
        "done": False
    }


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate):
    conn = get_connection()

    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = %s",
        (task_id,)
    ).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    title = row["title"]
    done = bool(row["done"])

    if task_data.title is not None:
        if not task_data.title.strip():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Title cannot be empty"
            )

        title = task_data.title

    if task_data.done is not None:
        done = task_data.done

    conn.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (title, done, task_id)
    )

    conn.commit()
    conn.close()

    return {
        "id": task_id,
        "title": title,
        "done": done
    }


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_connection()

    row = conn.execute(
        "SELECT id FROM tasks WHERE id = %s",
        (task_id,)
    ).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    conn.execute(
        "DELETE FROM tasks WHERE id = %s",
        (task_id,)
    )

    conn.commit()
    conn.close()

    return