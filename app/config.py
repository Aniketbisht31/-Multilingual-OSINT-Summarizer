from decouple import config
from pydantic import AnyHttpUrl
from typing import Optional

class Settings:
    ANTHROPIC_API_KEY: str = config("ANTHROPIC_API_KEY")
    DATABASE_URL: str = config("DATABASE_URL")
    REDIS_URL: str = config("REDIS_URL")
    INDICTRANS2_ENDPOINT: str = config("INDICTRANS2_ENDPOINT", default="https://api-inference.huggingface.co/models/ai4bharat/indictrans2-indic-en-1B")
    HUGGINGFACE_API_KEY: str = config("HUGGINGFACE_API_KEY", default="")
    SARVAM_API_KEY: str = config("SARVAM_API_KEY")
    JWT_SECRET: str = config("JWT_SECRET")
    JWT_ALGORITHM: str = config("JWT_ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=1440, cast=int)
    DATA_CLASSIFICATION: str = config("DATA_CLASSIFICATION", default="RESTRICTED")

settings = Settings()
