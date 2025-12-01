@echo off
REM Script de Deploy para Windows
REM NeuroEduca

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  NeuroEduca - Deploy Helper (Windows)
echo ========================================
echo.

REM Verificar se Docker está instalado
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Docker não encontrado!
    echo Instale em: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [OK] Docker encontrado

REM Verificar se Docker Compose está instalado
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Docker Compose não encontrado!
    pause
    exit /b 1
)

echo [OK] Docker Compose encontrado

REM Verificar arquivo .env
if not exist .env (
    echo [AVISO] Arquivo .env não encontrado
    if exist .env.example (
        echo Copiando .env.example para .env...
        copy .env.example .env
        echo [OK] .env criado - EDITE COM SUAS CREDENCIAIS!
        pause
    )
)

echo.
echo Escolha uma opção:
echo 1. Build e iniciar containers
echo 2. Parar containers
echo 3. Ver status
echo 4. Ver logs
echo 5. Backup do banco de dados
echo 6. Sair
echo.

set /p choice="Opção: "

if "%choice%"=="1" (
    echo.
    echo Iniciando build e deploy...
    docker-compose build
    docker-compose up -d
    echo.
    echo [OK] Containers iniciados!
    docker-compose ps
    echo.
    echo Acesse: http://localhost
    pause
) else if "%choice%"=="2" (
    echo.
    echo Parando containers...
    docker-compose down
    echo [OK] Containers parados!
    pause
) else if "%choice%"=="3" (
    echo.
    docker-compose ps
    pause
) else if "%choice%"=="4" (
    echo.
    docker-compose logs --tail 50
    pause
) else if "%choice%"=="5" (
    echo.
    REM Criar diretório de backup se não existir
    if not exist backups mkdir backups
    
    REM Backup do banco
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
    
    echo Criando backup...
    docker-compose exec -T mysql mysqldump -u%MYSQL_USER% -p%MYSQL_PASSWORD% %MYSQL_DB% | gzip > backups/backup_%mydate%_%mytime%.sql.gz
    echo [OK] Backup criado em: backups/backup_%mydate%_%mytime%.sql.gz
    pause
) else if "%choice%"=="6" (
    echo Saindo...
    exit /b 0
) else (
    echo Opção inválida!
    pause
)

endlocal
