# 🤖 LangGraph AI Chatbot

A full-stack, production-ready AI chatbot powered by **LangGraph**, **Groq (LLaMA)**, and **ChromaDB RAG**. It features intelligent tool routing, real-time streaming, PDF knowledge base uploads, web search, and weather lookups — all wrapped in a sleek custom HTML/CSS/JS frontend served by a FastAPI backend.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **LangGraph Agent** | State-machine-based conversation graph with memory |
| 🔀 **Smart Tool Router** | LLM automatically routes queries to the right tool |
| 📄 **RAG (PDF Upload)** | Upload PDFs and query them via ChromaDB + HuggingFace Embeddings |
| 🌤️ **Weather Tool** | Live weather data via OpenWeatherMap API |
| 🔍 **Web Search** | Real-time web search powered by Tavily |
| ⚡ **Streaming Responses** | Token-by-token streaming using SSE (Server-Sent Events) |
| 💬 **Multi-Conversation** | Manage multiple independent chat threads |
| 🔐 **Auth System** | User authentication with session management |
| 🐳 **Docker Ready** | Single-command deployment with Docker |

---

## 🏗️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** — High-performance async web framework
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** — Agent orchestration & stateful conversation graph
- **[LangChain](https://www.langchain.com/)** — LLM tooling & integrations
- **[Groq](https://groq.com/)** — Ultra-fast LLaMA inference (LPU)
- **[ChromaDB](https://www.trychroma.com/)** — Local vector store for RAG
- **[HuggingFace Embeddings](https://huggingface.co/)** — Sentence transformers for document embedding
- **SQLite** — Lightweight database for conversations & users

### Frontend
- **Vanilla HTML / CSS / JavaScript** — Zero-framework, lightweight UI
- **SSE (EventSource)** — Real-time token streaming from the backend

### DevOps
- **Docker** — Containerised deployment
- **Uvicorn** — ASGI production server

---

## 📁 Project Structure

```
Chatbot/
├── app/
│   ├── api/
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── chat.py           # Chat & SSE streaming endpoints
│   │   ├── conversations.py  # Conversation management endpoints
│   │   └── uploads.py        # PDF upload endpoints
│   ├── core/
│   │   ├── config.py         # Environment config & constants
│   │   ├── database.py       # SQLite DB init
│   │   └── langgraph_setup.py# LangGraph graph & LLM setup
│   ├── models/               # Pydantic models & state schemas
│   ├── repositories/         # DB access layer
│   ├── services/
│   │   ├── auth_service.py   # Auth business logic
│   │   ├── chat_service.py   # LLM routing & LangGraph node
│   │   ├── conversation_service.py
│   │   ├── rag_service.py    # ChromaDB ingestion & retrieval
│   │   └── tools_service.py  # Weather & web search tools
│   ├── exceptions/           # Custom exception handlers
│   └── main.py               # FastAPI app factory
├── frontend/
│   ├── index.html            # Single-page app shell
│   ├── style.css             # Custom UI styles
│   └── app.js                # Frontend logic & SSE client
├── data/
│   └── docs/                 # Default .txt documents for global RAG
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env                      # Local secrets (not committed)
```

---

## 🔀 How the Router Works

Every user message is classified by the LLM into one of four routes before a response is generated:

```
User Message
     │
     ▼
┌─────────────┐
│  LLM Router │  (Structured Output)
└──────┬──────┘
       │
  ┌────┴────────────────────────┐
  │                             │
  ▼          ▼         ▼        ▼
Weather   Web Search   RAG    General
  │          │          │        │
OpenWeather  Tavily  ChromaDB  Groq LLM
  │          │          │        │
  └──────────┴──────────┴────────┘
                  │
             Groq LLM (Final Answer)
                  │
             SSE Stream → Frontend
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11+
- Docker (optional)

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Create a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
OPENWEATHER_API_KEY=your_openweathermap_key
ALPHAVANTAGE_API_KEY=your_alphavantage_key

# Optional: LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=Chatbot Project
```

### 5. Run the server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **http://localhost:8000**

---

## 🐳 Docker Deployment

### Build and run with Docker Compose
```bash
docker-compose up --build
```

### Or build manually
```bash
docker build -t ai-chatbot .
docker run -p 7860:7860 --env-file .env ai-chatbot
```

---

## ☁️ Deploy on Render (Free)

1. Push your code to **GitHub** (make sure `.env` is in `.gitignore`).
2. Go to [render.com](https://render.com) → **New → Web Service**.
3. Connect your GitHub repository.
4. Configure the service:
   - **Environment**: Docker
   - **Port**: `7860`
5. Under **Environment Variables**, add all keys from your `.env` file.
6. Click **Deploy** — Render will build the Docker image and go live!

---

## 🔑 API Keys

| Service | Purpose | Get Key |
|---|---|---|
| [Groq](https://console.groq.com/) | LLM Inference (LLaMA) | Free |
| [Tavily](https://tavily.com/) | Web Search | Free |
| [OpenWeatherMap](https://openweathermap.org/api) | Weather data | Free |
| [Alpha Vantage](https://www.alphavantage.co/) | Financial data | Free |
| [LangSmith](https://smith.langchain.com/) | LLM Tracing (optional) | Free |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the frontend UI |
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login |
| `GET` | `/conversations` | List all conversations |
| `POST` | `/conversations` | Create a new conversation |
| `DELETE` | `/conversations/{id}` | Delete a conversation |
| `POST` | `/chat` | Send a message (SSE streaming) |
| `POST` | `/uploads/{thread_id}` | Upload a PDF to a conversation |

Full interactive API docs available at **`/docs`** (Swagger UI).

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
