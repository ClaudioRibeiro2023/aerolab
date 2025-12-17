# Script de deploy rápido para Netlify (Windows PowerShell)

Write-Host "🚀 Agno Platform - Deploy no Netlify" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Verificar se netlify CLI está instalado
$netlifyCLI = Get-Command netlify -ErrorAction SilentlyContinue
if (-not $netlifyCLI) {
    Write-Host "❌ Netlify CLI não encontrado!" -ForegroundColor Red
    Write-Host "📦 Instalando..." -ForegroundColor Yellow
    npm install -g netlify-cli
}

# Login
Write-Host "🔐 Fazendo login no Netlify..." -ForegroundColor Cyan
netlify login

# Build local para testar
Write-Host "🏗️  Testando build..." -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build falhou! Corrija os erros antes de fazer deploy." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build bem-sucedido!" -ForegroundColor Green
Write-Host ""

# Verificar se já tem site configurado
if (-not (Test-Path ".netlify\state.json")) {
    Write-Host "📝 Inicializando novo site no Netlify..." -ForegroundColor Cyan
    netlify init
}

# Verificar variável de ambiente
Write-Host ""
Write-Host "⚠️  IMPORTANTE: Configure a URL do backend!" -ForegroundColor Yellow
Write-Host ""
$backendUrl = Read-Host "Digite a URL do backend (ex: https://seu-backend.railway.app)"

if ([string]::IsNullOrWhiteSpace($backendUrl)) {
    Write-Host "❌ URL do backend não pode ser vazia!" -ForegroundColor Red
    exit 1
}

Write-Host "🔧 Configurando variável de ambiente..." -ForegroundColor Cyan
netlify env:set NEXT_PUBLIC_API_URL $backendUrl

# Deploy
Write-Host ""
Write-Host "🚀 Fazendo deploy para produção..." -ForegroundColor Cyan
netlify deploy --prod

Write-Host ""
Write-Host "✅ Deploy concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Acesse o site e teste o login"
Write-Host "2. Configure CORS no backend com a URL do Netlify"
Write-Host "3. Configure domínio customizado (opcional)"
