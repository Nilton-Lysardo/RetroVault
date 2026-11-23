@echo off
title RetroVault - Gerenciador de ROMs
cd /d "%~dp0"

:: Verificar se já está rodando na porta 8080
powershell -Command "$c = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue; if ($c) { Start-Process 'http://localhost:8080'; exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] RetroVault ja esta aberto em segundo plano. Abrindo no navegador...
    exit /b 0
)

:: Se o ambiente virtual nao existir, inicializa
if not exist "backend\venv" (
    echo [INFO] Criando ambiente virtual...
    python -m venv backend\venv
    call backend\venv\Scripts\activate.bat
    pip install -r backend\requirements.txt
)

if not exist "data\covers" mkdir "data\covers"

echo.
echo  =============================================
echo    RetroVault - Gerenciador de ROMs
echo  =============================================
echo.
echo [INFO] Iniciando servidor RetroVault...
echo [INFO] Acesse: http://localhost:8080
echo [INFO] Minimize esta janela enquanto estiver jogando.
echo.

:: Abrir navegador apos 2 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8080"

:: Iniciar servidor usando o Python do ambiente virtual
backend\venv\Scripts\python.exe backend\server.py
