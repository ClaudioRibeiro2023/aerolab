#!/bin/bash
# Script de deploy rápido para Netlify

echo "🚀 Agno Platform - Deploy no Netlify"
echo "===================================="
echo ""

# Verificar se netlify CLI está instalado
if ! command -v netlify &> /dev/null; then
    echo "❌ Netlify CLI não encontrado!"
    echo "📦 Instalando..."
    npm install -g netlify-cli
fi

# Login
echo "🔐 Fazendo login no Netlify..."
netlify login

# Build local para testar
echo "🏗️  Testando build..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build falhou! Corrija os erros antes de fazer deploy."
    exit 1
fi

echo "✅ Build bem-sucedido!"
echo ""

# Verificar se já tem site configurado
if [ ! -f ".netlify/state.json" ]; then
    echo "📝 Inicializando novo site no Netlify..."
    netlify init
fi

# Verificar variável de ambiente
echo ""
echo "⚠️  IMPORTANTE: Configure a URL do backend!"
echo ""
read -p "Digite a URL do backend (ex: https://seu-backend.railway.app): " backend_url

if [ -z "$backend_url" ]; then
    echo "❌ URL do backend não pode ser vazia!"
    exit 1
fi

echo "🔧 Configurando variável de ambiente..."
netlify env:set NEXT_PUBLIC_API_URL "$backend_url"

# Deploy
echo ""
echo "🚀 Fazendo deploy para produção..."
netlify deploy --prod

echo ""
echo "✅ Deploy concluído!"
echo ""
echo "📋 Próximos passos:"
echo "1. Acesse o site e teste o login"
echo "2. Configure CORS no backend com a URL do Netlify"
echo "3. Configure domínio customizado (opcional)"
