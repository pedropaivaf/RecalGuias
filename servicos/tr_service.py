from decimal import Decimal
from datetime import date

class TRService:
    def obter_coeficiente_tr(self, data_referencia: date) -> Decimal:
        # TODO: Implementar scraping ou tabela manual
        return Decimal('1.0000')
