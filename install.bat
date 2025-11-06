@echo off
echo ========================================
echo   Zentrada Processor - Instalare
echo ========================================
echo.

REM Verifică dacă Python este instalat
python --version >nul 2>&1
if errorlevel 1 (
    echo [EROARE] Python nu este instalat!
    echo.
    echo Te rog instaleaza Python de la:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: La instalare, bifeaza "Add Python to PATH"!
    echo.
    pause
    exit /b 1
)

echo [OK] Python este instalat
python --version
echo.

echo [INFO] Instalez dependentele...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [EROARE] Instalarea dependentelor a esuat!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Instalare Finalizata cu Succes!
echo ========================================
echo.
echo Pentru a porni aplicatia, ruleaza:
echo   start_app.bat
echo.
echo SAU din Command Prompt:
echo   python main_app.py
echo.
pause