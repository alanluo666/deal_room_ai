from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/deal_room_ai"

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_COOKIE_NAME: str = "deal_room_ai_session"
    JWT_EXPIRE_DAYS: int = 7

    FRONTEND_ORIGIN: str = "http://localhost:3000"

    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    EMBEDDING_MODEL: str = "text-embedding-3-small"

    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "deal_room_ai_chunks"

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")


settings = Settings()
