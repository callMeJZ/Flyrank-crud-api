# TaskAPI

TaskAPI is a FastAPI service that combines PostgreSQL-backed task CRUD with Supabase Auth. It provides signup and login, verifies Supabase access tokens, and protects user-only routes with a reusable FastAPI dependency.

## Features

- Supabase email signup and password login
- Supabase JWT verification for protected routes
- Protected profile, dashboard, and logout routes
- Public information route
- PostgreSQL task CRUD with Docker Compose
- Interactive API documentation at `/docs`

## Requirements

- Docker Desktop with the Linux engine enabled, or Python 3.10+ and PostgreSQL
- A Supabase project for authentication

## Configure the environment

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Set `SUPABASE_URL` and `SUPABASE_KEY` in `.env` using the project URL and its public anon key or publishable key. Do not use a service-role or secret key. Keep `.env` private; it is ignored by Git and excluded from the Docker build context.

For this practice assignment, disable email confirmation in Supabase under **Authentication > Sign In / Providers > Email** so new accounts can log in immediately. Enable it for production.

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL. |
| `SUPABASE_KEY` | Public anon or publishable key for Auth requests. |
| `POSTGRES_PASSWORD` | Local PostgreSQL password used by Docker Compose. |
| `POSTGRES_DB` | PostgreSQL database name. |
| `DATABASE_URL` | Database URL for running Uvicorn on the host (`localhost`). |
| `DATABASE_URL_DOCKER` | Database URL used by the API container (`db`). |

## Run the API

From the project directory, start the API and PostgreSQL with one command:

```powershell
docker compose up --build
```

The API is at <http://localhost:8000>, Swagger UI is at <http://localhost:8000/docs>, and PostgreSQL is published on port `5432`. Docker Desktop must be running first.

To run Uvicorn on Windows while PostgreSQL runs in Docker, start only the database and then the API:

```powershell
docker compose up -d db
uvicorn main:app --reload --port 8000
```

Verify Supabase connectivity from the host with:

```powershell
python check_supabase.py
```

The successful check prints `Supabase client initialized` and `Supabase Auth reachable: 200`. In the Compose setup, run it with `docker compose exec api python check_supabase.py`.

## Authentication API

| Method | Endpoint | Auth required | Success | Description |
| --- | --- | --- | --- | --- |
| `POST` | `/auth/signup` | No | `201 Created` | Creates a Supabase user. Email and password are required (`400` otherwise). |
| `POST` | `/auth/login` | No | `200 OK` | Authenticates a user and returns access and refresh tokens. Invalid credentials return `401`. |
| `POST` | `/auth/logout` | Bearer token | `204 No Content` | Verifies the caller and signs out the current Supabase session. |
| `GET` | `/protected/profile` | Bearer token | `200 OK` | Returns the verified user's ID, email, and account creation date. |
| `GET` | `/protected/dashboard` | Bearer token | `200 OK` | Example second route protected by the same auth dependency. |
| `GET` | `/public/info` | No | `200 OK` | Returns public information. |

Protected routes return `401 Unauthorized` for a missing, malformed, invalid, or expired access token. In Swagger, click **Authorize** and paste the access token returned by `/auth/login`; Swagger adds the `Bearer` prefix to requests.

### Example request bodies

Signup and login accept:

```json
{
  "email": "you@example.com",
  "password": "your-test-password"
}
```

Use a test account and do not put real passwords or access tokens in the README, source code, or Git history.

After `/auth/login` returns an `access_token`, send it to a protected endpoint:

```powershell
curl.exe -i http://localhost:8000/protected/profile `
  -H "Authorization: Bearer <access-token>"
```

The profile response contains the verified user's `id`, `email`, and `created_at` fields. A missing or invalid token returns `401`.

## Task API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | API information. |
| `GET` | `/health` | Health check. |
| `GET` | `/tasks` | List tasks. |
| `GET` | `/tasks/{task_id}` | Get one task. |
| `POST` | `/tasks` | Create a task. |
| `PUT` | `/tasks/{task_id}` | Update a task. |
| `DELETE` | `/tasks/{task_id}` | Delete a task. |

Tasks are stored in PostgreSQL. The app creates the `tasks` table on startup and seeds three example tasks when the table is empty. Docker Compose persists database files in the `taskdata` volume.

## Swagger screenshot

The auth-enabled Swagger screenshot is still needed for this section. Save the screenshot from `/docs` as `swagger-auth.png` in the repository root, then replace this note with:

```markdown
![Swagger UI showing bearer authorization on protected routes](swagger-auth.png)
```

## Project files

- `main.py` — FastAPI routes, Supabase Auth handlers, and the reusable bearer-token dependency.
- `supabase_client.py` — Supabase client factory with per-request sessions disabled.
- `check_supabase.py` — Supabase Auth connectivity check.
- `database.py` — PostgreSQL connection, table creation, and seed data.
- `docker-compose.yml` — API and PostgreSQL services.
- `.env.example` — safe template for local configuration.
