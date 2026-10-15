@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1"
if errorlevel 1 (
  echo.
  echo Confira o erro acima. Este computador precisa dos dois Pythons e do Inno Setup.
  pause
  exit /b 1
)
echo.
echo Instaladores prontos na pasta output.
explorer "%~dp0output"
pause
