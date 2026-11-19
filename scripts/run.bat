@echo off
setlocal

:: Cambiar al directorio raiz del proyecto
cd /d "%~dp0\.."

:: 1. Verificar si existe el entorno virtual
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual en .venv.
    echo Por favor ejecute primero el instalador:
    echo   scripts\install.bat
    echo.
    pause
    exit /b 1
)

:: 2. Activar entorno virtual
call .venv\Scripts\activate.bat

:: 3. Ejecutar el asistente
python main.py %*
if %errorlevel% neq 0 (
    echo.
    echo [AVISO] La ejecucion termino con codigo de error %errorlevel%.
    pause
)

