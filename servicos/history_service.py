import sqlite3
import json
from datetime import datetime
import os

class HistoryService:
    DB_PATH = 'database/historico.db'
    
    def __init__(self):
        self._ensure_table()
        
    def _ensure_table(self):
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_calculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_calculo TEXT,
                tipo_guia TEXT,
                valor_principal TEXT,
                data_vencimento TEXT,
                data_pagamento TEXT,
                valor_total TEXT,
                detalhes_json TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
    def salvar_calculo(self, dados: dict):
        """
        dados espera chaves: tipo, principal, vencimento, pagamento, total, detalhes (dict)
        """
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO historico_calculos 
            (data_calculo, tipo_guia, valor_principal, data_vencimento, data_pagamento, valor_total, detalhes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            dados['tipo'],
            str(dados['principal']),
            dados['vencimento'], # str YYYY-MM-DD or DD/MM/AAAA provided by app
            dados['pagamento'],
            str(dados['total']),
            json.dumps(dados['detalhes'])
        ))
        
        conn.commit()
        conn.close()
        
    def obter_ultimos(self, limite=10):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM historico_calculos ORDER BY id DESC LIMIT ?', (limite,))
        rows = cursor.fetchall()
        
        conn.close()
        return rows
