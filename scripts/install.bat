@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo   Instalacion del Asistente Moodle + Gemini (Windows)
echo ====================================================

:: Cambiar al directorio raiz del proyecto
cd /d "%~dp0\.."

:: 1. Verificar si Python esta instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no se encuentra en el PATH.
    echo Por favor descargue e instale Python 3.11 o superior desde:
    echo   https://www.python.org/downloads/
    echo IMPORTANTE: Durante la instalacion, asegurese de marcar la casilla:
    echo   "Add python.exe to PATH"
    pause
    exit /b 1
)

:: 2. Verificar version de Python (requiere 3.11 o superior)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Se requiere Python 3.11 o superior.
    echo Version actual instalada:
    python --version
    echo Por favor actualice Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python detectado correctamente.

:: 3. Crear entorno virtual si no existe
if not exist ".venv" (
    echo [INFO] Creando entorno virtual en .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo al crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo [OK] Entorno virtual .venv existente.
)

:: 4. Activar entorno virtual
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

:: 5. Actualizar pip e instalar dependencias
echo [INFO] Actualizando pip...
python -m pip install --upgrade pip --quiet

echo [INFO] Instalando dependencias de Python (requirements.txt)...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar dependencias de requirements.txt.
    pause
    exit /b 1
)

:: 6. Deteccion de Google Chrome oficial
echo [INFO] Verificando instalacion de Google Chrome oficial...
set "CHROME_FOUND=0"

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_FOUND=1"

if "%CHROME_FOUND%"=="1" (
    echo [OK] Google Chrome oficial detectado en el sistema.
) else (
    echo [ADVERTENCIA] No se encontro Google Chrome en las rutas predeterminadas de Windows.
    echo El asistente requiere Google Chrome oficial. Descarguelo e instale desde:
    echo   https://www.google.com/chrome/
)

:: 7. Crear archivo de configuracion .env si no existe
if not exist ".env" (
    echo [INFO] Creando archivo .env a partir de .env.example...
    copy .env.example .env >nul
    echo [ATENCION] Se creo el archivo .env. Debes configurarlo con tu GEMINI_API_KEY.
) else (
    echo [OK] Archivo .env ya presente.
)

echo ====================================================
echo   Instalacion completada con exito en Windows!
echo ====================================================
echo Pasos siguientes:
echo   1. Abra el archivo .env con el Bloc de notas y coloque su GEMINI_API_KEY:
echo      notepad .env
echo   2. Ejecute el asistente haciendo doble clic en scripts\run.bat
echo      o desde la terminal con: scripts\run.bat
echo ====================================================

pause

