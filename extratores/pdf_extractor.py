import pdfplumber
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict

class ExtratorGuiaPDF:
    """Extrai dados de guias INSS, FGTS, DART em PDF"""
    
    def __init__(self, caminho_pdf: str):
        self.caminho = caminho_pdf
        self.texto_completo = ""
    
    def extrair_dados_completos(self) -> Dict:
        """
        Extrai: tipo_guia, valor_principal, data_vencimento, codigo_barras
        
        REGEX PATTERNS:
        - Valor: R$?\\s*(\\d{1,3}(?:\\.\\d{3})*(?:,\\d{2}))
        - Data: (\\d{2}[/.-]\\d{2}[/.-]\\d{4})
        - Código: (\\d{47,48}) para linha digitável
        
        IDENTIFICAÇÃO:
        - "GPS" ou "INSS" ou "Previdência" → INSS
        - "FGTS" ou "Caixa Econômica" → FGTS
        - "ICMS" ou "DARE" ou "DART" → DART
        """
        try:
            with pdfplumber.open(self.caminho) as pdf:
                if not pdf.pages:
                    return self._retorno_vazio()
                self.texto_completo = pdf.pages[0].extract_text() or ""
            
            # FASE 3: Fallback OCR se texto vazio
            if not self.texto_completo or len(self.texto_completo) < 50:
                from extratores.ocr_handler import OCRHandler
                ocr = OCRHandler()
                texto_ocr = ocr.pdf_para_texto(self.caminho)
                if texto_ocr:
                    self.texto_completo = texto_ocr
            
            tipo = self._identificar_tipo()
            valor = self._extrair_valor()
            vencimento = self._extrair_data_vencimento()
            codigo = self._extrair_codigo_barras()
            
            return {
                'tipo_guia': tipo,
                'valor_principal': valor,
                'data_vencimento': vencimento,
                'codigo_barras': codigo,
                'confianca': self._calcular_confianca(valor, vencimento)
            }
        except Exception as e:
            print(f"Erro na extração: {e}")
            # Tentativa final com OCR se falhou antes
            try:
                from extratores.ocr_handler import OCRHandler
                ocr = OCRHandler()
                texto_ocr = ocr.pdf_para_texto(self.caminho)
                self.texto_completo = texto_ocr
                return {
                     'tipo_guia': self._identificar_tipo(),
                     'valor_principal': self._extrair_valor(),
                     'data_vencimento': self._extrair_data_vencimento(),
                     'codigo_barras': self._extrair_codigo_barras(),
                     'confianca': 0.5 # estimativa
                }
            except:
                return self._retorno_vazio()

    def _retorno_vazio(self):
        return {
            'tipo_guia': 'DESCONHECIDO',
            'valor_principal': None,
            'data_vencimento': None,
            'codigo_barras': None,
            'confianca': 0.0
        }
    
    def _identificar_tipo(self) -> str:
        """Busca palavras-chave no texto"""
        texto = self.texto_completo.upper()
        if 'GPS' in texto or 'INSS' in texto or 'PREVIDÊNCIA' in texto or 'PREVIDENCIA' in texto:
            return 'INSS'
        elif 'FGTS' in texto or 'CAIXA ECONÔMICA' in texto or 'CAIXA ECONOMICA' in texto:
            return 'FGTS'
        elif 'ICMS' in texto or 'DARE' in texto or 'DART' in texto or 'SECRETARIA DE ESTADO DE FAZENDA' in texto:
            return 'DART'
        return 'DESCONHECIDO'
    
    def _extrair_valor(self) -> Optional[Decimal]:
        # Regex para valores monetários brasileiros
        # Warning fix: escape the dollar sign using character class or double backslash
        pattern = r'R[$]?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))'
        match = re.search(pattern, self.texto_completo)
        if match:
            valor_str = match.group(1).replace('.', '').replace(',', '.')
            return Decimal(valor_str)
        return None
    
    def _extrair_data_vencimento(self) -> Optional[str]:
        """Busca padrão DD/MM/AAAA ou DD-MM-AAAA"""
        # Procurar próximo a palavras "vencimento", "validade"
        pattern = r'(?:vencimento|validade).*?(\d{2}[/.-]\d{2}[/.-]\d{4})'
        match = re.search(pattern, self.texto_completo, re.IGNORECASE)
        if match:
            return match.group(1).replace('-', '/').replace('.', '/')
        
        # Fallback: qualquer data no formato
        pattern = r'(\d{2}[/.-]\d{2}[/.-]\d{4})'
        matches = re.findall(pattern, self.texto_completo)
        if matches:
            # Tentar filtrar datas inválidas ou muito antigas/futuras se necessário
            return matches[0].replace('-', '/').replace('.', '/')
        return None
    
    def _extrair_codigo_barras(self) -> Optional[str]:
        """Busca sequência 47-48 dígitos"""
        # 1. Regex
        pattern = r'(\d{47,48})'
        match = re.search(pattern, self.texto_completo.replace(' ', '').replace('.', '').replace('-', ''))
        if match:
             return match.group(1)
        
        # 2. FASE 3: Barcode Reader (PyZbar)
        try:
             from extratores.barcode_reader import BarcodeReader
             reader = BarcodeReader()
             code = reader.ler_codigo_pdf(self.caminho)
             if code: return code
        except:
             pass
             
        return None
    
    def _calcular_confianca(self, valor, data) -> float:
        """0.0 a 1.0 baseado em campos extraídos"""
        score = 0.0
        if valor: score += 0.4
        if data: score += 0.4
        if self.texto_completo: score += 0.2
        return score
