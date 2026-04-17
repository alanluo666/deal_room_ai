from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/deal_room_ai"

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_COOKIE_NAME: str = "deal_room_ai_session"
    JWT_EXPIRE_DAYS: int = 7

    FRONTEND_ORIGIN: str = "http://localhost:3000"

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")


settings = Settings()
