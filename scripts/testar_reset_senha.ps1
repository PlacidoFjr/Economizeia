# Script para testar redefinição de senha

Write-Host "🧪 Testando Redefinição de Senha..." -ForegroundColor Cyan
Write-Host ""

# Teste 1: Solicitar redefinição de senha
Write-Host "1️⃣ Testando solicitação de redefinição..." -ForegroundColor Yellow

$body = @{
    email = "teste@finguia.com"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/forgot-password" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    
    Write-Host "✅ Resposta do servidor:" -ForegroundColor Green
    Write-Host $response.Content
    Write-Host ""
    
    # Verificar logs para ver o link
    Write-Host "2️⃣ Verificando logs do backend para link de redefinição..." -ForegroundColor Yellow
    Write-Host ""
    
    Start-Sleep -Seconds 2
    
    $logs = docker logs finguia-backend --tail 20 2>&1
    $resetLink = $logs | Select-String -Pattern "Reset link"
    
    if ($resetLink) {
        Write-Host "✅ Link de redefinição encontrado nos logs:" -ForegroundColor Green
        Write-Host $resetLink -ForegroundColor Cyan
        Write-Host ""
        Write-Host "💡 Você pode copiar esse link e usar diretamente no navegador!" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️ Link não encontrado nos logs. Verificando se usuário existe..." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Erro ao testar:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Verifique os logs completos: docker logs finguia-backend --tail 50"
Write-Host "2. Se o email não estiver configurado, o link aparecerá nos logs"
Write-Host "3. Copie o link e cole no navegador para testar a redefinicao"
Write-Host ""

