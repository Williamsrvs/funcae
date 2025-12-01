#!/bin/bash
# 🚀 QUICK START - Iniciar em 30 segundos

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         NeuroEduca - Deploy Ready (Pronto para Deploy)    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar arquivos críticos
echo "📋 Verificando arquivos..."
files=(
    ".env.example"
    "config.py"
    ".gitignore"
    "Dockerfile"
    "docker-compose.yml"
    "nginx.conf"
    "DEPLOY.md"
    "README.md"
    "security_check.py"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (FALTA)"
        all_exist=false
    fi
done

echo ""

if [ "$all_exist" = false ]; then
    echo "⚠️  Alguns arquivos estão faltando!"
    exit 1
fi

echo "✅ Todos os arquivos de deploy estão presentes!"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

echo "🎯 PRÓXIMOS PASSOS:"
echo ""
echo "1️⃣  Prepare os diretórios (Escolha conforme seu SO):"
echo ""
echo "    Linux/Mac:"
echo "    $ bash init-directories.sh"
echo ""
echo "    Windows (PowerShell):"
echo "    $ .\init-directories.ps1"
echo ""

echo "2️⃣  Configure as variáveis de ambiente:"
echo ""
echo "    $ cp .env.example .env"
echo "    $ nano .env  (ou seu editor favorito)"
echo ""
echo "    ⚠️  IMPORTANTE: Altere estes campos:"
echo "       - FLASK_SECRET_KEY"
echo "       - MYSQL_HOST"
echo "       - MYSQL_USER"
echo "       - MYSQL_PASSWORD"
echo "       - MYSQL_DB"
echo ""

echo "3️⃣  Valide a segurança:"
echo ""
echo "    $ python security_check.py"
echo "    # Deve retornar: ✅ PASSOU - Pronto para deploy!"
echo ""

echo "4️⃣  Inicie o deploy:"
echo ""
echo "    Docker:"
echo "    $ docker-compose up -d"
echo ""
echo "    OU use o script interativo:"
echo "    - Linux/Mac: $ python deploy.py"
echo "    - Windows: $ .\deploy.bat"
echo ""

echo "5️⃣  Teste acesso:"
echo ""
echo "    $ curl http://localhost/"
echo "    # Ou abra no navegador: http://localhost"
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo "📚 DOCUMENTAÇÃO:"
echo ""
echo "   README.md          - Visão geral do projeto"
echo "   DEPLOY.md          - Guia completo de deploy"
echo "   DEPLOY-CHECKLIST.md - Checklist de preparação"
echo "   config.py          - Configurações por ambiente"
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo "✨ Seu projeto está 100% preparado para deploy!"
echo ""
