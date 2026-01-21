import requests
import sqlite3
from datetime import datetime, date
from decimal import Decimal
import os

class SelicService:
    API_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados"
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
        """Verifica se o cache precisa ser atualizado (ex: mais de 7 dias ou vazio)."""
        # Por simplicidade neste MVP, vamos tentar atualizar sempre que instanciado, 
        # mas respeitando um timer ou se falhar usa o que tem.
        # Implementação robusta usaria 'metadata' para guardar 'last_update'.
        
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # Check last update
        cursor.execute("SELECT valor FROM metadata WHERE chave = 'last_selic_update'")
        result = cursor.fetchone()
        
        should_update = True
        if result:
            last_update = datetime.fromisoformat(result[0])
            if (datetime.now() - last_update).days < 7:
                 should_update = False
        
        if should_update:
            try:
                print("Atualizando taxas SELIC...")
                # Pegar toda a série histórica ou um range razoável (ex: últimos 10 anos)
                # A API retorna JSON: [{"data": "DD/MM/AAAA", "valor": "0.0123"}, ...]
                response = requests.get(self.API_URL + "?formato=json")
                response.raise_for_status()
                dados = response.json()
                
                for item in dados:
                    # item['data'] é DD/MM/AAAA
                    # item['valor'] é string float (percentual diário? Não, a série 4390 é Selic ACUMULADA MENSAL não?
                    # Espere. README diz: "Juros: Taxa SELIC acumulada mês a mês + 1% no mês pagamento"
                    # Série 4390 é "Taxa de juros - Selic acumulada no mês anualizada base 252"? 
                    # Não, 4390 é "Taxa de juros - Selic acumulada no mês".
                    # Vamos verificar a série 4390 padrão. É percentual mensal.
                    
                    data_str = item['data'] # DD/MM/AAAA
                    try:
                         # Converter para YYYY-MM-DD para ordenação correta no banco
                         dt = datetime.strptime(data_str, "%d/%m/%Y").date()
                         iso_date = dt.strftime("%Y-%m-%d") # Guardar dia 01 do mês? A 4390 é mensal.
                         # O dado vem com data do dia 01 geralmente?
                         # A API 4390 retorna data "01/MM/AAAA".
                         
                         valor = item['valor']
                         cursor.execute("INSERT OR REPLACE INTO selic_cache (data, valor) VALUES (?, ?)", (iso_date, valor))
                    except ValueError:
                        continue

                cursor.execute("INSERT OR REPLACE INTO metadata (chave, valor) VALUES (?, ?)", 
                               ('last_selic_update', datetime.now().isoformat()))
                conn.commit()
                print("Taxas SELIC atualizadas.")
                
            except Exception as e:
                print(f"Erro ao atualizar SELIC: {e}")
                # Fallback: usar o que tem no banco
        
        conn.close()

    def obter_selic_acumulada(self, data_vencimento: date, data_pagamento: date) -> Decimal:
        """
        Calcula a SELIC acumulada entre o mês seguinte ao vencimento e o mês anterior ao pagamento.
        Regra Federal (Lei 9.430/96):
        - Juros equivalentes à taxa referecial do Sistema Especial de Liquidação e de Custódia (SELIC)
        para títulos federais, acumulada MENSALMENTE.
        - Calculados a partir do primeiro dia do mês subsequente ao vencimento do prazo.
        - Até o mês anterior ao do pagamento.
        - E de 1% no mês de pagamento.
        """
        self._atualizar_cache_se_necessario()
        
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        
        # Mês seguinte ao vencimento
        mes_inicio = date(data_vencimento.year, data_vencimento.month, 1)
        if mes_inicio.month == 12:
            mes_inicio = date(mes_inicio.year + 1, 1, 1)
        else:
            mes_inicio = date(mes_inicio.year, mes_inicio.month + 1, 1)
            
        # Mês anterior ao pagamento
        if data_pagamento.day == 1:
            # Se pagar dia 1, não cobra mês atual? A regra diz "1% no mês de pagamento".
            # Normalmente a regra é: Selic acumulada até mês anterior + 1%.
            pass
        
        mes_fim = date(data_pagamento.year, data_pagamento.month, 1)
        # O range é [mes_inicio, mes_fim).
        # Query: datas >= mes_inicio AND datas < mes_fim
        
        query = "SELECT valor FROM selic_cache WHERE data >= ? AND data < ?"
        cursor.execute(query, (mes_inicio.strftime("%Y-%m-%d"), mes_fim.strftime("%Y-%m-%d")))
        rows = cursor.fetchall()
        
        acumulado = Decimal('0.00')
        detalhamento = []
        
        for row in rows:
            # Valor na base é percentual (ex: "1.22" significa 1.22%)
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
