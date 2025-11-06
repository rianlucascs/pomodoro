@echo off
title Iniciando Aplicacao Streamlit...

REM Ir para o diretorio onde o script .bat esta
cd /d "%~dp0"

REM Verificar se a venv existe
if not exist ".venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual não encontrado.
    echo Crie com: python -m venv .venv
    pause
    exit /b
)

echo Ativando ambiente virtual...
call ".venv\Scripts\activate.bat"

echo Iniciando aplicacao Streamlit...
python -m streamlit run main.py

echo.
echo Aplicacao encerrada.
pause
