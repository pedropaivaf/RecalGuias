# Documentação Técnica

## Arquitetura do Sistema

O sistema segue uma arquitetura modular dividida em camadas, facilitando manutenção e expansão.

### Estrutura de Diretórios
- `main.py`: Ponto de entrada e Interface Gráfica (Tkinter).
- `calculadoras/`: Módulos de lógica de negócio para cada tributo.
- `servicos/`: Serviços externos e de infraestrutura (API SELIC, Banco de Dados, Histórico).
- `validadores/`: Regras de validação (FEBRABAN).
- `extratores/`: Camada de extração de dados (PDF, OCR, Barcode).
- `relatorios/`: Geração de relatórios PDF com ReportLab.
- `database/`: Armazenamento local SQLite.

### Componentes de Extração (Fase 3)

#### 1. ExtratorGuiaPDF (`extratores/pdf_extractor.py`)
- Orquestra a extração. Primeiro tenta extrair texto nativo com `pdfplumber`.
- Se falhar (texto vazio ou insuficiente), aciona o `OCRHandler`.
- Identifica tipo de guia por palavras-chave.
- Extrai valores e datas via Regex.

#### 2. OCRHandler (`extratores/ocr_handler.py`)
- Usa `PyMuPDF (fitz)` para rasterizar o PDF em imagem de alta resolução (300 DPI).
- Usa `OpenCV` para pré-processamento (thresholding, denoising).
- Usa `Tesseract OCR` para extração de texto em português.

#### 3. BarcodeReader (`extratores/barcode_reader.py`)
- Usa `PyZbar` e `OpenCV` para detectar e decodificar códigos de barras (Interleaved 2 of 5) diretamente da imagem do documento.

### Calculadoras Estaduais (ICMS)

A `CalculadoraICMS` implementa o padrão Strategy via dispatcher `calcular(estado, ...)`:
- **SP**: Faixas de atraso (2%, 5%, 10%).
- **MG**: Taxa diária (0.15%) até 30 dias, depois faixas fixas.
- **RJ**: Regra padrão federal (0.33%/dia).
- **SC**: Taxa diária (0.30%).

### Como Criar Executável

O projeto inclui script de build `build_exe.py` utilizando PyInstaller.

1. Instale dependências: `pip install -r requirements.txt`
2. Execute: `python build_exe.py`
3. O executável será gerado em `dist/RecalculoGuias.exe`.

**Nota**: Para incluir OCR no executável portável, é necessário empacotar os binários do Tesseract ou garantir que o cliente tenha instalado na máquina. O script atual assume instalação na máquina.
