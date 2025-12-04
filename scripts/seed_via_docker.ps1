# Script para popular banco de dados via Docker - Windows PowerShell
# Uso: .\scripts\seed_via_docker.ps1
# IMPORTANTE: Execute na pasta raiz do projeto!

# Verificar se está na pasta correta
if (-not (Test-Path "scripts\seed_data.py")) {
    Write-Host "❌ Erro: Execute este script na pasta raiz do projeto (FINDGUIA)" -ForegroundColor Red
    Write-Host "   Você está em: $PWD" -ForegroundColor Yellow
    Write-Host "   Deve estar em: K:\Projetos\FINDGUIA" -ForegroundColor Yellow
    exit 1
}

Write-Host "Populando banco de dados com dados de teste..." -ForegroundColor Green

# Verificar se o container está rodando
$containerRunning = docker ps --filter "name=finguia-backend" --format "{{.Names}}"

if (-not $containerRunning) {
    Write-Host "Container não está rodando. Iniciando..." -ForegroundColor Yellow
    docker-compose up -d backend
    Start-Sleep -Seconds 5
}

# Copiar script para o container
Write-Host "Copiando script para o container..." -ForegroundColor Yellow
docker cp scripts/seed_data.py finguia-backend:/app/seed_data.py

# Executar seed
Write-Host "Executando script de seed..." -ForegroundColor Yellow
docker exec finguia-backend python /app/seed_data.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Dados de teste criados com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Credenciais de login:" -ForegroundColor Cyan
    Write-Host "  Email: teste@finguia.com" -ForegroundColor White
    Write-Host "  Senha: senha123" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Erro ao popular banco de dados" -ForegroundColor Red
    Write-Host "Verifique os logs:" -ForegroundColor Yellow
    Write-Host "  docker logs finguia-backend" -ForegroundColor Cyan
    exit 1
}

