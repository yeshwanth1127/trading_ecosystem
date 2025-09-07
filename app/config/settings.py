from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:6ded34bad0f447a4a071ce794a4a8f63@localhost:5432/trading_ecosystem")
    database_url_sync: str = os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:6ded34bad0f447a4a071ce794a4a8f63@localhost:5432/trading_ecosystem")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-make-it-long-and-random")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Application
    app_name: str = os.getenv("APP_NAME", "Trading Ecosystem API")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    # Comma-separated list of allowed origins, e.g. "http://localhost:3000,http://localhost:5173"
    cors_origins_raw: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:53620,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:53620",
    )
    # Regex to allow all localhost ports by default
    cors_origin_regex_raw: str = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"^https?://(localhost|127\.0\.0\.1)(:\\d+)?$",
    )
    
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str:
        return self.cors_origin_regex_raw
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # External API Keys
    binance_api_key: Optional[str] = os.getenv("BINANCE_API_KEY")
    binance_secret_key: Optional[str] = os.getenv("BINANCE_SECRET_KEY")
    alpha_vantage_api_key: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    coingecko_api_key: Optional[str] = os.getenv("COINGECKO_API_KEY")
    
    # WebSocket Configuration
    websocket_host: str = os.getenv("WEBSOCKET_HOST", "localhost")
    websocket_port: int = int(os.getenv("WEBSOCKET_PORT", "8000"))
    
    # Database Pool Configuration
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    db_pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    db_pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    def validate_configuration(self):
        """Validate critical configuration settings"""
        errors = []
        
        # Check for default/weak secrets in production
        if self.environment == "production":
            if self.secret_key == "your-secret-key-here-make-it-long-and-random":
                errors.append("SECRET_KEY must be set to a secure value in production")
            if any(x in (self.database_url or "") for x in ["postgres:postgres@localhost", "@localhost:"]):
                errors.append("DATABASE_URL should be set securely and not use default credentials or localhost in production")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Validate configuration on startup
try:
    settings.validate_configuration()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise
