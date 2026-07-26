"""User repository — raw SQLite database operations for users and sessions."""
from datetime import datetime, timezone
from app.core.database import get_new_conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_user(email: str, password_hash: str) -> None:
    """Create a new user."""
    with get_new_conn() as c:
        cursor = c.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email.strip().lower(), password_hash, _now())
        )
        c.commit()


def get_user(email: str) -> dict | None:
    """Retrieve user details by email."""
    with get_new_conn() as c:
        row = c.execute(
            "SELECT email, password_hash, created_at FROM users WHERE email = ?",
            (email.strip().lower(),)
        )
        row = row.fetchone()
    if row:
        return {
            "email": row["email"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"],
        }
    return None


def create_session(session_id: str, email: str) -> None:
    """Create and persist a new session ID for a user email."""
    with get_new_conn() as c:
        cursor = c.cursor()
        cursor.execute(
            "INSERT INTO sessions (session_id, email, created_at) VALUES (?, ?, ?)",
            (session_id, email.strip().lower(), _now())
        )
        c.commit()


def get_session_user(session_id: str) -> str | None:
    """Retrieve user email associated with active session ID."""
    with get_new_conn() as c:
        row = c.execute(
            "SELECT email FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = row.fetchone()
    return row["email"] if row else None


def delete_session(session_id: str) -> None:
    """Delete a session (logout)."""
    with get_new_conn() as c:
        cursor = c.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        c.commit()
