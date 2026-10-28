@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo Установка зависимостей...
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Сборка exe...
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name RasterLab3 --collect-submodules raster_lab main.py
if errorlevel 1 goto :error

if not exist "dist\RasterLab3.exe" goto :error
echo Готово. Файл находится в папке dist\RasterLab3.exe
exit /b 0

:error
echo Ошибка сборки. Проверьте сообщения выше.
exit /b 1
