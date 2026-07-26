"""LangGraph graph compilation — exports the compiled chatbot graph."""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_groq import ChatGroq

from app.core.config import GROQ_MODEL
from app.core.database import conn
from app.models.chat_state import ChatState


llm = ChatGroq(model=GROQ_MODEL)

checkpointer = SqliteSaver(conn=conn)


def _build_graph() -> StateGraph:
    # Import here to avoid circular imports
    from app.services.chat_service import chat_node

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_edge(START, "chat_node")
    graph.add_edge("chat_node", END)
    return graph


# Compiled graph — imported everywhere that needs to invoke the chatbot
chatbot = _build_graph().compile(checkpointer=checkpointer)
