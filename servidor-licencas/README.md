# 🔐 Servidor de Licenciamento

## Rodar Local
```bash
pip install -r requirements.txt
python app.py
```

Acesse: http://localhost:5000/admin

## Deploy PythonAnywhere (GRÁTIS)

1. Criar conta: pythonanywhere.com
2. Upload desta pasta
3. Criar Web App Flask
4. Configurar WSGI:
```python
import sys
path = '/home/seuusuario/servidor-licencas'
sys.path.append(path)
from app import app as application
```

5. Reload

URL: https://seuusuario.pythonanywhere.com

## Uso

1. Acessar /admin
2. Criar licença
3. Enviar chave ao cliente
4. Cliente insere no app
5. Bloquear quando necessário
