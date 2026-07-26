"""Conversation service — higher-level helpers wrapping the repository."""
from app.repositories import conversation_repository as repo
from app.core.langgraph_setup import llm


def ensure_conversation(thread_id: str, title: str | None = None, email: str | None = None) -> None:
    """Upsert conversation metadata; create with title if new."""
    repo.upsert(thread_id, title, email)


def set_smart_title_from_first_message(thread_id: str, first_message: str) -> None:
    """
    If the conversation is new or still named 'New Conversation',
    generate a concise LLM-based title from the first user message.
    """
    current_title = repo.get_title(thread_id)
    if current_title not in ("New Conversation", ""):
        # Already has a meaningful title — just touch updated_at
        repo.upsert(thread_id)
        return

    title = _generate_smart_title(first_message)
    repo.upsert(thread_id, title)


def _generate_smart_title(message: str) -> str:
    try:
        result = llm.invoke(
            "Generate a concise 3-6 word title for a conversation that starts with "
            "this message. Return ONLY the title text, no quotes, nothing else.\n\n"
            + message
        )
        title = result.content.strip().strip('"').strip("'")
        if title and 2 <= len(title) <= 60:
            return title
    except Exception:
        pass
    suggested = message.strip().replace("\n", " ")
    return suggested[:40].rstrip() + "..." if len(suggested) > 40 else suggested


def rename_conversation(thread_id: str, new_title: str) -> None:
    repo.rename(thread_id, new_title)


def delete_conversation(thread_id: str) -> None:
    repo.delete(thread_id)


def get_title(thread_id: str) -> str:
    return repo.get_title(thread_id)


def list_conversations(email: str) -> list[dict]:
    return repo.list_by_user(email)
