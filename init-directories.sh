#!/bin/bash
# Script para inicializar estrutura de diretórios
# Execute antes do primeiro deploy: ./init-directories.sh

set -e

echo "Inicializando estrutura de diretórios..."

# Criar diretórios de logs
mkdir -p logs
touch logs/app.log
touch logs/.gitkeep
echo "✓ Diretório logs/ criado"

# Criar diretório de uploads
mkdir -p app/static/uploads
touch app/static/uploads/.gitkeep
echo "✓ Diretório uploads/ criado"

# Criar diretório de backups
mkdir -p backups
touch backups/.gitkeep
echo "✓ Diretório backups/ criado"

# Criar diretório de SSL (para produção)
mkdir -p ssl
touch ssl/.gitkeep
echo "✓ Diretório ssl/ criado (colocar certificados aqui)"

# Criar diretório de certificados auto-assinados de teste
mkdir -p ssl/test-certs
echo "✓ Diretório ssl/test-certs/ criado"

# Gerar certificado auto-assinado para teste (opcional)
# Descomente para gerar certificado de teste
# openssl req -x509 -newkey rsa:4096 -nodes -out ssl/test-certs/cert.pem -keyout ssl/test-certs/key.pem -days 365

# Ajustar permissões
chmod 755 logs backups app/static/uploads ssl
chmod 644 logs/.gitkeep backups/.gitkeep app/static/uploads/.gitkeep ssl/.gitkeep

echo ""
echo "✓ Estrutura de diretórios inicializada com sucesso!"
echo ""
echo "Próximos passos:"
echo "1. Copiar .env.example para .env: cp .env.example .env"
echo "2. Editar .env com suas credenciais"
echo "3. Executar security_check.py para validar: python security_check.py"
echo "4. Fazer deploy: docker-compose up -d"
echo ""
