@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
if exist ".venv-x86\Scripts\python.exe" goto run32
if exist ".venv-x64\Scripts\python.exe" goto run64
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3.12-64 -m venv .venv
if not errorlevel 1 goto install
py -3.10-32 -m venv .venv
if errorlevel 1 goto failed
goto install
:usepython
python -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -c "import struct,sys; sys.exit(0 if struct.calcsize('P') == 4 else 1)"
if errorlevel 1 goto install64
".venv\Scripts\python.exe" -m pip install -r requirements-windows-x86.txt
if errorlevel 1 goto failed
goto run
:install64
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:run
".venv\Scripts\python.exe" main.py %*
if errorlevel 1 goto failed
exit /b 0
:run32
".venv-x86\Scripts\python.exe" main.py %*
if errorlevel 1 goto failed
exit /b 0
:run64
".venv-x64\Scripts\python.exe" main.py %*
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Nao foi possivel iniciar. Use Python 3.12 de 64 bits ou Python 3.10 de 32 bits.
echo O instalador final dispensa a instalacao de Python.
pause
exit /b 1
