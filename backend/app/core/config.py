from pydantic_settings import BaseSettings  # type: ignore
from typing import List
import os
import json
from pathlib import Path

# Carregar .env apenas em desenvolvimento local (não no Railway/produção)
# No Railway, as variáveis vêm das Environment Variables configuradas na plataforma
if os.getenv("ENVIRONMENT", "development") == "development" or not os.getenv("RAILWAY_ENVIRONMENT"):
    try:
        from dotenv import load_dotenv  # type: ignore
        
        # Tenta carregar de diferentes locais
        env_paths = [
            Path(__file__).parent.parent.parent / ".env",  # backend/.env
            Path(__file__).parent.parent.parent.parent / ".env",  # raiz do projeto/.env
            Path(".env"),  # diretório atual
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=False)  # override=False: variáveis de ambiente têm prioridade
                break
        else:
            # Se não encontrou, tenta carregar do diretório atual
            load_dotenv(override=False)
    except ImportError:
        # Se python-dotenv não estiver instalado, continua sem .env (normal no Railway)
        pass


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
    
    # SMTP (Gmail/Outlook)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587  # Porta 587 para TLS
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@economizeia.com"
    
    # Brevo (Sendinblue) API - alternativa mais confiável que SMTP
    BREVO_API_KEY: str = ""  # Se configurado, usa Brevo API ao invés de SMTP
    BREVO_FROM: str = ""  # Email de envio (pode ser qualquer email verificado)
    
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
        import re
        logger = logging.getLogger(__name__)
        
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "":
            logger.warning("CORS_ORIGINS vazio, usando padrão")
            return ["http://localhost:3000", "http://localhost:5173"]
        
        logger.info(f"Parsing CORS_ORIGINS: {self.CORS_ORIGINS}")
        
        try:
            # Tentar fazer parse do JSON
            parsed = json.loads(self.CORS_ORIGINS)
            if isinstance(parsed, list):
                # Expandir wildcards do Vercel
                expanded = []
                for origin in parsed:
                    if isinstance(origin, str) and "*" in origin:
                        # Se contém wildcard, adicionar padrões comuns do Vercel
                        if "vercel.app" in origin:
                            expanded.append(origin.replace("*", "economizeia"))
                            # Adicionar padrão para previews do Vercel
                            expanded.append("https://economizeia-*.vercel.app")
                        else:
                            expanded.append(origin)
                    else:
                        expanded.append(origin)
                logger.info(f"CORS origins (JSON list): {expanded}")
                return expanded
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
        # Prioridade: Variáveis de ambiente do sistema > .env
        # No Railway, as variáveis vêm das Environment Variables configuradas
        env_file = ".env"  # Usado apenas se a variável não existir no sistema
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Importante: pydantic-settings já prioriza variáveis de ambiente sobre .env por padrão


# Criar settings após carregar .env
settings = Settings()

# Log das configurações carregadas (sem mostrar valores sensíveis)
import logging
logger = logging.getLogger(__name__)
logger.info("=" * 50)
logger.info("Configurações carregadas:")
logger.info(f"  DATABASE_URL: {'✅ Configurado' if settings.DATABASE_URL and 'localhost' not in settings.DATABASE_URL else '⚠️ Usando padrão local'}")
logger.info(f"  REDIS_URL: {'✅ Configurado' if settings.REDIS_URL and 'localhost' not in settings.REDIS_URL else '⚠️ Usando padrão local'}")
logger.info(f"  BREVO_API_KEY: {'✅ Configurado' if settings.BREVO_API_KEY else '❌ Não configurado (usando SMTP se disponível)'}")
logger.info(f"  SMTP_HOST: {'✅ Configurado' if settings.SMTP_HOST else '❌ Não configurado'}")
logger.info(f"  GEMINI_API_KEY: {'✅ Configurado' if settings.GEMINI_API_KEY else '❌ Não configurado'}")
logger.info(f"  CORS_ORIGINS: {settings.CORS_ORIGINS[:100] if len(settings.CORS_ORIGINS) > 100 else settings.CORS_ORIGINS}")
logger.info(f"  FRONTEND_URL: {settings.FRONTEND_URL}")
logger.info(f"  ENVIRONMENT: {settings.ENVIRONMENT}")
logger.info("=" * 50)

