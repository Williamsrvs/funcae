"""
Configuração centralizada do NeuroEduca
Gerencia diferentes ambientes (development, staging, production)
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


class Config:
    """Configurações base para todos os ambientes"""
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Banco de dados
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB')
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Servidor
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 5000))
    
    # Segurança
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Upload de arquivos
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))  # 50MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xls', 'xlsx', 'doc', 'docx'}
    
    # Logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')


class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class StagingConfig(Config):
    """Configurações para staging/testes"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # Validação de configurações críticas
    def __init__(self):
        """Valida configurações críticas para produção"""
        required_vars = ['MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB', 'MYSQL_HOST']
        missing = [var for var in required_vars if not getattr(self, var, None)]
        if missing:
            raise ValueError(f"Variáveis de ambiente obrigatórias em produção: {', '.join(missing)}")
        
        if self.SECRET_KEY == 'dev-key-change-in-production':
            raise ValueError("FLASK_SECRET_KEY não deve ser a chave padrão em produção!")


class TestingConfig(Config):
    """Configurações para testes automatizados"""
    DEBUG = True
    TESTING = True
    MYSQL_DB = 'test_db_funcae'


def get_config(env=None):
    """
    Retorna a configuração apropriada baseada no ambiente
    
    Args:
        env: Nome do ambiente ('development', 'staging', 'production', 'testing')
             Se None, usa a variável FLASK_ENV ou padrão para desenvolvimento
    
    Returns:
        Classe de configuração apropriada
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development').lower()
    
    config_map = {
        'development': DevelopmentConfig,
        'staging': StagingConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    
    if env not in config_map:
        raise ValueError(f"Ambiente inválido: {env}. Use: {', '.join(config_map.keys())}")
    
    return config_map[env]()
