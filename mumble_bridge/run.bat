@echo off
cd /d "%~dp0"
chcp 65001 >nul
echo ==========================================
echo   Let's Role - Spatial Audio - Pont Mumble
echo ==========================================
echo.

:: Vérification Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo Telecharge Python sur https://www.python.org/downloads/
    echo Coche bien "Add Python to PATH" lors de l'installation.
    pause
    exit /b 1
)

:: Installation des dependances si nécessaire
echo Installation des dependances...
python -m pip install websockets --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [ERREUR] Impossible d'installer les dependances.
    pause
    exit /b 1
)

echo.
echo Demarrage du pont Mumble...
echo.
python mumble_bridge.py

pause
