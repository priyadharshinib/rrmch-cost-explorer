"""Create / list / delete login users in Supabase from your own machine.

Uses the SERVICE ROLE key, so keep it only in a local .env file (git-ignored),
never in the Streamlit app or its secrets.

  python scripts/create_user.py add you@example.com "StrongPass#123"
  python scripts/create_user.py list
  python scripts/create_user.py delete you@example.com
"""
import os
import sys
from pathlib import Path

from supabase import create_client


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def admin_client():
    load_env(Path(__file__).resolve().parent.parent / ".env")
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env (see .env.example).")
    return create_client(url, key)


def main(argv: list[str]) -> None:
    if not argv or argv[0] not in {"add", "list", "delete"}:
        sys.exit(__doc__)
    sb = admin_client()
    cmd = argv[0]
    if cmd == "add":
        if len(argv) != 3:
            sys.exit('Usage: create_user.py add EMAIL "PASSWORD"  (min 6 chars)')
        res = sb.auth.admin.create_user({"email": argv[1], "password": argv[2], "email_confirm": True})
        print(f"Created and confirmed: {res.user.email}")
    elif cmd == "list":
        users = sb.auth.admin.list_users()
        for u in users:
            print(f"{u.email}\tconfirmed={'yes' if u.email_confirmed_at else 'NO'}\tlast_login={u.last_sign_in_at}")
        print(f"{len(users)} user(s)")
    else:
        if len(argv) != 2:
            sys.exit("Usage: create_user.py delete EMAIL")
        match = [u for u in sb.auth.admin.list_users() if u.email == argv[1]]
        if not match:
            sys.exit("No such user.")
        sb.auth.admin.delete_user(match[0].id)
        print(f"Deleted: {argv[1]}")


if __name__ == "__main__":
    main(sys.argv[1:])
