#!/usr/bin/env python3
"""
Script de inicialização e validação para deploy do NeuroEduca
Valida configurações, prepara ambiente e facilita deploy
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

# Cores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"{text.center(60)}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_ok(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def run_command(cmd, show_output=False):
    """Executa comando e retorna sucesso/erro"""
    try:
        if show_output:
            result = subprocess.run(cmd, shell=True, check=True)
        else:
            result = subprocess.run(cmd, shell=True, check=True, 
                                  capture_output=True, text=True)
        return True, result.stdout if hasattr(result, 'stdout') else ""
    except subprocess.CalledProcessError as e:
        return False, str(e)

def check_docker():
    """Verifica se Docker está instalado"""
    print_info("Verificando Docker...")
    success, _ = run_command("docker --version")
    if success:
        print_ok("Docker encontrado")
        return True
    else:
        print_error("Docker não encontrado. Instale em: https://www.docker.com")
        return False

def check_docker_compose():
    """Verifica se Docker Compose está instalado"""
    print_info("Verificando Docker Compose...")
    success, _ = run_command("docker-compose --version")
    if success:
        print_ok("Docker Compose encontrado")
        return True
    else:
        print_error("Docker Compose não encontrado")
        return False

def check_env_file():
    """Verifica se arquivo .env existe"""
    print_info("Verificando arquivo .env...")
    if os.path.exists('.env'):
        print_ok("Arquivo .env encontrado")
        return True
    else:
        print_warning("Arquivo .env não encontrado")
        if os.path.exists('.env.example'):
            print_info("Criando .env a partir de .env.example...")
            run_command("cp .env.example .env")
            print_ok("Arquivo .env criado. Edite-o com suas credenciais!")
            return False
        return False

def validate_env_vars():
    """Valida variáveis críticas de ambiente"""
    print_info("Validando variáveis de ambiente...")
    load_dotenv()
    
    required_vars = [
        'FLASK_SECRET_KEY',
        'MYSQL_USER',
        'MYSQL_PASSWORD',
        'MYSQL_DB'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('seu_'):
            missing.append(var)
    
    if missing:
        print_error(f"Variáveis não configuradas: {', '.join(missing)}")
        print_info("Edite o arquivo .env com as configurações reais")
        return False
    
    print_ok("Variáveis de ambiente validadas")
    return True

def check_ports():
    """Verifica portas que serão usadas"""
    print_info("Verificando portas...")
    
    ports = {
        '80': 'HTTP (Nginx)',
        '3306': 'MySQL',
        '5000': 'Flask App',
        '9000': 'Portainer (opcional)'
    }
    
    for port, service in ports.items():
        # Comando diferente para Windows/Linux
        cmd = f"netstat -an | findstr :{port}" if sys.platform == 'win32' \
              else f"lsof -i :{port}"
        
        success, output = run_command(cmd)
        if success and output:
            print_warning(f"Porta {port} ({service}) pode estar em uso")
        else:
            print_ok(f"Porta {port} ({service}) disponível")

def build_images():
    """Build das imagens Docker"""
    print_header("Build das Imagens Docker")
    print_info("Isso pode levar alguns minutos...")
    
    success, output = run_command("docker-compose build", show_output=True)
    if success:
        print_ok("Imagens construídas com sucesso")
        return True
    else:
        print_error("Erro ao construir imagens")
        print(output)
        return False

def start_containers():
    """Inicia containers"""
    print_header("Iniciando Containers")
    
    success, output = run_command("docker-compose up -d", show_output=True)
    if success:
        print_ok("Containers iniciados")
        return True
    else:
        print_error("Erro ao iniciar containers")
        print(output)
        return False

def wait_for_health():
    """Aguarda containers ficarem saudáveis"""
    print_info("Aguardando containers ficarem saudáveis (máx 60s)...")
    
    import time
    for i in range(30):
        success, output = run_command("docker-compose ps")
        if success and 'healthy' in output.lower():
            print_ok("Todos os serviços estão saudáveis")
            return True
        time.sleep(2)
        print(".", end="", flush=True)
    
    print_warning("Timeout ao aguardar saúde dos containers")
    return False

def show_status():
    """Mostra status dos containers"""
    print_header("Status dos Containers")
    run_command("docker-compose ps", show_output=True)

def show_logs():
    """Mostra logs dos containers"""
    print_header("Últimos logs (últimas 20 linhas)")
    run_command("docker-compose logs --tail 20", show_output=True)

def create_backup_script():
    """Cria script de backup"""
    print_info("Criando script de backup...")
    
    script_content = '''#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker-compose exec -T mysql mysqldump -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DB | gzip > $BACKUP_DIR/backup_${DATE}.sql.gz
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
echo "Backup criado: $BACKUP_DIR/backup_${DATE}.sql.gz"
'''
    
    with open('backup.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('backup.sh', 0o755)
    print_ok("Script de backup criado: backup.sh")

def validate_requirements():
    """Valida arquivo requirements.txt"""
    print_info("Validando requirements.txt...")
    
    if os.path.exists('requirements.txt'):
        print_ok("requirements.txt encontrado")
        with open('requirements.txt', 'r') as f:
            lines = len(f.readlines())
        print_info(f"Total de dependências: {lines}")
        return True
    else:
        print_error("requirements.txt não encontrado")
        return False

def main():
    """Função principal"""
    print_header("NeuroEduca - Deploy Validator & Setup")
    
    # Pre-flight checks
    print_header("Pre-Flight Checks")
    
    checks = [
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("Arquivo .env", check_env_file),
        ("requirements.txt", validate_requirements),
    ]
    
    all_passed = True
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print_error(f"Erro ao verificar {name}: {str(e)}")
            all_passed = False
    
    if not all_passed:
        print_error("\nAlguns pré-requisitos não foram atendidos!")
        sys.exit(1)
    
    # Validar variáveis de ambiente
    if not validate_env_vars():
        print_warning("\nConfigure o arquivo .env e execute novamente")
        sys.exit(1)
    
    # Verificar portas
    check_ports()
    
    # Menu de opções
    print_header("Menu de Deploy")
    print("""
    1. Validar configurações apenas
    2. Build das imagens Docker
    3. Iniciar containers
    4. Build + Iniciar (Deploy completo)
    5. Ver status dos containers
    6. Ver logs
    7. Criar script de backup
    8. Sair
    """)
    
    choice = input("Escolha uma opção (1-8): ").strip()
    
    if choice == '1':
        print_ok("Validação concluída com sucesso!")
    elif choice == '2':
        build_images()
    elif choice == '3':
        start_containers()
        wait_for_health()
        show_status()
    elif choice == '4':
        if build_images() and start_containers():
            wait_for_health()
            show_status()
            create_backup_script()
            print_header("🎉 Deploy Concluído com Sucesso!")
            print_info(f"Acesse: http://localhost")
            print_info("Para parar: docker-compose down")
            print_info("Para ver logs: docker-compose logs -f")
    elif choice == '5':
        show_status()
    elif choice == '6':
        show_logs()
    elif choice == '7':
        create_backup_script()
    elif choice == '8':
        print("Até logo!")
        sys.exit(0)
    else:
        print_error("Opção inválida!")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\nOperação cancelada pelo usuário")
        sys.exit(0)
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        sys.exit(1)
