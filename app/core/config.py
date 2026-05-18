"""全局配置。"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = "development"
    PROJECT_NAME: str = "RAG 知识库问答系统"
    API_V1_STR: str = "/api/v1"
    API_PORT: int = 8000

    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    class Config:
        env_file = ".env"; env_file_encoding = "utf-8"

settings = Settings()
