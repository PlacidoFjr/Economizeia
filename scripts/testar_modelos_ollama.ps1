# Script para testar diferentes modelos Ollama

Write-Host "🧪 Testando Modelos Ollama para FinGuia" -ForegroundColor Cyan
Write-Host ""

$models = @(
    @{name="qwen2.5:7b"; desc="Qwen2.5 7B (Recomendado)"},
    @{name="mistral:7b"; desc="Mistral 7B (Rápido)"},
    @{name="phi3:mini"; desc="Phi-3 Mini (Leve)"},
    @{name="llama3.2:3b"; desc="Llama 3.2 3B (Atual)"}
)

$pergunta = "Olá, como você pode me ajudar com gestão financeira?"

foreach ($model in $models) {
    Write-Host "📊 Testando: $($model.desc)" -ForegroundColor Yellow
    Write-Host "   Modelo: $($model.name)" -ForegroundColor Gray
    
    $startTime = Get-Date
    
    try {
        $result = ollama run $model.name $pergunta 2>&1
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host "   ✅ Resposta em $([math]::Round($duration, 2))s" -ForegroundColor Green
        Write-Host "   Resposta: $($result -join ' ' | Select-String -Pattern '.' | Select-Object -First 1)" -ForegroundColor Gray
    } catch {
        Write-Host "   ❌ Erro: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    Start-Sleep -Seconds 2
}

Write-Host "✅ Teste concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Recomendação: Use o modelo que teve melhor equilíbrio entre velocidade e qualidade" -ForegroundColor Cyan

