#!/usr/bin/env python3
"""
Script para resetar/apagar todos os usuários do banco de dados.
⚠️ ATENÇÃO: Isso apaga TODOS os dados do sistema!
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.config import settings

def reset_users():
    """Apaga todos os usuários e dados relacionados."""
    print("⚠️  ATENÇÃO: Isso vai apagar TODOS os usuários e dados relacionados!")
    resposta = input("Tem certeza? Digite 'SIM' para confirmar: ")
    
    if resposta != "SIM":
        print("Operação cancelada.")
        return
    
    # Criar conexão com o banco
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("\n🗑️  Apagando dados...")
        
        # Apagar dados relacionados primeiro (devido a foreign keys)
        session.execute(text("DELETE FROM audit_logs"))
        print("✅ Audit logs apagados")
        
        session.execute(text("DELETE FROM notifications"))
        print("✅ Notificações apagadas")
        
        session.execute(text("DELETE FROM payments"))
        print("✅ Pagamentos apagados")
        
        session.execute(text("DELETE FROM bills"))
        print("✅ Boletos/Finanças apagados")
        
        # Apagar todos os usuários
        result = session.execute(text("DELETE FROM users"))
        print(f"✅ {result.rowcount} usuário(s) apagado(s)")
        
        # Commit
        session.commit()
        print("\n✅ Reset completo! Todos os dados foram apagados.")
        
        # Verificar
        total_users = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        total_bills = session.execute(text("SELECT COUNT(*) FROM bills")).scalar()
        print(f"\n📊 Verificação:")
        print(f"   - Usuários: {total_users}")
        print(f"   - Boletos: {total_bills}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    reset_users()

