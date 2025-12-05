#!/usr/bin/env python3
"""
Script para zerar todos os usuários do banco de dados.
Uso: python scripts/zerar_usuarios.py
"""
import requests
import json

URL = "https://economizeia-production.up.railway.app/api/v1/reset-all-users"

print("⚠️  ATENÇÃO: Isso vai deletar TODOS os usuários do banco de dados!")
print()
confirm = input("Digite 'SIM' para confirmar: ")

if confirm != "SIM":
    print("Operação cancelada.")
    exit(1)

print()
print("Enviando requisição DELETE...")

try:
    response = requests.delete(URL)
    response.raise_for_status()
    
    data = response.json()
    
    print()
    print("✅ Sucesso!")
    print(f"Mensagem: {data.get('message', 'N/A')}")
    print(f"Usuários deletados: {data.get('deleted_count', 0)}")
    print(f"Usuários restantes: {data.get('remaining_count', 0)}")
    
except requests.exceptions.RequestException as e:
    print()
    print("❌ Erro ao deletar usuários:")
    print(f"Erro: {e}")
    if hasattr(e, 'response') and e.response is not None:
        try:
            error_data = e.response.json()
            print(f"Detalhes: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Resposta: {e.response.text}")

