@echo off
echo Iniciando RecalGuias (OFFLINE MODE)...
echo Verificando dependencias...
pip install -r requirements.txt
echo.
echo Iniciando aplicacao...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Ocorreu um erro ao executar a aplicacao.
    pause
)
