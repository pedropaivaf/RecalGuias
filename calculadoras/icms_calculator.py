from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Dict
import sys
import os
from functools import partial

# Ensure import of sibling modules works
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from servicos.selic_service import SelicService

class CalculadoraICMS:
    """ICMS-SP: Faixas 2%/5%/10% + SELIC"""
    
    def __init__(self):
        self.selic_service = SelicService()
    
    def calcular_mg(self, principal: Decimal, vencimento: date,
                    pagamento: date) -> Dict:
        """Minas Gerais: 0.15%/dia até 30d, depois faixas"""
        dias = (pagamento - vencimento).days
        
        if dias <= 0:
            return self._retorno_padrao('MG', principal)
        
        # Multa MG
        if dias <= 30:
            perc_multa = min(Decimal('0.0015') * dias, Decimal('0.045'))  # 0.15%/dia, máx 4.5%
        elif dias <= 60:
            perc_multa = Decimal('0.09')  # 9%
        else:
            perc_multa = Decimal('0.12')  # 12%
        
        multa = principal * perc_multa
        
        # Juros SELIC (MG sem +1% adicional? Prompt diz "Todos: juros = SELIC + 1%" na fase 2, 
        # mas na fase 3 diz "Juros SELIC (sem +1% adicional em MG)". Seguir fase 3.
        # SelicService volta sum().
        selic_acum = self.selic_service.obter_selic_acumulada(vencimento, pagamento)
        
        juros = principal * (selic_acum / 100)
        
        return self._formatar_resposta('MG', principal, dias, perc_multa, multa, selic_acum, juros)

    def calcular_rj(self, principal: Decimal, vencimento: date,
                    pagamento: date) -> Dict:
        """Rio de Janeiro: 0.33%/dia + SELIC + 1%"""
        # Igual ao padrão federal
        return self._calcular_padrao_033(principal, vencimento, pagamento, 'RJ')

    def calcular_sc(self, principal: Decimal, vencimento: date,
                    pagamento: date) -> Dict:
        """Santa Catarina: 0.30%/dia + SELIC + 1%"""
        dias = (pagamento - vencimento).days
        
        if dias <= 0:
            return self._retorno_padrao('SC', principal)
        
        # Multa SC: 0.30%/dia limited to 20%
        perc_multa = min(Decimal('0.003') * dias, Decimal('0.20'))
        multa = principal * perc_multa
        
        # Juros SELIC + 1%
        selic_acum = self.selic_service.obter_selic_acumulada(vencimento, pagamento) + Decimal('1.00')
        juros = principal * (selic_acum / 100)
        
        return self._formatar_resposta('SC', principal, dias, perc_multa, multa, selic_acum, juros)

    def calcular(self, estado: str, principal: Decimal, 
                 vencimento: date, pagamento: date) -> Dict:
        """Dispatcher por estado"""
        # Specific implementations
        calculadoras_especificas = {
            'SP': self.calcular_sp,
            'MG': self.calcular_mg,
            'SC': self.calcular_sc,
        }
        
        # Default for others (RJ, PR, RS, etc usually follow 0.33%/day or similar standard)
        # Using the standard 0.33%/day limit 20% + Selic + 1%
        calc_func = calculadoras_especificas.get(estado, partial(self._calcular_padrao_033, estado=estado))
        
        # Determine if we need to pass 'estado' to the specific functions?
        # The specific functions don't take 'estado' as arg in their signature (except _calcular_padrao_033).
        # We need to handle the calling signature correctly.
        
        if estado in calculadoras_especificas:
            return calculadoras_especificas[estado](principal, vencimento, pagamento)
        else:
            return self._calcular_padrao_033(principal, vencimento, pagamento, estado)

    def _calcular_padrao_033(self, principal, vencimento, pagamento, estado):
        """
        Regra Geral (ex: RJ, RS, PR, etc):
        - Multa: 0.33% ao dia, limitada a 20%.
        - Juros: SELIC acumulada + 1%.
        """
        dias = (pagamento - vencimento).days
        if dias <= 0: return self._retorno_padrao(estado, principal)
        
        # 0.33% / dia limit 20%
        perc_multa = min(Decimal('0.0033') * dias, Decimal('0.20'))
        multa = principal * perc_multa
        
        # Selic + 1%
        selic_acum = self.selic_service.obter_selic_acumulada(vencimento, pagamento) + Decimal('1.00')
        juros = principal * (selic_acum / 100)
        
        return self._formatar_resposta(estado, principal, dias, perc_multa, multa, selic_acum, juros)

    def _retorno_padrao(self, estado, principal):
        return {
            'estado': estado,
            'principal': principal,
            'status': 'EM DIA', 
            'dias_atraso': 0,
            'multa_perc': '0%',
            'multa_valor': Decimal('0.00'),
            'juros_selic_acum': '0%',
            'juros_valor': Decimal('0.00'),
            'total': principal
        }
        
    def _formatar_resposta(self, estado, principal, dias, perc_multa, multa, perc_juros, juros):
        multa = multa.quantize(Decimal('0.01'), ROUND_HALF_UP)
        juros = juros.quantize(Decimal('0.01'), ROUND_HALF_UP)
        total = principal + multa + juros
        
        # Format perc strings
        if isinstance(perc_multa, Decimal):
            p_multa_str = f"{perc_multa * 100:.2f}%"
        else:
            p_multa_str = str(perc_multa)
            
        if isinstance(perc_juros, Decimal):
            p_juros_str = f"{perc_juros:.2f}%"
        else:
            p_juros_str = str(perc_juros)

        return {
            'estado': estado,
            'principal': principal,
            'dias_atraso': dias,
            'multa_perc': p_multa_str,
            'multa_valor': multa,
            'juros_selic_acum': p_juros_str,
            'juros_valor': juros,
            'total': total
        }
