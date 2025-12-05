from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.api.v1 import auth, bills, payments, notifications, qa, chatbot, savings_goals, investments
from app.db.database import engine, Base

# Importar modelos para garantir que sejam registrados no Base.metadata
from app.db.models import SavingsGoal, Investment  # noqa: F401

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

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


@app.post("/api/v1/reset-all-users")
async def reset_all_users():
    """
    ⚠️ ENDPOINT TEMPORÁRIO - APAGA TODOS OS USUÁRIOS E DADOS!
    REMOVER DEPOIS DE USAR!
    """
    from sqlalchemy import text
    
    try:
        with engine.connect() as connection:
            print("🗑️  Apagando todos os dados...")
            
            # Apagar dados relacionados primeiro (devido a foreign keys)
            connection.execute(text("DELETE FROM audit_logs"))
            connection.commit()
            print("✅ Audit logs apagados")
            
            connection.execute(text("DELETE FROM notifications"))
            connection.commit()
            print("✅ Notificações apagadas")
            
            # Novas tabelas
            try:
                connection.execute(text("DELETE FROM savings_goals"))
                connection.commit()
                print("✅ Metas de economia apagadas")
            except:
                pass  # Tabela pode não existir ainda
            
            try:
                connection.execute(text("DELETE FROM investments"))
                connection.commit()
                print("✅ Investimentos apagados")
            except:
                pass  # Tabela pode não existir ainda
            
            connection.execute(text("DELETE FROM payments"))
            connection.commit()
            print("✅ Pagamentos apagados")
            
            connection.execute(text("DELETE FROM bills"))
            connection.commit()
            print("✅ Boletos/Finanças apagados")
            
            # Apagar todos os usuários
            result = connection.execute(text("DELETE FROM users"))
            connection.commit()
            print(f"✅ {result.rowcount} usuário(s) apagado(s)")
            
            # Verificar
            total_users = connection.execute(text("SELECT COUNT(*) FROM users")).scalar()
            total_bills = connection.execute(text("SELECT COUNT(*) FROM bills")).scalar()
            
            return {
                "status": "success",
                "message": "Todos os dados foram apagados!",
                "usuarios_restantes": total_users,
                "boletos_restantes": total_bills
            }
            
    except Exception as e:
        logger.error(f"Erro ao resetar: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/api/v1/cors-debug")
async def cors_debug():
    """Endpoint de debug para verificar CORS configurado."""
    return {
        "cors_origins": settings.get_cors_origins(),
        "cors_origins_raw": settings.CORS_ORIGINS
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

