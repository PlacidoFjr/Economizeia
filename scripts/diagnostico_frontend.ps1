# Script de diagnóstico do frontend - Windows PowerShell
# Uso: .\scripts\diagnostico_frontend.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnóstico Frontend - FinGuia" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está na pasta correta
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Execute este script na pasta frontend!" -ForegroundColor Red
    Write-Host "   Você está em: $PWD" -ForegroundColor Yellow
    Write-Host "   Deve estar em: K:\Projetos\FINDGUIA\frontend" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/6] Verificando Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Node.js: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "  ❌ Node.js não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "[2/6] Verificando npm..." -ForegroundColor Yellow
$npmVersion = npm --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ npm: $npmVersion" -ForegroundColor Green
} else {
    Write-Host "  ❌ npm não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "[3/6] Verificando arquivos principais..." -ForegroundColor Yellow
$files = @("package.json", "index.html", "src/main.tsx", "src/App.tsx", "vite.config.ts")
$allOk = $true
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file não encontrado!" -ForegroundColor Red
        $allOk = $false
    }
}

if (-not $allOk) {
    Write-Host ""
    Write-Host "❌ Alguns arquivos estão faltando!" -ForegroundColor Red
    exit 1
}

Write-Host "[4/6] Verificando dependências..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    $packageCount = (Get-ChildItem node_modules -Directory | Measure-Object).Count
    Write-Host "  ✅ node_modules existe ($packageCount pacotes)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  node_modules não encontrado. Execute: npm install" -ForegroundColor Yellow
}

Write-Host "[5/6] Verificando porta 3000..." -ForegroundColor Yellow
$portInUse = netstat -ano | findstr ":3000" | findstr "LISTENING"
if ($portInUse) {
    Write-Host "  ⚠️  Porta 3000 está em uso!" -ForegroundColor Yellow
    Write-Host "     Pode ser o servidor já rodando ou outro programa" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ Porta 3000 está livre" -ForegroundColor Green
}

Write-Host "[6/6] Verificando backend..." -ForegroundColor Yellow
$backendRunning = docker ps --filter "name=finguia-backend" --format "{{.Names}}" 2>$null
if ($backendRunning) {
    Write-Host "  ✅ Backend está rodando" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Backend não está rodando" -ForegroundColor Yellow
    Write-Host "     Execute: docker-compose up -d backend" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnóstico concluído!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para iniciar o servidor:" -ForegroundColor Yellow
Write-Host "  npm run dev" -ForegroundColor Cyan
Write-Host ""

