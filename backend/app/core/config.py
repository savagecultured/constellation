from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Constellation Streaming API"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/streaming"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # JWT Settings
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_SUPER_SECRET_KEY_MIN_32_CHARS"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_ROUNDS: int = 12
    
    # Media Server Settings
    JELLYFIN_URL: str = ""
    JELLYFIN_API_KEY: str = ""
    JELLYFIN_DEVICE_ID: str = "constellation-streaming"
    
    NAVIDROME_URL: str = ""
    NAVIDROME_API_KEY: str = ""
    
    MEDIA_SERVER_TIMEOUT: float = 30.0
    MEDIA_SERVER_RETRY_ATTEMPTS: int = 3
    MEDIA_SERVER_RETRY_DELAY: float = 1.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()