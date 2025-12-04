# Script para criar o banco de dados - Windows PowerShell
# Uso: .\scripts\criar_banco.ps1

Write-Host "Criando banco de dados FinGuia..." -ForegroundColor Green

$schemaFile = "backend/app/db/schema.sql"

if (-not (Test-Path $schemaFile)) {
    Write-Host "Erro: Arquivo $schemaFile não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "Lendo arquivo schema.sql..." -ForegroundColor Yellow
Get-Content $schemaFile | docker exec -i finguia-postgres psql -U finguia -d finguia_db

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Banco de dados criado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao criar banco de dados" -ForegroundColor Red
    exit 1
}

