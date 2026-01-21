from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Dict
import requests

class CalculadoraFGTS:
    """
    FGTS: Correção TR + Juros 0.5%/mês + Multa 5% ou 10%
    Ordem: Principal → TR → Juros → Multa
    """
    
    ALIQUOTA = Decimal('0.08')
    JUROS_MENSAL = Decimal('0.005')
    MULTA_MES_VENC = Decimal('0.05')
    MULTA_APOS_VENC = Decimal('0.10')
    
    # Tabela TR (atualizar manualmente - CAIXA publica mensalmente)
    # Mockada para Phase 2 demo conforme prompt
    TABELA_TR = {
        '2025-01': Decimal('1.0000'), '2025-02': Decimal('1.0001'),
        '2025-03': Decimal('1.0002'), '2025-04': Decimal('1.0001'),
        '2025-05': Decimal('1.0002'), '2025-06': Decimal('1.0001'),
        '2025-07': Decimal('1.0003'), '2025-08': Decimal('1.0002'),
        '2025-09': Decimal('1.0002'), '2025-10': Decimal('1.0003'),
        '2025-11': Decimal('1.0002'), '2025-12': Decimal('1.0002'),
        '2026-01': Decimal('1.0002'),
    }
    
    def calcular(self, principal: Decimal, vencimento: datetime, 
                 pagamento: datetime) -> Dict:
        """
        Input: dates as datetime objects (or date objects)
        """
        # Ensure we work with dates if datetime passed
        if isinstance(vencimento, datetime):
            vencimento = vencimento.date()
        if isinstance(pagamento, datetime):
            pagamento = pagamento.date()
            
        dt_venc = vencimento
        dt_pag = pagamento
        
        if dt_pag <= dt_venc:
            return {
                'principal': principal,
                'status': 'DENTRO DO PRAZO',
                'meses_atraso': 0,
                'coef_tr': '1.000000',
                'correcao_monetaria': Decimal('0.00'),
                'valor_corrigido': principal,
                'juros_perc': '0.00%',
                'juros_valor': Decimal('0.00'),
                'multa_perc': '0%',
                'multa_valor': Decimal('0.00'),
                'total': principal
            }
        
        # Meses de atraso (not strict calendar months, but span)
        # Using prompt logic: (dt_pag.year - dt_venc.year) * 12 + (dt_pag.month - dt_venc.month)
        meses = (dt_pag.year - dt_venc.year) * 12 + (dt_pag.month - dt_venc.month)
        if dt_pag.day < dt_venc.day:
             # If day not reached, maybe substract 1? Assuming simplified monthly logic from prompt
             pass
        
        # 1. Correção TR
        coef_tr = self._obter_coef_tr(dt_venc, dt_pag)
        valor_corrigido = principal * coef_tr
        correcao = valor_corrigido - principal
        
        # 2. Juros 0.5%/mês sobre corrigido
        # Juros is normally pro-rata or full month? Prompt says "0.5%/mês".
        juros = valor_corrigido * self.JUROS_MENSAL * Decimal(meses)
        
        # 3. Multa 5% ou 10%
        # 5% no mês vencimento, 10% depois.
        no_mes_venc = (dt_pag.year == dt_venc.year and 
                       dt_pag.month == dt_venc.month)
        taxa_multa = self.MULTA_MES_VENC if no_mes_venc else self.MULTA_APOS_VENC
        multa = valor_corrigido * taxa_multa
        
        total = valor_corrigido + juros + multa
        
        return {
            'principal': principal,
            'meses_atraso': meses,
            'coef_tr': f"{coef_tr:.6f}",
            'correcao_monetaria': correcao.quantize(Decimal('0.01'), ROUND_HALF_UP),
            'valor_corrigido': valor_corrigido.quantize(Decimal('0.01'), ROUND_HALF_UP),
            'juros_perc': f"{self.JUROS_MENSAL * Decimal(meses) * 100:.2f}%",
            'juros_valor': juros.quantize(Decimal('0.01'), ROUND_HALF_UP),
            'multa_perc': f"{taxa_multa*100:.0f}%",
            'multa_valor': multa.quantize(Decimal('0.01'), ROUND_HALF_UP),
            'total': total.quantize(Decimal('0.01'), ROUND_HALF_UP)
        }
    
    def _obter_coef_tr(self, dt_inicio, dt_fim) -> Decimal:
        """Multiplica coeficientes TR do período"""
        coef_acum = Decimal('1.0')
        ano, mes = dt_inicio.year, dt_inicio.month
        
        # Iterate months from start to end
        # Prompt logic: while (ano, mes) <= (dt_fim.year, dt_fim.month)
        
        while (ano, mes) <= (dt_fim.year, dt_fim.month):
            chave = f"{ano}-{mes:02d}"
            coef_acum *= self.TABELA_TR.get(chave, Decimal('1.0'))
            mes += 1
            if mes > 12:
                mes = 1
                ano += 1
        
        return coef_acum
