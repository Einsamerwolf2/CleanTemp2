@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto erro
)
.venv\Scripts\python.exe -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Preparando o CleanTemp pela primeira vez. E necessaria uma conexao com a internet.
  .venv\Scripts\python.exe -m pip install -r backend\requirements.txt
  if errorlevel 1 goto erro
)
.venv\Scripts\python.exe backend\desktop.py
pause
exit /b
:erro
echo Nao foi possivel abrir o CleanTemp. Verifique a instalacao do Python.
echo Na primeira utilizacao, conecte o computador a internet para concluir a preparacao.
pause
exit /b 1
