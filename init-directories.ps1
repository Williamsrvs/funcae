# Script para inicializar estrutura de diretórios no Windows
# Execute: .\init-directories.ps1

Write-Host "Inicializando estrutura de diretórios..." -ForegroundColor Green
Write-Host ""

# Função auxiliar para criar diretório e arquivo .gitkeep
function Create-Directory {
    param([string]$Path)
    
    if (-not (Test-Path -Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "✓ Diretório '$Path' criado" -ForegroundColor Green
    } else {
        Write-Host "✓ Diretório '$Path' já existe" -ForegroundColor Yellow
    }
    
    # Criar arquivo .gitkeep se não existir
    $gitkeep = Join-Path -Path $Path -ChildPath ".gitkeep"
    if (-not (Test-Path -Path $gitkeep)) {
        New-Item -ItemType File -Path $gitkeep -Force | Out-Null
    }
}

# Criar diretórios de logs
Create-Directory "logs"
if (-not (Test-Path "logs/app.log")) {
    New-Item -ItemType File -Path "logs/app.log" -Force | Out-Null
}

# Criar diretório de uploads
Create-Directory "app\static\uploads"

# Criar diretório de backups
Create-Directory "backups"

# Criar diretório de SSL
Create-Directory "ssl"
Create-Directory "ssl\test-certs"

Write-Host ""
Write-Host "✓ Estrutura de diretórios inicializada com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Copiar .env.example para .env"
Write-Host "2. Editar .env com suas credenciais"
Write-Host "3. Executar: python security_check.py"
Write-Host "4. Fazer deploy: docker-compose up -d"
Write-Host ""
