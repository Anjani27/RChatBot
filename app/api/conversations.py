"""Conversations API — CRUD endpoints for conversation threads with user isolation."""
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from langchain_core.messages import HumanMessage, AIMessage

from app.schemas.request.chat_request import RenamePayload
from app.schemas.response.conversation_response import ConversationOut
from app.services import conversation_service as svc
from app.services.auth_service import get_current_user
from app.repositories import conversation_repository as repo
from app.core.langgraph_setup import chatbot

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _verify_ownership(thread_id: str, email: str) -> None:
    """Helper to ensure a user owns the target thread."""
    owner = repo.get_owner(thread_id)
    if owner and owner != email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation."
        )


@router.get("", response_model=list[ConversationOut])
def list_conversations(current_user: str = Depends(get_current_user)):
    try:
        return svc.list_conversations(current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
def create_conversation(current_user: str = Depends(get_current_user)):
    try:
        thread_id = str(uuid.uuid4())
        svc.ensure_conversation(thread_id, "New Conversation", current_user)
        return {"thread_id": thread_id, "title": "New Conversation"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{thread_id}")
def delete_conversation(thread_id: str, current_user: str = Depends(get_current_user)):
    _verify_ownership(thread_id, current_user)
    try:
        svc.delete_conversation(thread_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thread_id}/rename")
def rename_conversation(thread_id: str, payload: RenamePayload, current_user: str = Depends(get_current_user)):
    _verify_ownership(thread_id, current_user)
    try:
        svc.rename_conversation(thread_id, payload.title)
        return {"status": "success", "title": payload.title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}/messages")
def get_messages(thread_id: str, current_user: str = Depends(get_current_user)):
    _verify_ownership(thread_id, current_user)
    try:
        state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
        messages = []
        if state and state.values:
            for msg in state.values.get("messages", []):
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})
        return {"messages": messages, "title": svc.get_title(thread_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
