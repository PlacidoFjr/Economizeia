# Script para verificar o banco de dados - Windows PowerShell
# Uso: .\scripts\verificar_banco.ps1

Write-Host "Verificando banco de dados FinGuia..." -ForegroundColor Green

$result = docker exec finguia-postgres psql -U finguia -d finguia_db -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Banco de dados está funcionando!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tabelas encontradas:" -ForegroundColor Yellow
    Write-Host $result
} else {
    Write-Host "❌ Erro ao conectar ao banco de dados" -ForegroundColor Red
    Write-Host "Verifique se o container está rodando:" -ForegroundColor Yellow
    Write-Host "  docker ps | findstr postgres" -ForegroundColor Cyan
    exit 1
}

