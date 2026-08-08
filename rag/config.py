import os
from dotenv import load_dotenv


load_dotenv()


class Settings :
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROQ_MODEL = "llama-3.3-70b-versatile"

    # --- VECTOR DB (Postgres + pgvector) ---
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/swift"
    )

    # --- EMBEDDINGS (local, multilingual — matches kb_chunks.embedding vector(1024)) ---
    EMBEDDING_MODEL = "BAAI/bge-m3"
    EMBEDDING_FALLBACK_MODEL = "intfloat/multilingual-e5-large"
    EMBEDDING_DIM = 1024


settings = Settings()
