# Script para zerar todos os usuários do banco de dados
# Uso: .\scripts\zerar_usuarios.ps1

$url = "https://economizeia-production.up.railway.app/api/v1/reset-all-users"

Write-Host "⚠️  ATENÇÃO: Isso vai deletar TODOS os usuários do banco de dados!" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Digite 'SIM' para confirmar"

if ($confirm -ne "SIM") {
    Write-Host "Operação cancelada." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Enviando requisição DELETE..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $url -Method Delete -ContentType "application/json"
    
    Write-Host ""
    Write-Host "✅ Sucesso!" -ForegroundColor Green
    Write-Host "Mensagem: $($response.message)" -ForegroundColor Green
    Write-Host "Usuários deletados: $($response.deleted_count)" -ForegroundColor Green
    Write-Host "Usuários restantes: $($response.remaining_count)" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ Erro ao deletar usuários:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.ErrorDetails.Message) {
        Write-Host "Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

