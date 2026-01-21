@echo off
echo ================================
echo  SERVIDOR DE LICENCAS
echo ================================
echo.
echo Instalando dependencias...
pip install -r requirements.txt
echo.
echo Iniciando servidor...
echo Painel: http://localhost:5000/admin
echo.
python app.py
pause
