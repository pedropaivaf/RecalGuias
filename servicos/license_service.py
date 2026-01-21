"""
Sistema de Licenciamento - RecalGuias
Valida licenças online e offline (cache 7 dias)
"""
import requests
import hashlib
import platform
import uuid
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class LicenseService:
    """Gerencia validação de licença local e remota"""
    
    # ⚠️ CONFIGURAÇÃO - TROCAR ANTES DE COMPILAR
    # Desenvolvimento local:
    # API_URL = "http://localhost:5000/api"
    
    # Produção (PythonAnywhere):
    API_URL = "https://pedropython.pythonanywhere.com/api"
    
    CACHE_FILE = Path("database/license_cache.json")
    CACHE_VALIDADE_DIAS = 7
    
    def __init__(self):
        self.license_key = None
        self.hardware_id = self._get_hardware_id()
    
    def _get_hardware_id(self) -> str:
        """Gera ID único do hardware (UUID + Hostname + Processor)"""
        try:
            machine_id = uuid.UUID(int=uuid.getnode())
            hostname = platform.node()
            processor = platform.processor()
            raw = f"{machine_id}{hostname}{processor}"
            return hashlib.sha256(raw.encode()).hexdigest()[:32]
        except Exception:
            return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:32]
    
    def validar_online(self, chave_licenca: str) -> dict:
        """Valida licença com servidor"""
        try:
            response = requests.post(
                f"{self.API_URL}/validar",
                json={
                    "chave_licenca": chave_licenca,
                    "hardware_id": self.hardware_id
                },
                timeout=10
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('valida'):
                self._salvar_cache(chave_licenca, data)
                return {
                    'valida': True,
                    'mensagem': data.get('mensagem'),
                    'cliente_nome': data.get('cliente_nome'),
                    'online': True
                }
            else:
                return {
                    'valida': False,
                    'mensagem': data.get('mensagem', 'Licença inválida'),
                    'online': True
                }
        
        except requests.exceptions.RequestException:
            return self._validar_cache(chave_licenca)
    
    def _salvar_cache(self, chave: str, data: dict):
        """Salva cache local"""
        cache_data = {
            'chave_licenca': chave,
            'hardware_id': self.hardware_id,
            'valida': True,
            'cliente_nome': data.get('cliente_nome'),
            'timestamp': datetime.now().isoformat(),
            'expira_cache': (datetime.now() + timedelta(days=self.CACHE_VALIDADE_DIAS)).isoformat()
        }
        
        self.CACHE_FILE.parent.mkdir(exist_ok=True)
        with open(self.CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    
    def _validar_cache(self, chave: str) -> dict:
        """Valida modo offline"""
        if not self.CACHE_FILE.exists():
            return {
                'valida': False,
                'mensagem': 'Sem conexão e sem cache local',
                'online': False
            }
        
        try:
            with open(self.CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            if cache.get('chave_licenca') != chave:
                return {'valida': False, 'mensagem': 'Chave diferente', 'online': False}
            
            if cache.get('hardware_id') != self.hardware_id:
                return {'valida': False, 'mensagem': 'Hardware diferente', 'online': False}
            
            expira = datetime.fromisoformat(cache['expira_cache'])
            if datetime.now() > expira:
                return {
                    'valida': False,
                    'mensagem': 'Cache expirou. Conecte à internet.',
                    'online': False
                }
            
            dias_restantes = (expira - datetime.now()).days
            
            return {
                'valida': True,
                'mensagem': f'Modo offline - {dias_restantes} dias restantes',
                'cliente_nome': cache.get('cliente_nome'),
                'online': False,
                'dias_offline_restantes': dias_restantes
            }
        
        except Exception as e:
            return {'valida': False, 'mensagem': f'Erro no cache: {e}', 'online': False}
    
    def obter_chave_salva(self) -> str:
        """Retorna chave salva no cache"""
        if self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                return cache.get('chave_licenca')
            except:
                pass
        return None
    
    def limpar_cache(self):
        """Remove cache local"""
        if self.CACHE_FILE.exists():
            os.remove(self.CACHE_FILE)
