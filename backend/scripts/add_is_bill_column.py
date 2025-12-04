#!/usr/bin/env python3
"""Script para adicionar coluna is_bill à tabela bills."""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import engine
from sqlalchemy import text

def add_is_bill_column():
    """Adiciona a coluna is_bill se não existir."""
    try:
        with engine.connect() as conn:
            # Verificar se a coluna já existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='bills' AND column_name='is_bill'
            """))
            
            if result.fetchone():
                print("✅ Coluna 'is_bill' já existe!")
                return
            
            # Adicionar coluna
            conn.execute(text("""
                ALTER TABLE bills 
                ADD COLUMN is_bill BOOLEAN DEFAULT TRUE
            """))
            conn.commit()
            print("✅ Coluna 'is_bill' adicionada com sucesso!")
            
            # Atualizar registros existentes: se tiver documento, é boleto
            conn.execute(text("""
                UPDATE bills 
                SET is_bill = TRUE 
                WHERE id IN (
                    SELECT DISTINCT bill_id 
                    FROM bill_documents
                )
            """))
            conn.commit()
            print("✅ Registros existentes atualizados!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_is_bill_column()

