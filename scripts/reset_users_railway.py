#!/usr/bin/env python3
"""
Script para resetar/apagar todos os usuários do banco de dados Railway.
⚠️ ATENÇÃO: Isso apaga TODOS os dados do sistema!

Como usar:
1. Copie a DATABASE_URL do Railway (Postgres → Variables → DATABASE_URL)
2. Execute: python reset_users_railway.py
3. Cole a DATABASE_URL quando pedir
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy import create_engine, text

def reset_users():
    """Apaga todos os usuários e dados relacionados."""
    print("⚠️  ATENÇÃO: Isso vai apagar TODOS os usuários e dados relacionados!")
    print("\nVocê precisa da DATABASE_URL do Railway:")
    print("1. No Railway → Postgres → Variables")
    print("2. Copie o valor de DATABASE_URL")
    print()
    
    database_url = input("Cole a DATABASE_URL aqui: ").strip()
    
    if not database_url:
        print("❌ DATABASE_URL não pode estar vazio!")
        return
    
    resposta = input("\nTem certeza que quer apagar TODOS os dados? Digite 'SIM' para confirmar: ")
    
    if resposta != "SIM":
        print("Operação cancelada.")
        return
    
    # Criar conexão com o banco
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            print("\n🗑️  Apagando dados...")
            
            # Apagar dados relacionados primeiro (devido a foreign keys)
            conn.execute(text("DELETE FROM audit_logs"))
            conn.commit()
            print("✅ Audit logs apagados")
            
            conn.execute(text("DELETE FROM notifications"))
            conn.commit()
            print("✅ Notificações apagadas")
            
            # Novas tabelas
            conn.execute(text("DELETE FROM savings_goals"))
            conn.commit()
            print("✅ Metas de economia apagadas")
            
            conn.execute(text("DELETE FROM investments"))
            conn.commit()
            print("✅ Investimentos apagados")
            
            conn.execute(text("DELETE FROM payments"))
            conn.commit()
            print("✅ Pagamentos apagados")
            
            conn.execute(text("DELETE FROM bills"))
            conn.commit()
            print("✅ Boletos/Finanças apagados")
            
            # Apagar todos os usuários
            result = conn.execute(text("DELETE FROM users"))
            conn.commit()
            print(f"✅ {result.rowcount} usuário(s) apagado(s)")
            
            # Verificar
            total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            total_bills = conn.execute(text("SELECT COUNT(*) FROM bills")).scalar()
            print(f"\n✅ Reset completo!")
            print(f"📊 Verificação:")
            print(f"   - Usuários: {total_users}")
            print(f"   - Boletos: {total_bills}")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nVerifique se a DATABASE_URL está correta!")

if __name__ == "__main__":
    reset_users()

