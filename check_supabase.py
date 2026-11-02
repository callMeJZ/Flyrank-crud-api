import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from supabase import SupabaseException

from supabase_client import get_supabase_client


def main() -> None:
    try:
        get_supabase_client()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
    except (ValueError, SupabaseException):
        raise SystemExit(
            "Could not initialize Supabase. Check SUPABASE_URL and SUPABASE_KEY."
        ) from None

    print("Supabase client initialized")
    request = Request(
        os.environ["SUPABASE_URL"].strip().rstrip("/") + "/auth/v1/settings",
        headers={"apikey": os.environ["SUPABASE_KEY"].strip()},
    )

    try:
        with urlopen(request, timeout=15) as response:
            print(f"Supabase Auth reachable: {response.status}")
    except HTTPError as exc:
        raise SystemExit(
            f"Supabase Auth returned HTTP {exc.code}. Check your project URL and public key."
        ) from None
    except (URLError, TimeoutError):
        raise SystemExit(
            "Could not reach Supabase Auth. Check your project URL, project status, and internet connection."
        ) from None


if __name__ == "__main__":
    main()
