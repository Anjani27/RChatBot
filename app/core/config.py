"""Core configuration — loads all environment variables and defines global constants."""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = "llama-3.3-70b-versatile"

# Tools
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

# Persistence
SQLITE_DB_PATH: str = "chatbot.db"
CHROMA_DB_PATH: str = "chroma_db"

# File Upload
UPLOAD_DIR: str = "data/uploads"
DATA_DOCS_DIR: str = "data/docs"

# Embeddings
EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
