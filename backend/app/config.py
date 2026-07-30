from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolves to the backend folder regardless of where the server is started.
BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Owlivia Backend"
    environment: str = "local"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Supabase settings
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None

    # LanceDB settings
    lancedb_path: Path = BACKEND_DIR / "data" / "fau_eecs_lancedb"
    lancedb_table_name: str = "fau_eecs_resources"

    # Must match the model used to build the existing database vectors.
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Hybrid RAG retrieval settings
    rag_top_k: int = 10
    rag_retrieval_pool: int = 75
    rag_rrf_k: int = 300
    rag_bm25_weight: float = 0.4
    rag_dense_weight: float = 3.0
    rag_max_context_chars: int = 4200
    rag_max_snippet_chars: int = 520
    rag_max_input_tokens: int = 2048
    rag_max_new_tokens: int = 220

    # Runtime modes: local | extractive | gemini
    rag_generation_mode: str = "gemini"
    rag_dense_enabled: bool = True

    # Answer-generation model (used when rag_generation_mode=local)
    rag_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"

    # Gemini settings (used when rag_generation_mode=gemini)
    gemini_api_key: str | None = None
    gemini_model_name: str = "gemini-3.1-flash-lite"

    # Existing placeholder settings retained for compatibility
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "owlivia-advising"

    llm_provider: str | None = None
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_gemini_api_key(self) -> str | None:
        """Return the Gemini API key from dedicated or legacy settings."""

        return self.gemini_api_key or self.llm_api_key

    @property
    def cors_origins(self) -> list[str]:
        """Return normalized frontend origins for the CORS middleware."""
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()

