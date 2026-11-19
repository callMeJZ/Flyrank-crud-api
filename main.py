import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase_auth.errors import AuthApiError
from database import get_connection
from supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if is_supabase_configured():
        logger.info(
            "Supabase configuration found. Run check_supabase.py to verify connectivity."
        )
    else:
        logger.warning(
            "Supabase setup is pending. Add SUPABASE_URL and SUPABASE_KEY to .env; "
            "the CRUD API is available."
        )
    yield


app = FastAPI(lifespan=lifespan)


class AuthCredentials(BaseModel):
    email: str | None = None
    password: str | None = None


def credentials_error():
    return JSONResponse(
        status_code=400,
        content={"error": "Email and password are required"},
    )


@app.post("/auth/signup", status_code=201)
def signup(credentials: AuthCredentials):
    if (
        credentials.email is None
        or not credentials.email.strip()
        or credentials.password is None
        or not credentials.password.strip()
    ):
        return credentials_error()

    try:
        result = get_supabase_client().auth.sign_up(
            {
                "email": credentials.email.strip(),
                "password": credentials.password,
            }
        )
    except AuthApiError as exc:
        if exc.status >= 500:
            raise HTTPException(
                status_code=502,
                detail="Supabase Auth could not create the account",
            ) from None
        return JSONResponse(
            status_code=400,
            content={"error": exc.message},
        )

    if result.user is None:
        raise HTTPException(
            status_code=502,
            detail="Supabase Auth did not return a user",
        )

    return JSONResponse(
        status_code=201,
        content=jsonable_encoder(result.user),
    )


@app.post("/auth/login")
def login(credentials: AuthCredentials):
    if (
        credentials.email is None
        or not credentials.email.strip()
        or credentials.password is None
        or not credentials.password.strip()
    ):
        return credentials_error()

    try:
        result = get_supabase_client().auth.sign_in_with_password(
            {
                "email": credentials.email.strip(),
                "password": credentials.password,
            }
        )
    except AuthApiError as exc:
        if exc.status in (400, 401):
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid login credentials"},
            )
        raise HTTPException(
            status_code=502,
            detail="Supabase Auth could not complete the login",
        ) from None

    if result.session is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid login credentials"},
        )

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
    }


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


def access_token_error():
    return JSONResponse(
        status_code=401,
        content={"error": "Access token required"},
    )


@app.get("/protected/profile")
def protected_profile(authorization: str | None = Header(default=None)):
    if authorization is None:
        return access_token_error()

    auth_parts = authorization.strip().split()
    if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
        return access_token_error()

    access_token = auth_parts[1]
    try:
        result = get_supabase_client().auth.get_user(access_token)
    except AuthApiError as exc:
        if exc.status in (400, 401, 403) or exc.code in ("bad_jwt", "invalid_jwt"):
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired token"},
            )
        raise HTTPException(
            status_code=502,
            detail="Supabase Auth could not verify the access token",
        ) from None

    if result is None or result.user is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"},
        )

    user = result.user
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }

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
