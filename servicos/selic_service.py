import sqlite3
from datetime import datetime, date
from decimal import Decimal
import os

class SelicService:
    DB_PATH = 'database/historico.db'
    
    def __init__(self):
        self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selic_cache (
                data TEXT PRIMARY KEY,
                valor TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _atualizar_cache_se_necessario(self):
        """
        Modo Offline: Não conecta à API.
        Apenas verifica se há dados. Em produção offline, os dados devem ser
        carregados via script administrativo ou arquivo de dump sql.
        """
        pass

    def obter_selic_acumulada(self, data_vencimento: date, data_pagamento: date) -> Decimal:
        """
        Calcula a SELIC acumulada entre o mês seguinte ao vencimento e o mês anterior ao pagamento.
        """
        # No updates in offline mode
        # self._atualizar_cache_se_necessario()
        
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        mes_inicio = date(data_vencimento.year, data_vencimento.month, 1)
        if mes_inicio.month == 12:
            mes_inicio = date(mes_inicio.year + 1, 1, 1)
        else:
            mes_inicio = date(mes_inicio.year, mes_inicio.month + 1, 1)
            
        mes_fim = date(data_pagamento.year, data_pagamento.month, 1)
        
        query = "SELECT valor FROM selic_cache WHERE data >= ? AND data < ?"
        cursor.execute(query, (mes_inicio.strftime("%Y-%m-%d"), mes_fim.strftime("%Y-%m-%d")))
        rows = cursor.fetchall()
        
        acumulado = Decimal('0.00')
        
        for row in rows:
            val = Decimal(row[0])
            acumulado += val
        
        conn.close()
        
        return acumulado

    def list_all(self):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM selic_cache ORDER BY data DESC LIMIT 10")
        for r in cursor.fetchall():
            print(r)
        conn.close()
