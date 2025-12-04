#!/bin/bash

echo "========================================"
echo "Verificador de Ollama - FinGuia"
echo "========================================"
echo ""

# Verificar se Ollama está instalado
echo "[1/3] Verificando se o Ollama está instalado..."
if ! command -v ollama &> /dev/null; then
    echo "[ERRO] Ollama não encontrado!"
    echo "Por favor, instale o Ollama primeiro: https://ollama.ai/download"
    exit 1
fi
echo "[OK] Ollama está instalado"
echo ""

# Verificar se está rodando
echo "[2/3] Verificando se o Ollama está rodando..."
if ollama list &> /dev/null; then
    echo "[OK] Ollama está RODANDO!"
    echo ""
    echo "Modelos instalados:"
    ollama list
    echo ""
    echo "Tudo certo! Você pode continuar usando o FinGuia."
    exit 0
else
    echo "[AVISO] Ollama não está respondendo"
    echo ""
fi

# Verificar porta
echo "[3/3] Verificando se a porta 11434 está em uso..."
if lsof -i :11434 &> /dev/null || netstat -tlnp 2>/dev/null | grep :11434 &> /dev/null; then
    echo "[AVISO] Porta 11434 está em uso!"
    echo ""
    echo "Processos usando a porta 11434:"
    if command -v lsof &> /dev/null; then
        lsof -i :11434
    elif command -v netstat &> /dev/null; then
        netstat -tlnp | grep :11434
    fi
    echo ""
    read -p "Deseja parar o processo? (s/N): " resposta
    if [[ "$resposta" =~ ^[Ss]$ ]]; then
        echo ""
        echo "Por favor, copie o PID da linha acima"
        echo "e execute: kill <PID>"
        echo ""
    fi
else
    echo "[OK] Porta 11434 está livre"
    echo ""
    echo "Iniciando Ollama..."
    ollama serve &
    echo ""
    echo "Ollama iniciado! Aguarde alguns segundos e tente novamente."
fi

echo ""
echo "========================================"
echo "Verificação concluída!"
echo "========================================"

