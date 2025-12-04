@echo off
echo ========================================
echo Verificador de Ollama - FinGuia
echo ========================================
echo.

echo [1/3] Verificando se o Ollama esta instalado...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Ollama nao encontrado!
    echo Por favor, instale o Ollama primeiro: https://ollama.ai/download
    pause
    exit /b 1
)
echo [OK] Ollama esta instalado
echo.

echo [2/3] Verificando se o Ollama esta rodando...
ollama list >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama esta RODANDO!
    echo.
    echo Modelos instalados:
    ollama list
    echo.
    echo Tudo certo! Voce pode continuar usando o FinGuia.
    pause
    exit /b 0
) else (
    echo [AVISO] Ollama nao esta respondendo
    echo.
)

echo [3/3] Verificando se a porta 11434 esta em uso...
netstat -ano | findstr :11434 >nul 2>&1
if %errorlevel% equ 0 (
    echo [AVISO] Porta 11434 esta em uso!
    echo.
    echo Processos usando a porta 11434:
    netstat -ano | findstr :11434
    echo.
    echo Deseja parar o processo? (S/N)
    set /p resposta=
    if /i "%resposta%"=="S" (
        echo.
        echo Por favor, copie o PID (ultimo numero) da linha acima
        echo e execute: taskkill /PID [PID] /F
        echo.
        echo Ou use o Gerenciador de Tarefas:
        echo 1. Pressione Ctrl+Shift+Esc
        echo 2. Procure por "ollama.exe"
        echo 3. Clique com botao direito ^> Finalizar tarefa
        echo.
    )
) else (
    echo [OK] Porta 11434 esta livre
    echo.
    echo Iniciando Ollama...
    start "Ollama Server" cmd /k "ollama serve"
    echo.
    echo Ollama iniciado! Aguarde alguns segundos e tente novamente.
)

echo.
echo ========================================
echo Verificacao concluida!
echo ========================================
pause

