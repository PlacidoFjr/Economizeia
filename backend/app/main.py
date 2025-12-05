from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.api.v1 import auth, bills, payments, notifications, qa, chatbot, savings_goals, investments
from app.db.database import engine, Base

# Importar modelos para garantir que sejam registrados no Base.metadata
from app.db.models import SavingsGoal, Investment, User  # noqa: F401

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Executar migrations necessárias
def run_migrations():
    """Executa migrations SQL necessárias."""
    from sqlalchemy import text
    from app.db.database import engine
    
    try:
        with engine.connect() as conn:
            # Verificar se a coluna amount ainda tem NOT NULL
            result = conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'bills' AND column_name = 'amount'
            """))
            row = result.fetchone()
            
            if row and row[0] == 'NO':
                logger.info("Executando migration: tornar amount e due_date nullable")
                conn.execute(text("ALTER TABLE bills ALTER COLUMN amount DROP NOT NULL"))
                conn.execute(text("ALTER TABLE bills ALTER COLUMN due_date DROP NOT NULL"))
                conn.commit()
                logger.info("Migration executada com sucesso")
            else:
                logger.info("Migration já aplicada ou coluna já é nullable")
    except Exception as e:
        logger.warning(f"Erro ao executar migration (pode ser que já esteja aplicada): {e}")

# Executar migrations na inicialização
run_migrations()

app = FastAPI(
    title="EconomizeIA API",
    description="Sistema de organização financeira pessoal",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
cors_origins = settings.get_cors_origins()
logger.info(f"CORS origins configurados: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(bills.router, prefix="/api/v1/bills", tags=["Boletos"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Pagamentos"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notificações"])
app.include_router(qa.router, prefix="/api/v1/qa", tags=["QA"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["Chatbot"])
app.include_router(savings_goals.router, prefix="/api/v1/savings-goals", tags=["Metas de Economia"])
app.include_router(investments.router, prefix="/api/v1/investments", tags=["Investimentos"])


@app.get("/")
async def root():
    return {"message": "EconomizeIA API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

