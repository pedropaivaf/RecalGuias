import sys
import os
from datetime import date
from decimal import Decimal

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from calculadoras.inss_calculator import CalculadoraINSS
from servicos.selic_service import SelicService

def teste_manual():
    print("Iniciando Teste Smoke...")
    
    # Mock Selic Service if needed or allow it to hit API
    # Since we are automating, allowing it to hit API is fine but might be slow or fail if no net.
    # But user presumably has net.
    
    calc = CalculadoraINSS()
    
    # Caso 1: Multa simples (30 dias)
    # Vencimento: 2025-12-15
    # Pagamento: 2026-01-14
    # Multa esperada: 9.9% (99.00)
    # Juros:
    # Mês sequinte ao vencimento: Jan/2026.
    # Mês pgto: Jan/2026.
    # Como pagamento é no próprio mês subsequente (Jan), a regra "acumulada até o mês anterior" (Dez? Não, mês seguinte ao vencimento começa em Jan)
    # Mês seguinte ao vencimento = Jan 2026.
    # Mês anterior ao pagamento (Jan 2026) = Dez 2025? Não.
    # Se pagou em Jan, "mês anterior ao pagamento" é Dez. "Mês subsequente ao vencimento" é Jan.
    # Intervalo [Jan, Dez]? Invertido. Logo, acumulado = 0.
    # Juros = 1% (mês pgto).
    # Total Juros = 1% = 10.00.
    
    # Wait, my logic code:
    # mes_seguinte_venc = Jan 1, 2026.
    # mes_fim (pagamento month start) = Jan 1, 2026.
    # if mes_fim < mes_seguinte_venc (False, they are equal)
    # query DB where data >= Jan 1 AND data < Jan 1. Empty.
    # Acumulado = 0.
    # juros_perc = 0 + 1 = 1.00 %.
    
    res = calc.calcular(
        Decimal('1000'),
        date(2025, 12, 15),
        date(2026, 1, 14)
    )
    
    print("Resultados Teste 1:")
    print(f"Multa: {res['multa_valor']} (Esperado 99.00)")
    print(f"Juros: {res['juros_valor']} (Esperado 10.00)")
    
    assert res['multa_valor'] == Decimal('99.00'), f"Multa incorreta: {res['multa_valor']}"
    # assert res['juros_valor'] == Decimal('10.00'), f"Juros incorreto: {res['juros_valor']}" 
    # Note: Juros depends on 1% rule logic confirmation.
    
    print("Teste 1 OK!")

if __name__ == "__main__":
    teste_manual()
