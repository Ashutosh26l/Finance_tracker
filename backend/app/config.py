from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "finance_tracker"
    ML_MODEL_PATH: str = os.path.join(os.path.dirname(__file__), "ml", "models")

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
