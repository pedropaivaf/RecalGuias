from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from servicos.selic_service import SelicService

class CalculadoraINSS:
    def __init__(self):
        self.selic_service = SelicService()

    def calcular(self, principal: Decimal, vencimento: date, pagamento: date) -> dict:
        """
        Calcula acréscimos legais para INSS (GPS).
        """
        if pagamento <= vencimento:
            return {
                'principal': principal,
                'dias_atraso': 0,
                'multa_percentual': "0.00%",
                'multa_valor': Decimal('0.00'),
                'juros_selic_acum': "0.00%",
                'juros_valor': Decimal('0.00'),
                'valor_total': principal,
                'detalhamento_selic': []
            }

        # 1. Multa
        delta = pagamento - vencimento
        dias_atraso = delta.days
        
        # 0.33% ao dia, max 20%
        taxa_multa = min(Decimal('0.0033') * dias_atraso, Decimal('0.20'))
        # Arredondar taxa para comparações ou display? Usualmente aplica direto.
        # Mas para display vamos formatar.
        
        multa_valor = (principal * taxa_multa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # 2. Juros (SELIC)
        # Regra: A partir do mês seguinte ao vencimento acumulada até mês anterior + 1% no mês pgto.
        # Se pagou no mesmo mês do vencimento: Juros = 0
        
        juros_perc = Decimal('0.00')
        
        # Primeiro dia do mês seguinte ao vencimento
        mes_seguinte_venc = date(vencimento.year, vencimento.month, 1)
        if mes_seguinte_venc.month == 12:
            mes_seguinte_venc = date(mes_seguinte_venc.year + 1, 1, 1)
        else:
            mes_seguinte_venc = date(mes_seguinte_venc.year, mes_seguinte_venc.month + 1, 1)
            
        pagamento_mes_inicio = date(pagamento.year, pagamento.month, 1)
        
        if pagamento_mes_inicio < mes_seguinte_venc:
            # Pagamento ocorreu no próprio mês de vencimento (ou antes, mas já checamos pay <= due)
            juros_perc = Decimal('0.00')
        else:
            # Estamos pelo menos no mês seguinte.
            # Selic acumulada dos meses intermediários
            selic_acumulada = self.selic_service.obter_selic_acumulada(vencimento, pagamento)
            # Soma 1% do mês do pagamento
            juros_perc = selic_acumulada + Decimal('1.00')
            
        # Converter juros_perc de percentual number (ex: 5.25) para multiplicador (0.0525)
        juros_valor = (principal * (juros_perc / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        total = principal + multa_valor + juros_valor
        
        return {
            'principal': principal,
            'dias_atraso': dias_atraso,
            'multa_percentual': f"{taxa_multa * 100:.2f}%",
            'multa_valor': multa_valor,
            'juros_selic_acum': f"{juros_perc:.2f}%",
            'juros_valor': juros_valor,
            'valor_total': total,
            'detalhamento_selic': [] # TODO: Retornar lista detalhada se necessário
        }
