from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/deal_room_ai"

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_COOKIE_NAME: str = "deal_room_ai_session"
    JWT_EXPIRE_DAYS: int = 7
    # Set true in production (HTTPS). Keep false locally so cookies are sent
    # over plain HTTP during dev. Tests rely on the default-false behaviour.
    JWT_COOKIE_SECURE: bool = False

    FRONTEND_ORIGIN: str = "http://localhost:3000"

    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    EMBEDDING_MODEL: str = "text-embedding-3-small"

    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "deal_room_ai_chunks"

    # OpenAI (read at startup; never logged)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-mini"
    OPENAI_MAX_OUTPUT_TOKENS: int = 400

    # MLflow (off by default; remote logging only when URI is set)
    MLFLOW_TRACKING_URI: str = ""
    MLFLOW_EXPERIMENT_NAME: str = "team-project"

    # Offline / no-cost master switches.
    # Default mode is offline/local/free. Cloud or paid-API behaviour must be
    # an explicit opt-in via these flags AND the matching credentials.
    ENABLE_LLM_CALLS: bool = False
    ENABLE_MLFLOW: bool = False
    ENABLE_EXTERNAL_INGESTION: bool = False

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")


settings = Settings()
