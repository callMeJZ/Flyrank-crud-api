import os

from dotenv import load_dotenv
from supabase import Client, create_client
from supabase.client import ClientOptions

load_dotenv()


def is_supabase_configured() -> bool:
    return all(
        os.getenv(name, "").strip()
        for name in ("SUPABASE_URL", "SUPABASE_KEY")
    )


def get_supabase_client() -> Client:
    """Create a separate Auth client for each caller, without shared sessions."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    if not url or not key:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in .env."
        )

    return create_client(
        url,
        key,
        options=ClientOptions(
            persist_session=False,
            auto_refresh_token=False,
        ),
    )
