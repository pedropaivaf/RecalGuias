@echo off
echo Iniciando RecalGuias...
echo Verificando dependencias basicas...
pip install requests packaging pillow
echo.
echo Iniciando aplicacao...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Ocorreu um erro ao executar a aplicacao.
    pause
)
