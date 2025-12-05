from pydantic_settings import BaseSettings
from typing import List
import os
import json


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://economizeia:economizeia_dev@localhost:5432/economizeia_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6380/0"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"  # Modelo Qwen 2.5 7B - melhor qualidade e performance
    
    # Google Gemini (opcional, mais rápido)
    GEMINI_API_KEY: str = ""
    USE_GEMINI: bool = False  # Se True, usa Gemini ao invés de Ollama
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Modelo rápido do Gemini (mais rápido e disponível)
    
    # MinIO / S3
    MINIO_ENABLED: bool = False  # Desabilitado por padrão (não quebra se MinIO não estiver disponível)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "economizeia-documents"
    MINIO_USE_SSL: bool = False
    
    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@economizeia.com"
    
    # SMS (Twilio)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # FCM
    FCM_SERVER_KEY: str = ""
    FCM_PROJECT_ID: str = ""
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # LGPD
    DATA_RETENTION_DAYS: int = 365
    MASK_SENSITIVE_DATA: bool = True
    
    # CORS - aceita JSON ou string separada por vírgula
    CORS_ORIGINS: str = '["http://localhost:3000", "http://localhost:5173"]'
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS from JSON string or comma-separated string."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "":
            logger.warning("CORS_ORIGINS vazio, usando padrão")
            return ["http://localhost:3000", "http://localhost:5173"]
        
        logger.info(f"Parsing CORS_ORIGINS: {self.CORS_ORIGINS}")
        
        try:
            # Tentar fazer parse do JSON
            parsed = json.loads(self.CORS_ORIGINS)
            if isinstance(parsed, list):
                logger.info(f"CORS origins (JSON list): {parsed}")
                return parsed
            elif isinstance(parsed, str):
                # Se for string única, retornar como lista
                logger.info(f"CORS origins (JSON string): [{parsed}]")
                return [parsed]
        except (json.JSONDecodeError, ValueError) as e:
            logger.info(f"JSON parse falhou: {e}, tentando split por vírgula")
            # Se não for JSON, tentar split por vírgula
            try:
                origins = [origin.strip().strip('"').strip("'") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
                if origins:
                    logger.info(f"CORS origins (comma-separated): {origins}")
                    return origins
                else:
                    logger.warning("Nenhum origin encontrado após split, usando padrão")
                    return ["http://localhost:3000", "http://localhost:5173"]
            except Exception as e2:
                logger.error(f"Erro ao fazer split: {e2}, usando padrão")
                return ["http://localhost:3000", "http://localhost:5173"]
        
        logger.warning("Retornando padrão")
        return ["http://localhost:3000", "http://localhost:5173"]
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

