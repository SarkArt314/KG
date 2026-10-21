@echo off
chcp 65001 >nul

echo ============================================
echo   Сборка .exe для лабораторной работы 2
echo ============================================

python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name Lab2_ImageProcessing ^
    --hidden-import PIL._tkinter_finder ^
    main.py
if errorlevel 1 exit /b 1

echo Готово: dist\Lab2_ImageProcessing.exe
pause
