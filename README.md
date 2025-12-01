# 🧠 NeuroEduca - Sistema de Educação Inclusiva

[![Deploy](https://img.shields.io/badge/Deploy-Ready-brightgreen)]()
[![License](https://img.shields.io/badge/License-Proprietary-red)]()
[![Python](https://img.shields.io/badge/Python-3.11-blue)]()
[![Flask](https://img.shields.io/badge/Flask-3.1-purple)]()

## 📋 Sobre o Projeto

NeuroEduca é um sistema web completo para gestão educacional com foco em educação inclusiva, desenvolvido com Flask e MySQL.

### Funcionalidades Principais
- 📚 Gestão de alunos e turmas
- 📊 Avaliações (PEI, PEDI, GUIDE)
- 📈 Dashboard com relatórios
- 🔐 Autenticação segura
- 📁 Upload de documentos
- 📄 Geração de PDFs
- 💾 Backup automático

---

## 🚀 Quick Start

### Pré-requisitos
- Docker e Docker Compose instalados
- Git
- Conhecimento básico de terminal

### Instalação Rápida (3 passos)

**1. Clone o repositório**
```bash
git clone <seu-repositorio> neuroeduca
cd neuroeduca
```

**2. Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite .env com suas credenciais
nano .env  # ou use seu editor favorito
```

**3. Deploy com Docker**
```bash
# Em Linux/Mac:
docker-compose up -d

# Em Windows (PowerShell):
docker-compose up -d
# Ou execute:
.\deploy.bat
```

Acesse a aplicação em: **http://localhost**

---

## 📁 Estrutura do Projeto

```
neuroeduca/
├── app/                          # Aplicação Flask
│   ├── app.py                   # Arquivo principal
│   ├── login.py                 # Autenticação
│   ├── templates/               # Templates HTML
│   └── static/                  # CSS, JS, imagens
│       └── uploads/             # Arquivos de usuários
├── banco_dados/                 # Scripts SQL
├── config.py                    # Configurações por ambiente
├── requirements.txt             # Dependências Python
├── Dockerfile                   # Imagem Docker da app
├── docker-compose.yml           # Orquestração de containers
├── nginx.conf                   # Configuração do proxy reverso
├── DEPLOY.md                    # Guia completo de deploy
├── deploy.py                    # Script Python de deploy
├── deploy.bat                   # Script Windows de deploy
├── security_check.py            # Verificador de segurança
├── .env.example                 # Template de variáveis de ambiente
├── .gitignore                   # Arquivos ignorados pelo Git
└── README.md                    # Este arquivo
```

---

## ⚙️ Configuração

### Variáveis de Ambiente Essenciais

```env
# Flask
FLASK_ENV=production
FLASK_SECRET_KEY=chave-aleatória-segura-mínimo-32-caracteres

# Banco de Dados
MYSQL_HOST=seu-host
MYSQL_USER=seu-usuario
MYSQL_PASSWORD=sua-senha-forte
MYSQL_DB=nome-do-banco

# Servidor
PORT=5000
HOST=0.0.0.0
```

**Gerar chave segura:**
```bash
# Linux/Mac
python3 -c "import secrets; print(secrets.token_hex(32))"

# Windows
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🔍 Verificação de Segurança

Antes de fazer deploy, execute o verificador de segurança:

```bash
python security_check.py
```

Isso validará:
- ✅ Credenciais hardcoded
- ✅ Arquivo .env configurado
- ✅ .gitignore adequado
- ✅ DEBUG mode desligado
- ✅ SQL Injection vulnerabilities
- ✅ Configuração Docker segura
- ✅ Headers de segurança Nginx
- ✅ Backup automático

---

## 📦 Dependências

Principais pacotes instalados:

| Pacote | Versão | Uso |
|--------|--------|-----|
| Flask | 3.1.1 | Framework web |
| MySQL-Connector | 9.5.0 | Conexão com MySQL |
| MySQLdb | 2.2.7 | Driver MySQL |
| WeasyPrint | - | Geração de PDF |
| Pandas | 2.3.1 | Processamento de dados |
| Gunicorn | 23.0.0 | Servidor WSGI |
| Flask-WTF | 1.2.2 | Formulários e CSRF |

Ver arquivo `requirements.txt` para lista completa.

---

## 🐳 Docker

### Estrutura de Containers

```
┌─────────────────────────────┐
│      nginx (port 80)        │  ← Entrada principal
└──────────────┬──────────────┘
               │
        ┌──────▼──────┐
        │ Flask App   │  ← Aplicação (port 5000)
        │ (Gunicorn)  │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │    MySQL    │  ← Banco de dados
        │ (port 3306) │
        └─────────────┘
```

### Comandos Docker Úteis

```bash
# Ver status dos containers
docker-compose ps

# Ver logs
docker-compose logs -f app

# Executar comando no container
docker-compose exec app bash

# Backup do banco
docker-compose exec mysql mysqldump -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DB > backup.sql

# Parar containers
docker-compose down

# Remover tudo (CUIDADO!)
docker-compose down -v
```

---

## 🗄️ Banco de Dados

### Inicialização

Os scripts SQL em `banco_dados/` são executados automaticamente na primeira execução do container MySQL.

### Backup Automático

```bash
# Executar backup manual
./backup.sh

# Ver backups criados
ls -lh backups/
```

Backups com mais de 30 dias são deletados automaticamente.

---

## 📊 Monitoramento

### Logs

```bash
# Logs em tempo real
docker-compose logs -f

# Últimas 50 linhas
docker-compose logs --tail 50

# Apenas da aplicação
docker-compose logs app

# Apenas do banco
docker-compose logs mysql
```

### Health Check

O aplicação possui health check configurado. Verifique com:

```bash
docker-compose ps
# Status "healthy" = tudo bem
```

---

## 🔐 Segurança

### Boas Práticas Implementadas

✅ Isolamento com Docker
✅ Variáveis de ambiente para credenciais
✅ HTTPS support (via nginx)
✅ Proteção contra SQL Injection
✅ CSRF Protection (Flask-WTF)
✅ Headers de segurança
✅ Rate limiting (nginx)
✅ Usuário não-root em containers
✅ Backup automático

### Checklist Pré-Deploy

- [ ] Arquivo `.env` com credenciais reais
- [ ] FLASK_SECRET_KEY alterada
- [ ] Banco de dados com senha forte
- [ ] Backup testado
- [ ] HTTPS/SSL configurado (produção)
- [ ] Firewall configurado
- [ ] Security check passou (python security_check.py)

---

## 🚢 Deploy em Produção

### Opção 1: Docker em VPS

Ver `DEPLOY.md` seção "Deploy em Produção" para instruções passo-a-passo.

### Opção 2: Heroku

```bash
# Instalar Heroku CLI
# Fazer login
heroku login

# Criar app
heroku create seu-app-name

# Configurar banco
heroku addons:create cleardb:ignite

# Setar variáveis
heroku config:set FLASK_ENV=production
heroku config:set FLASK_SECRET_KEY=<sua-chave>

# Deploy
git push heroku main
```

### Opção 3: AWS/Railway/DigitalOcean

Ver `DEPLOY.md` para instruções específicas de cada plataforma.

---

## 🐛 Troubleshooting

### Aplicação não inicia

```bash
# Ver logs detalhados
docker-compose logs app | tail -100

# Verificar se variáveis estão corretas
docker-compose config
```

### Erro de conexão com MySQL

```bash
# Verificar se MySQL está rodando
docker-compose ps

# Testar conexão
docker-compose exec app ping mysql

# Ver logs do MySQL
docker-compose logs mysql
```

### Porta em uso

```bash
# Qual processo está usando a porta?
lsof -i :80  # Linux/Mac
netstat -ano | findstr :80  # Windows

# Usar porta diferente
# Editar docker-compose.yml ou .env
```

Ver `DEPLOY.md` seção "Troubleshooting" para mais problemas comuns.

---

## 🤝 Suporte Técnico

Para dúvidas ou problemas:

1. Consulte a documentação em `DEPLOY.md`
2. Verifique os logs: `docker-compose logs -f`
3. Execute security check: `python security_check.py`
4. Contate o desenvolvedor: [seu-email@exemplo.com]

---

## 📝 Changelog

### v1.0.0 (2025-12-01)
- ✅ Setup inicial de deploy
- ✅ Configuração Docker completa
- ✅ Nginx com suporte a HTTPS
- ✅ Scripts de backup automático
- ✅ Verificador de segurança
- ✅ Documentação de deploy

---

## 📄 Licença

Proprietary - Todos os direitos reservados.

---

## 👨‍💼 Desenvolvido por

**Williams** - Consultoria de TI
- Website: [seu-website.com]
- Email: [seu-email@exemplo.com]

---

## 🎯 Próximas Melhorias

- [ ] Testes automatizados (pytest)
- [ ] CI/CD com GitHub Actions
- [ ] Monitoring com Prometheus/Grafana
- [ ] Cache com Redis
- [ ] Load balancing
- [ ] Multi-language support
- [ ] Mobile app

---

**Última atualização:** 1 de dezembro de 2025
