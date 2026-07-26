"""Conversation repository — all raw SQLite access for conversation_meta table."""
import sqlite3
from datetime import datetime, timezone
from app.core.database import get_new_conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert(thread_id: str, title: str | None = None, email: str | None = None) -> None:
    """Insert or update a conversation record."""
    with get_new_conn() as c:
        cursor = c.cursor()
        now = _now()
        cursor.execute(
            "SELECT thread_id, title FROM conversation_meta WHERE thread_id = ?",
            (thread_id,)
        )
        row = cursor.fetchone()

        if row is None:
            final_title = title.strip() if title and title.strip() else "New Conversation"
            cursor.execute(
                "INSERT INTO conversation_meta (thread_id, title, email, created_at, updated_at) VALUES (?,?,?,?,?)",
                (thread_id, final_title, email, now, now)
            )
        else:
            if title and title.strip():
                cursor.execute(
                    "UPDATE conversation_meta SET title=?, updated_at=? WHERE thread_id=?",
                    (title.strip(), now, thread_id)
                )
            else:
                cursor.execute(
                    "UPDATE conversation_meta SET updated_at=? WHERE thread_id=?",
                    (now, thread_id)
                )
        c.commit()


def get_title(thread_id: str) -> str:
    """Return the conversation title or 'New Conversation' if not found."""
    with get_new_conn() as c:
        row = c.execute(
            "SELECT title FROM conversation_meta WHERE thread_id=?", (thread_id,)
        ).fetchone()
    return row["title"] if row else "New Conversation"


def rename(thread_id: str, new_title: str) -> None:
    """Rename a conversation."""
    new_title = new_title.strip()
    if not new_title:
        return
    with get_new_conn() as c:
        c.execute(
            "UPDATE conversation_meta SET title=?, updated_at=? WHERE thread_id=?",
            (new_title, _now(), thread_id)
        )
        c.commit()


def delete(thread_id: str) -> None:
    """Delete conversation metadata AND LangGraph checkpoint rows."""
    with get_new_conn() as c:
        cursor = c.cursor()
        cursor.execute("DELETE FROM conversation_meta WHERE thread_id=?", (thread_id,))
        for table in ("checkpoints", "writes"):
            try:
                cursor.execute(f"DELETE FROM {table} WHERE thread_id=?", (thread_id,))
            except sqlite3.OperationalError:
                pass
        c.commit()


def list_by_user(email: str) -> list[dict]:
    """Return all conversations for a specific user email, newest-first."""
    with get_new_conn() as c:
        rows = c.execute(
            "SELECT thread_id, title, updated_at FROM conversation_meta WHERE email = ? ORDER BY updated_at DESC",
            (email.strip().lower(),)
        ).fetchall()
    return [{"thread_id": r["thread_id"], "title": r["title"], "updated_at": r["updated_at"]} for r in rows]


def get_owner(thread_id: str) -> str | None:
    """Return the owner (email) of the conversation."""
    with get_new_conn() as c:
        row = c.execute(
            "SELECT email FROM conversation_meta WHERE thread_id=?", (thread_id,)
        ).fetchone()
    return row["email"] if row else None
