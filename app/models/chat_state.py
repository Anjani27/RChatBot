"""Domain models — LangGraph state definition and tool routing schema."""
from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class ChatState(TypedDict):
    """LangGraph conversation state."""
    messages: Annotated[list[BaseMessage], add_messages]
    tool_used: str


class ToolRoute(BaseModel):
    """Pydantic schema for the LLM router decision."""
    tool: Literal["weather", "web_search", "rag", "general"] = Field(
        description="Best tool to answer the user query"
    )
    query: str = Field(description="Cleaned user query")
    location: str | None = Field(default=None, description="City/location if needed")
