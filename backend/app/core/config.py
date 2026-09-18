from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "insecure-dev-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str = "postgresql+asyncpg://vapt:vapt_secure_password@localhost:5432/vapt_db"
    DATABASE_URL_SYNC: str = "postgresql://vapt:vapt_secure_password@localhost:5432/vapt_db"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    ALLOWED_ORIGINS: str = "http://localhost:3000"

    NMAP_TIMEOUT: int = 300
    ZAP_TIMEOUT: int = 1800
    TRIVY_TIMEOUT: int = 600
    SEMGREP_TIMEOUT: int = 600

    SCANNER_MEMORY_LIMIT: str = "1g"
    SCANNER_CPU_LIMIT: float = 1.0

    REPORTS_DIR: str = "/app/reports"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
