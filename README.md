# RecalGuias
sistema para recálculo de guia DART (ICMS), INSS e FGTS


# PROMPT MASTER: Sistema Completo de Recálculo de Guias Tributárias Brasileiras

## CONTEXTO
Desenvolver sistema Python desktop para escritório contábil processar guias DART (ICMS), INSS e FGTS vencidas. Cliente anexa PDF da guia OU insere dados manualmente, sistema calcula multa e juros automaticamente conforme regras oficiais 2025/2026.

## OBJETIVO PRINCIPAL
Eliminar retrabalho manual do escritório. Cliente consegue recalcular próprias guias sem depender do contador.

---

## REQUISITOS FUNCIONAIS OBRIGATÓRIOS

### 1. EXTRAÇÃO AUTOMÁTICA DE DADOS
- Aceitar upload de PDF (guia escaneada ou nativa)
- Extrair automaticamente: valor original, data vencimento, código de barras
- Identificar tipo de guia (DART/INSS/FGTS) pelo código de barras ou texto
- Fallback: permitir input manual se OCR falhar

### 2. CÁLCULOS OFICIAIS PRECISOS

**INSS (GPS)**
- Multa: 0,33% ao dia, máximo 20%
- Juros: Taxa SELIC acumulada mês a mês + 1% no mês pagamento
- Fonte: Lei 8.212/91 Art.35 + Lei 9.430/96 Art.61

**FGTS**
- Correção monetária: coeficiente TR do período
- Juros: 0,5% ao mês sobre valor corrigido
- Multa: 5% (pagto no mês vencimento) ou 10% (após mês vencimento)
- Fonte: Lei 8.036/90 Art.22

**DART/ICMS (São Paulo específico, adaptar outros estados)**
- Multa por faixas: 2% (até 30d), 5% (31-60d), 10% (após 60d)
- Juros: SELIC acumulada + 1% mês pagamento
- Fonte: Lei 6.374/89 SP

### 3. VALIDAÇÕES
- Validar código de barras padrão FEBRABAN (Módulo 10 ou 11)
- Verificar dígito verificador
- Identificar segmento e órgão arrecadador
- Alertar se código inválido

### 4. ATUALIZAÇÃO AUTOMÁTICA DE TAXAS
- Consultar API BCB para SELIC atual: https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados
- Baixar tabela TR mensal (manual ou scraping CAIXA)
- Cache local com refresh semanal

### 5. INTERFACE GRÁFICA SIMPLES
- Drag-and-drop para PDF
- Seleção manual de tipo de guia
- Campos editáveis (valor, vencimento, data pagamento)
- Botão "Calcular"
- Resultado formatado profissional
- Botão "Gerar Relatório PDF"
- Histórico de cálculos em lista

### 6. SAÍDAS
- Tela: breakdown detalhado (principal, multa%, juros%, total)
- PDF: relatório profissional com cálculos passo-a-passo
- JSON: histórico persistente local

---

## STACK TÉCNICA OBRIGATÓRIA

### Backend Python
```python
# Extração de dados
pdfplumber==0.11.0      # PDF nativo
PyMuPDF==1.23.8         # PDF → imagem
pytesseract==0.3.10     # OCR português
opencv-python==4.8.1    # Pré-processamento
pyzbar==0.1.9           # Código barras I25

# Cálculos
decimal                 # Precisão monetária
datetime               
requests==2.31.0        # API SELIC

# Interface
tkinter                 # GUI nativa Python
customtkinter==5.2.0    # UI moderna (opcional)

# Relatórios
reportlab==4.0.7        # Gerar PDF resultado
```

### Estrutura de Arquivos
```
sistema_recalculo/
├── main.py                    # Entry point + GUI
├── extratores/
│   ├── pdf_extractor.py       # Classe ExtratorGuiaPDF
│   ├── ocr_handler.py         # Tesseract wrapper
│   └── barcode_reader.py      # pyzbar wrapper
├── calculadoras/
│   ├── inss_calculator.py     # Lógica GPS
│   ├── fgts_calculator.py     # Lógica FGTS
│   └── icms_calculator.py     # Lógica DART (multi-estado)
├── validadores/
│   └── febraban_validator.py  # Validação códigos
├── servicos/
│   ├── selic_service.py       # API BCB + cache
│   └── tr_service.py          # Tabela TR
├── relatorios/
│   └── pdf_generator.py       # ReportLab
├── database/
│   └── historico.db           # SQLite
├── assets/
│   └── logo.png
└── requirements.txt
```

---

## ESPECIFICAÇÕES TÉCNICAS CRÍTICAS

### 1. ExtratorGuiaPDF (extratores/pdf_extractor.py)
```python
class ExtratorGuiaPDF:
    def __init__(self, caminho_pdf: str):
        """Inicializa com caminho do PDF"""
        
    def extrair_dados_completos(self) -> dict:
        """
        Retorna: {
            'tipo_guia': 'INSS'|'FGTS'|'DART',
            'valor_principal': Decimal,
            'data_vencimento': date,
            'codigo_barras': str,
            'confianca': float  # 0-1
        }
        Tenta: 1) pdfplumber, 2) OCR se falhar, 3) barcode reader
        """
        
    def _extrair_por_coordenadas(self, bbox: tuple) -> str:
        """Extração precisa por região do PDF"""
        
    def _extrair_com_ocr(self) -> str:
        """Fallback OCR com pytesseract"""
        
    def _ler_codigo_barras(self) -> str:
        """pyzbar para I25"""
```

### 2. CalculadoraINSS (calculadoras/inss_calculator.py)
```python
from decimal import Decimal
from datetime import date

class CalculadoraINSS:
    def calcular(self, 
                 principal: Decimal,
                 vencimento: date,
                 pagamento: date) -> dict:
        """
        Retorna: {
            'principal': Decimal,
            'dias_atraso': int,
            'multa_percentual': str,  # "20.00%"
            'multa_valor': Decimal,
            'juros_selic_acum': str,  # "4.52%"
            'juros_valor': Decimal,
            'valor_total': Decimal,
            'detalhamento_selic': [
                {'mes': '2025-08', 'taxa': '1.22%'},
                ...
            ]
        }
        """
        # Implementar lógica exata:
        # - Multa: min(0.0033 * dias, 0.20)
        # - Juros: soma SELIC mensal + 1% mês pgto
```

### 3. CalculadoraFGTS (calculadoras/fgts_calculator.py)
```python
class CalculadoraFGTS:
    def calcular(self,
                 principal: Decimal,
                 vencimento: date,
                 pagamento: date,
                 competencia: str) -> dict:  # "MM/AAAA"
        """
        Ordem de cálculo EXATA:
        1. Principal (8% remuneração)
        2. Correção TR (buscar coef. na tabela)
        3. Juros 0,5%/mês sobre valor corrigido
        4. Multa 5% ou 10% sobre valor corrigido
        
        Retorna dict com breakdown completo
        """
```

### 4. CalculadoraICMS (calculadoras/icms_calculator.py)
```python
from enum import Enum

class EstadoICMS(Enum):
    SP = "São Paulo"
    MG = "Minas Gerais"
    RJ = "Rio de Janeiro"
    # ...

class CalculadoraICMS:
    def calcular(self,
                 principal: Decimal,
                 vencimento: date,
                 pagamento: date,
                 estado: EstadoICMS) -> dict:
        """
        Implementar switch-case por estado:
        - SP: faixas 2%/5%/10%
        - MG: 0.15%/dia até 30d, depois faixas
        - Outros: 0.33%/dia padrão
        
        Todos: juros = SELIC + 1%
        """
```

### 5. SelicService (servicos/selic_service.py)
```python
import requests
import sqlite3
from datetime import datetime

class SelicService:
    API_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados"
    
    def __init__(self):
        self.db = sqlite3.connect('database/cache.db')
        self._criar_tabela()
    
    def obter_selic_periodo(self, mes_ini: int, ano_ini: int,
                           mes_fim: int, ano_fim: int) -> dict:
        """
        Retorna: {(ano, mes): Decimal('0.0122'), ...}
        Cache local, atualiza se >7 dias
        """
    
    def _consultar_bcb(self, data_ini: str, data_fim: str) -> list:
        """HTTP request para API BCB"""
```

### 6. Interface GUI (main.py)
```python
import tkinter as tk
from tkinter import filedialog, ttk

class AplicacaoRecalculo:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Recálculo de Guias - MB Contabilidade")
        self.window.geometry("900x700")
        
    def criar_interface(self):
        """
        Layout:
        - Frame superior: Upload PDF ou Input Manual
        - Frame meio: Tipo guia, valor, datas (editáveis)
        - Botão Calcular (grande, azul)
        - Frame resultado: Tabela breakdown
        - Botões: Gerar PDF, Salvar, Limpar
        - Frame inferior: Histórico (últimos 10)
        """
    
    def upload_pdf(self):
        arquivo = filedialog.askopenfilename(
            filetypes=[("PDF", "*.pdf")]
        )
        # Chama ExtratorGuiaPDF
        # Preenche campos automaticamente
        
    def calcular(self):
        # Validar inputs
        # Chamar calculadora apropriada
        # Exibir resultado formatado
        # Salvar em histórico
        
    def gerar_relatorio_pdf(self):
        # ReportLab: criar PDF profissional
        # Logo escritório, dados cálculo, breakdown
```

---

## VALIDAÇÕES E TESTES OBRIGATÓRIOS

### Casos de Teste INSS
```python
# Teste 1: 30 dias atraso
assert calcular_inss(Decimal('1000'), 
                     date(2025,12,15), 
                     date(2026,1,14))['multa_valor'] == Decimal('99.00')

# Teste 2: Limite 20% multa (>61 dias)
assert calcular_inss(Decimal('1000'),
                     date(2025,7,1),
                     date(2026,1,21))['multa_percentual'] == "20.00%"
```

### Casos de Teste FGTS
```python
# Teste: Salário R$3000, 3 meses atraso, TR 1.0025
resultado = calcular_fgts(
    remuneracao=Decimal('3000'),
    vencimento=date(2025,7,7),
    pagamento=date(2025,10,7),
    tr_coef=Decimal('1.0025')
)
assert resultado['principal'] == Decimal('240.00')
assert resultado['multa_valor'] == Decimal('24.06')  # 10%
```

### Validação Código de Barras
```python
# Guia FGTS válida
assert validar_febraban("85890000460952460179160607593050865831483000010")['valido'] == True
assert validar_febraban("85890000460952460179160607593050865831483000010")['orgao'] == 'FGTS'
```

---

## ENTREGÁVEIS FINAIS

1. **Executável standalone**
   - PyInstaller: `pyinstaller --onefile --windowed main.py`
   - Incluir Tesseract OCR no bundle

2. **Manual do usuário PDF**
   - Como usar extração automática
   - Como inserir dados manualmente
   - Interpretação dos resultados

3. **Documentação técnica**
   - Como atualizar tabelas SELIC/TR
   - Como adicionar novos estados ICMS
   - Estrutura de banco de dados

4. **Arquivo de configuração**
```json
   {
     "escritorio": {
       "nome": "MB Contabilidade",
       "cnpj": "...",
       "logo": "assets/logo.png"
     },
     "taxas": {
       "selic_cache_dias": 7,
       "tr_update_manual": true
     }
   }
```

---

## PRIORIDADE DE IMPLEMENTAÇÃO

**FASE 1 (MVP):**
1. Interface básica tkinter
2. Input manual (sem OCR)
3. Calculadora INSS completa
4. Validador FEBRABAN básico
5. SelicService com API BCB

**FASE 2:**
6. Extração PDF com pdfplumber
7. Calculadora FGTS
8. Calculadora ICMS-SP
9. Geração relatório PDF
10. Histórico SQLite

**FASE 3:**
11. OCR fallback (pytesseract)
12. Leitura código barras (pyzbar)
13. ICMS multi-estado
14. Drag-and-drop interface
15. Executável standalone

---

## CRITÉRIOS DE SUCESSO

✅ Cliente anexa PDF → sistema extrai 90%+ dados corretamente
✅ Cálculos conferem com ferramentas oficiais (SICALC, calculadora CAIXA)
✅ Interface intuitiva: <5 cliques para resultado
✅ Relatório PDF profissional e imprimível
✅ Histórico persiste entre sessões
✅ SELIC atualiza automaticamente via API
✅ Executável roda sem Python instalado

---

## OBSERVAÇÕES IMPORTANTES

- **Precisão monetária**: SEMPRE usar `Decimal`, nunca `float`
- **Datas**: biblioteca `datetime`, formato `DD/MM/AAAA` no UI
- **SELIC**: arredondar 4 casas decimais no cálculo intermediário
- **TR**: obter de fonte oficial CAIXA, não estimar
- **Estados ICMS**: começar com SP, expandir gradualmente
- **OCR português**: `pytesseract.image_to_string(img, lang='por')`
- **Performance**: extração PDF deve ser <3s por documento

---

## FONTES OFICIAIS (documentar no código)

- INSS: https://www.gov.br/receitafederal (Lei 8.212/91)
- FGTS: https://www.caixa.gov.br/fgts (Lei 8.036/90)
- SELIC: https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados
- FEBRABAN: Layout código barras v7 (2023)
- ICMS-SP: https://www.fazenda.sp.gov.br (Lei 6.374/89)