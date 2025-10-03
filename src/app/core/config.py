import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://svc:secret@localhost:5432/summarizer")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API = "http://ollama:11434/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "Gemma3:1B")
MAX_SUMMARY_CHARS = 1500
