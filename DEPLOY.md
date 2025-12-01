# 🚀 GUIA DE DEPLOY - NEUROEDUCA

## Índice
1. [Preparação Inicial](#preparação-inicial)
2. [Deploy Local com Docker](#deploy-local-com-docker)
3. [Deploy em Produção](#deploy-em-produção)
4. [Segurança](#segurança)
5. [Monitoramento](#monitoramento)
6. [Troubleshooting](#troubleshooting)

---

## Preparação Inicial

### Pré-requisitos
- Docker e Docker Compose instalados
- Git configurado
- Acesso SSH à servidor de produção (se aplicável)

### 1. Clonar o Repositório
```bash
git clone <seu-repositorio> neuroeduca
cd neuroeduca
```

### 2. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo exemplo
cp .env.example .env

# Editar com suas configurações reais
nano .env
```

**Variáveis obrigatórias:**
```env
FLASK_ENV=production
FLASK_SECRET_KEY=<gerar_chave_aleatoria_segura>
MYSQL_HOST=seu_host
MYSQL_USER=seu_usuario
MYSQL_PASSWORD=sua_senha_segura
MYSQL_DB=seu_banco_dados
```

### 3. Gerar Chave Segura para FLASK_SECRET_KEY
```bash
# Linux/Mac
python3 -c "import secrets; print(secrets.token_hex(32))"

# Windows PowerShell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Deploy Local com Docker

### Iniciar Containers
```bash
# Build e inicia os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f app

# Verificar status
docker-compose ps
```

### Primeiro Acesso
1. Acesse: `http://localhost` (ou a porta configurada)
2. Verifique se o banco de dados está conectado
3. Execute scripts de inicialização se necessário

### Parar Containers
```bash
docker-compose down

# Com limpeza de volumes (CUIDADO!)
docker-compose down -v
```

---

## Deploy em Produção

### Opção 1: Deploy com Docker em VPS

#### 1.1 Preparar Servidor
```bash
# SSH no servidor
ssh user@your-server.com

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Criar diretório da aplicação
mkdir -p /opt/neuroeduca
cd /opt/neuroeduca
```

#### 1.2 Clonar Código
```bash
git clone <seu-repositorio> .
```

#### 1.3 Configurar Produção
```bash
# Editar arquivo .env com valores de produção
nano .env

# Configurações críticas para produção:
FLASK_ENV=production
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

#### 1.4 Gerar Certificados SSL (HTTPS)
```bash
# Usando Let's Encrypt (recomendado)
sudo apt-get install certbot python3-certbot-nginx

sudo certbot certonly --standalone -d seu-dominio.com

# Copiar certificados
sudo cp /etc/letsencrypt/live/seu-dominio.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/seu-dominio.com/privkey.pem ./ssl/key.pem
sudo chown $USER:$USER ./ssl/*
```

#### 1.5 Atualizar Nginx com SSL
```bash
# Descomente as linhas HTTPS no arquivo nginx.conf
# E configure seu domínio
```

#### 1.6 Iniciar Produção
```bash
# Build com otimizações
docker-compose -f docker-compose.yml up -d

# Verificar status
docker-compose ps
docker-compose logs app
```

### Opção 2: Deploy em Plataformas Gerenciadas

#### Heroku
```bash
# Instalar Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Criar aplicação
heroku create seu-app-name

# Adicionar banco de dados MySQL
heroku addons:create cleardb:ignite

# Configurar variáveis de ambiente
heroku config:set FLASK_ENV=production
heroku config:set FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Deploy
git push heroku main

# Ver logs
heroku logs --tail
```

#### AWS (ECS)
```bash
# 1. Criar repositório ECR
aws ecr create-repository --repository-name neuroeduca

# 2. Build e push da imagem
docker build -t neuroeduca:latest .
docker tag neuroeduca:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/neuroeduca:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/neuroeduca:latest

# 3. Criar task definition e serviço no ECS
# (Use AWS Console ou AWS CLI)
```

#### Railway
```bash
# 1. Fazer push do repositório para GitHub

# 2. Conectar no Railway dashboard:
# https://railway.app/dashboard

# 3. Configurar variáveis de ambiente no painel
```

---

## Segurança

### ✅ Checklist de Segurança Pré-Deploy

- [ ] **Variáveis de Ambiente Seguras**
  - [ ] FLASK_SECRET_KEY alterada (não usar padrão)
  - [ ] Banco de dados com senha forte (mínimo 12 caracteres)
  - [ ] Nenhuma credencial no código-fonte

- [ ] **Banco de Dados**
  - [ ] Backup automático configurado
  - [ ] Acesso restrito por IP (firewall)
  - [ ] Usuário de produção com permissões limitadas

- [ ] **Servidor**
  - [ ] Firewall ativo (portas 80, 443 apenas abertas)
  - [ ] SSH com autenticação por chave (não senha)
  - [ ] Desabilitar root login
  - [ ] Fail2ban ou similar configurado

- [ ] **HTTPS/SSL**
  - [ ] Certificado SSL válido instalado
  - [ ] Redirecionamento HTTP → HTTPS ativo
  - [ ] HSTS header configurado

- [ ] **Aplicação**
  - [ ] DEBUG mode desligado (FLASK_ENV=production)
  - [ ] Logs configurados e monitorados
  - [ ] Uploads de usuário sanitizados
  - [ ] Rate limiting ativo

- [ ] **Backup & Recuperação**
  - [ ] Backup automático diário do banco
  - [ ] Plano de recuperação testado
  - [ ] Logs centralizados

### Vulnerabilidades Comuns - Remediação

#### 1. SQL Injection
**Status:** ✅ Usando parametrização (bom)
```python
# ✅ BOM
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ RUIM
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

#### 2. Credenciais em Código
**Ação:** Usar apenas variáveis de ambiente
```bash
# Verificar se há credenciais no git
git log -p -S 'Q1k2v1y5' | head -20
```

#### 3. Senha Fraca
**Implementar:** Validação de senha forte
```python
import re

def validar_senha_forte(senha):
    if len(senha) < 12:
        return False, "Mínimo 12 caracteres"
    if not re.search(r'[A-Z]', senha):
        return False, "Deve conter letra maiúscula"
    if not re.search(r'[a-z]', senha):
        return False, "Deve conter letra minúscula"
    if not re.search(r'[0-9]', senha):
        return False, "Deve conter número"
    if not re.search(r'[!@#$%^&*]', senha):
        return False, "Deve conter caractere especial"
    return True, "Senha válida"
```

---

## Monitoramento

### Logs
```bash
# Ver logs da aplicação
docker-compose logs app

# Ver logs do banco de dados
docker-compose logs mysql

# Ver logs em tempo real
docker-compose logs -f

# Salvar logs para arquivo
docker-compose logs > logs.txt
```

### Health Check
```bash
# Testar endpoint da aplicação
curl -i http://localhost/

# Ver status do container
docker-compose ps
docker stats
```

### Backup Automático do Banco
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/mysql"
CONTAINER="neuroeduca-mysql"
DATABASE="u799109175_db_funcae"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

docker exec $CONTAINER mysqldump -u$MYSQL_USER -p$MYSQL_PASSWORD $DATABASE \
  | gzip > $BACKUP_DIR/backup_${DATE}.sql.gz

# Manter apenas últimos 30 dias
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup criado: $BACKUP_DIR/backup_${DATE}.sql.gz"
```

**Agendar com Cron:**
```bash
# Executar backup todos os dias às 2 da manhã
0 2 * * * /opt/neuroeduca/backup.sh >> /var/log/neuroeduca-backup.log 2>&1
```

### Monitoramento Contínuo
```bash
# Instalar Portainer (Web UI para Docker)
docker run -d -p 8000:8000 -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  portainer/portainer-ce:latest
```

---

## Troubleshooting

### Aplicação não inicia
```bash
# Ver logs detalhados
docker-compose logs app | tail -50

# Verificar se variáveis de ambiente estão corretas
docker-compose config | grep -A 10 "environment:"

# Recriar container
docker-compose down
docker-compose up -d --build
```

### Erro de Conexão com Banco
```bash
# Verificar conectividade
docker-compose exec app ping mysql

# Testar credenciais
docker-compose exec mysql mysql -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DB -e "SELECT 1;"

# Ver logs do MySQL
docker-compose logs mysql
```

### Porta 80/443 Já em Uso
```bash
# Ver o que está usando a porta
sudo lsof -i :80
sudo lsof -i :443

# Matar processo
sudo kill -9 <PID>
```

### Performance Lenta
```bash
# Verificar recursos
docker stats

# Aumentar workers em production
# Editar docker-compose.yml:
# gunicorn --workers 8 --threads 4 ...

# Verificar índices no banco
docker-compose exec mysql mysql -e "SELECT * FROM information_schema.STATISTICS;"
```

### Resetar Banco de Dados (CUIDADO!)
```bash
# Backup primeiro!
docker-compose exec mysql mysqldump -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DB > backup.sql

# Remover volumes
docker-compose down -v

# Recrear
docker-compose up -d
```

---

## Após Deploy - Checklist Final

- [ ] Acessar aplicação e testar funcionalidades principais
- [ ] Verificar logs sem erros críticos
- [ ] Confirmar backup automático funcionando
- [ ] Testar login e autenticação
- [ ] Verificar HTTPS em produção
- [ ] Testar upload de arquivos
- [ ] Confirmar emails/notificações (se houver)
- [ ] Documentar IPs e acessos
- [ ] Criar runbook de emergência

---

## Suporte & Documentação

- **Docker Docs:** https://docs.docker.com
- **Flask Docs:** https://flask.palletsprojects.com
- **MySQL Docs:** https://dev.mysql.com/doc

**Contato do Desenvolvedor:** [seu-email@exemplo.com]
