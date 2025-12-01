#!/usr/bin/env python3
"""
Checklist de Segurança para Deploy do NeuroEduca
Verifica vulnerabilidades comuns e boas práticas
"""

import os
import re
import sys
from pathlib import Path

class SecurityChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def check_hardcoded_credentials(self):
        """Verifica credenciais hardcoded no código"""
        print("Verificando credenciais hardcoded...")
        
        patterns = [
            (r'password\s*=\s*["\'](?!<|{)[\w@!#$%^&*]{8,}', 'Senha possível hardcoded'),
            (r'api[_-]?key\s*=\s*["\'][a-zA-Z0-9]{20,}', 'API Key possível hardcoded'),
            (r'secret\s*=\s*["\'][\w\-]{20,}', 'Secret possível hardcoded'),
        ]
        
        files_to_check = [
            'app/app.py',
            'app/login.py',
            'config.py'
        ]
        
        found_issues = False
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    for i, line in enumerate(f, 1):
                        for pattern, msg in patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                self.issues.append(f"{file_path}:{i} - {msg}")
                                found_issues = True
        
        if not found_issues:
            self.passed.append("Nenhuma credencial hardcoded detectada")
        
        return not found_issues
    
    def check_env_file(self):
        """Verifica se .env está configurado"""
        print("Verificando arquivo .env...")
        
        if not os.path.exists('.env'):
            self.warnings.append("Arquivo .env não encontrado")
            return False
        
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                content = f.read()
            
            # Verificar se ainda tem valores placeholder
            if 'seu_' in content or '<' in content or '{' in content:
                self.issues.append(".env contém placeholders (seu_*, <...>, {...})")
                return False
            
            self.passed.append(".env configurado corretamente")
            return True
    
    def check_gitignore(self):
        """Verifica se .gitignore exclui arquivos sensíveis"""
        print("Verificando .gitignore...")
        
        if not os.path.exists('.gitignore'):
            self.issues.append(".gitignore não encontrado")
            return False
        
        sensitive_patterns = ['.env', '*.pem', '*.key', '*.sql', 'logs/']
        
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
        
        missing = []
        for pattern in sensitive_patterns:
            if pattern not in gitignore_content:
                missing.append(pattern)
        
        if missing:
            self.warnings.append(f".gitignore deveria incluir: {', '.join(missing)}")
            return False
        
        self.passed.append(".gitignore configurado corretamente")
        return True
    
    def check_flask_debug(self):
        """Verifica se DEBUG está desligado em produção"""
        print("Verificando modo DEBUG...")
        
        if os.path.exists('app/app.py'):
            with open('app/app.py', 'r') as f:
                content = f.read()
            
            # Verificar debug hardcoded
            if re.search(r'app\.run\([^)]*debug\s*=\s*True', content):
                self.issues.append("app.run() com debug=True pode estar em produção")
                return False
            
            # Usar variáveis de ambiente é bom
            if 'os.getenv' in content and 'FLASK_ENV' in content:
                self.passed.append("Modo DEBUG controlado por variável de ambiente")
                return True
        
        return True
    
    def check_requirements_pinned(self):
        """Verifica se requirements.txt tem versões fixadas"""
        print("Verificando versões fixadas em requirements.txt...")
        
        if not os.path.exists('requirements.txt'):
            self.warnings.append("requirements.txt não encontrado")
            return False
        
        unpinned = []
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if not any(op in line for op in ['==', '~=', '>=']  if '==' in line):
                        if '==' not in line:
                            unpinned.append(line.split()[0] if line.split() else line)
        
        if unpinned:
            self.warnings.append(f"Dependências sem versão fixada (use ==): {', '.join(unpinned[:5])}")
        else:
            self.passed.append("Todas as dependências têm versão fixada")
        
        return True
    
    def check_sql_injection(self):
        """Verifica práticas seguras de SQL"""
        print("Verificando vulnerabilidades de SQL Injection...")
        
        dangerous_patterns = [
            (r'cursor\.execute\(["\'].*\{.*\}.*["\']\.format', 'Possível SQL Injection com format()'),
            (r'cursor\.execute\(["\'].*f["\']', 'Possível SQL Injection com f-string'),
            (r'cursor\.execute\(["\'][^"\']*\+[^"\']*["\']', 'Possível SQL Injection com concatenação'),
        ]
        
        py_files = list(Path('app').rglob('*.py'))
        found_issues = False
        
        for py_file in py_files:
            with open(py_file, 'r') as f:
                for i, line in enumerate(f, 1):
                    for pattern, msg in dangerous_patterns:
                        if re.search(pattern, line):
                            self.issues.append(f"{py_file}:{i} - {msg}")
                            found_issues = True
        
        if not found_issues:
            self.passed.append("Nenhum padrão de SQL Injection detectado")
        
        return not found_issues
    
    def check_docker_security(self):
        """Verifica segurança do Dockerfile"""
        print("Verificando Dockerfile...")
        
        if not os.path.exists('Dockerfile'):
            self.warnings.append("Dockerfile não encontrado")
            return False
        
        with open('Dockerfile', 'r') as f:
            dockerfile = f.read()
        
        checks = {
            'FROM python:3.11-slim' in dockerfile: "Imagem base slim (bom)",
            'useradd' in dockerfile: "Usuário não-root criado (bom)",
            'HEALTHCHECK' in dockerfile: "Health check configurado (bom)",
            'apt-get clean' in dockerfile or 'rm -rf /var/lib/apt' in dockerfile: "Cache apt limpo (bom)",
        }
        
        for check, msg in checks.items():
            if check:
                self.passed.append(msg)
            else:
                self.warnings.append(msg)
        
        return True
    
    def check_nginx_security(self):
        """Verifica configuração de segurança do Nginx"""
        print("Verificando nginx.conf...")
        
        if not os.path.exists('nginx.conf'):
            self.warnings.append("nginx.conf não encontrado")
            return False
        
        with open('nginx.conf', 'r') as f:
            nginx_conf = f.read()
        
        security_headers = [
            ('X-Frame-Options', 'Proteção contra Clickjacking'),
            ('X-Content-Type-Options', 'Proteção contra MIME sniffing'),
            ('X-XSS-Protection', 'Proteção XSS'),
        ]
        
        for header, desc in security_headers:
            if header in nginx_conf:
                self.passed.append(f"Header {header} configurado ({desc})")
            else:
                self.warnings.append(f"Header {header} não configurado ({desc})")
        
        return True
    
    def check_database_config(self):
        """Verifica segurança da configuração do banco"""
        print("Verificando configuração do banco de dados...")
        
        if os.path.exists('docker-compose.yml'):
            with open('docker-compose.yml', 'r') as f:
                compose = f.read()
            
            if 'MYSQL_ROOT_PASSWORD' in compose:
                self.passed.append("Root password configurado no docker-compose")
            else:
                self.warnings.append("Root password não explícito no docker-compose")
        
        return True
    
    def check_backup_strategy(self):
        """Verifica se há estratégia de backup"""
        print("Verificando estratégia de backup...")
        
        if os.path.exists('backup.sh'):
            self.passed.append("Script de backup encontrado")
        elif os.path.exists('deploy.py'):
            self.passed.append("Deploy.py com suporte a backup")
        else:
            self.warnings.append("Nenhum script de backup automatizado encontrado")
        
        return True
    
    def run_all_checks(self):
        """Executa todos os checks"""
        print("=" * 60)
        print("NeuroEduca - Security Checker".center(60))
        print("=" * 60)
        print()
        
        self.check_env_file()
        self.check_hardcoded_credentials()
        self.check_gitignore()
        self.check_flask_debug()
        self.check_requirements_pinned()
        self.check_sql_injection()
        self.check_docker_security()
        self.check_nginx_security()
        self.check_database_config()
        self.check_backup_strategy()
        
        self.print_results()
    
    def print_results(self):
        """Imprime resultados"""
        print()
        print("=" * 60)
        print("RESULTADOS".center(60))
        print("=" * 60)
        
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)}):")
            for item in self.passed:
                print(f"   ✓ {item}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for item in self.warnings:
                print(f"   ⚠ {item}")
        
        if self.issues:
            print(f"\n❌ ISSUES ({len(self.issues)}):")
            for item in self.issues:
                print(f"   ✗ {item}")
        
        print("\n" + "=" * 60)
        
        if self.issues:
            print("RESULTADO: ❌ FALHOU - Corrija os issues acima")
            return 1
        elif self.warnings:
            print("RESULTADO: ⚠️  COM AVISOS - Revise os warnings")
            return 2
        else:
            print("RESULTADO: ✅ PASSOU - Pronto para deploy!")
            return 0

if __name__ == '__main__':
    checker = SecurityChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)
