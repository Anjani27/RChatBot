"""Chat API — SSE streaming endpoint with user isolation."""
import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

from app.schemas.request.chat_request import ChatPayload
from app.services import conversation_service as svc
from app.services.auth_service import get_current_user
from app.repositories import conversation_repository as repo
from app.core.langgraph_setup import chatbot

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat_stream(
    payload: ChatPayload,
    current_user: str = Depends(get_current_user)
):
    thread_id = payload.thread_id
    
    if thread_id:
        # Verify ownership
        owner = repo.get_owner(thread_id)
        if owner and owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation."
            )
    else:
        thread_id = str(uuid.uuid4())

    user_message = payload.message

    # Ensure conversation is created and associated with the current user
    svc.ensure_conversation(thread_id, email=current_user)
    svc.set_smart_title_from_first_message(thread_id, user_message)

    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": {"thread_id": thread_id},
        "run_name": "chat_turn",
    }

    async def event_generator():
        title = svc.get_title(thread_id)
        yield f"event: metadata\ndata: {json.dumps({'thread_id': thread_id, 'title': title})}\n\n"

        loop = asyncio.get_event_loop()

        def get_stream():
            return chatbot.stream(
                {"messages": [HumanMessage(content=user_message)]},
                config=config,
                stream_mode="messages",
            )

        try:
            stream = await loop.run_in_executor(None, get_stream)
            for message_chunk, _ in stream:
                if isinstance(message_chunk, AIMessage) and message_chunk.content:
                    payload_data = json.dumps({"content": message_chunk.content})
                    yield f"event: chunk\ndata: {payload_data}\n\n"
                    await asyncio.sleep(0.01)

            svc.ensure_conversation(thread_id, email=current_user)
            yield "event: end\ndata: done\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
