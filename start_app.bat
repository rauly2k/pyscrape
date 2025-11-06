@echo off
echo ========================================
echo   Zentrada Processor
echo ========================================
echo.
echo Pornesc aplicatia...
echo.

python main_app.py

if errorlevel 1 (
    echo.
    echo [EROARE] Aplicatia a intampinat o problema!
    echo.
    echo Verifica ca ai instalat dependentele cu:
    echo   install.bat
    echo.
    pause
)