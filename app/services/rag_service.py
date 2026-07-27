"""RAG service — Chroma DB vector store, PDF ingestion, and context retrieval."""
import os
import shutil
from typing import List

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastembed import TextEmbedding

from app.core.config import (
    CHROMA_DB_PATH,
    DATA_DOCS_DIR,
    UPLOAD_DIR,
)


class _FastEmbedWrapper(Embeddings):
    """Lightweight ONNX-based embedding wrapper using fastembed directly.
    
    Uses fastembed's TextEmbedding which runs via ONNX Runtime — no PyTorch
    required. Explicitly converts numpy arrays to Python float lists so
    ChromaDB's upsert receives the correct type.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self._model = TextEmbedding(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [e.tolist() for e in self._model.embed(texts)]

    def embed_query(self, text: str) -> List[float]:
        return next(self._model.embed([text])).tolist()


# ── Embeddings (ONNX-based, memory-efficient — no PyTorch) ────────────────
_embedding_model = _FastEmbedWrapper()

# ── Text splitter ─────────────────────────────────────────────────────────
_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)

# ── Chroma collection name ────────────────────────────────────────────────
COLLECTION_NAME = "chatbot_docs"


def _get_vector_store() -> Chroma:
    """Return the persistent Chroma vector store instance."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_embedding_model,
        persist_directory=CHROMA_DB_PATH,
    )


def _load_and_index_default_docs() -> None:
    """Index default .txt documents from data/docs/ with thread_id='global' if not done yet."""
    if not os.path.isdir(DATA_DOCS_DIR):
        return

    db = _get_vector_store()
    # Check if global docs already indexed
    results = db.get(where={"thread_id": "global"}, limit=1)
    if results and results.get("ids"):
        return  # Already indexed

    loader = DirectoryLoader(
        DATA_DOCS_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    if not documents:
        return

    chunks = _splitter.split_documents(documents)
    for chunk in chunks:
        chunk.metadata["thread_id"] = "global"

    db.add_documents(chunks)


def retrieve_context(query: str, thread_id: str, k: int = 4) -> str:
    """
    Retrieve relevant context from Chroma DB.
    First searches thread-specific documents, then global docs.
    Merges and deduplicates results.
    """
    db = _get_vector_store()
    seen_contents: set[str] = set()
    all_docs = []

    # Thread-specific search
    if thread_id and thread_id != "global":
        try:
            thread_docs = db.similarity_search(query, k=k, filter={"thread_id": thread_id})
            for doc in thread_docs:
                if doc.page_content not in seen_contents:
                    seen_contents.add(doc.page_content)
                    all_docs.append(doc)
        except Exception:
            pass

    # Global docs search
    try:
        global_docs = db.similarity_search(query, k=k, filter={"thread_id": "global"})
        for doc in global_docs:
            if doc.page_content not in seen_contents:
                seen_contents.add(doc.page_content)
                all_docs.append(doc)
    except Exception:
        pass

    if not all_docs:
        return "No relevant context found in documents."

    return "\n\n".join(doc.page_content for doc in all_docs[:k])


def index_uploaded_pdf(file_path: str, thread_id: str) -> int:
    """
    Parse a PDF file, split into chunks, tag with thread_id, and insert into Chroma.
    Returns the number of chunks indexed.
    """
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    if not documents:
        return 0

    chunks = _splitter.split_documents(documents)
    for chunk in chunks:
        chunk.metadata["thread_id"] = thread_id

    db = _get_vector_store()
    db.add_documents(chunks)
    return len(chunks)


# Initialise default docs at import time
_load_and_index_default_docs()
