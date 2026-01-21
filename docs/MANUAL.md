# Manual do Usuário - Sistema de Recálculo de Guias

Este sistema permite o recálculo de guias tributárias (INSS, FGTS, ICMS) com atualização automática de taxas e extração inteligente de dados.

## Instalação e Execução

1. **Requisitos**:
   - Windows 10/11
   - Python 3.10+ instalado (recomendado)
   - Tesseract OCR (para leitura de imagens e PDFs escaneados). Baixe de [aqui](https://github.com/UB-Mannheim/tesseract/wiki).

2. **Como Rodar**:
   - Navegue até a pasta do projeto.
   - Dê um duplo clique no arquivo `run_app.bat`.
   - A janela principal do sistema irá abrir.

## Guia Rápido

### Extração Automática (PDF)
1. Clique no botão **"📂 Carregar PDF"** no topo da tela. 
2. Ou **arraste o arquivo PDF** para dentro da janela do aplicativo.
3. O sistema tentará identificar automaticamente:
   - Tipo de guia (INSS, FGTS, DART)
   - Valor Principal
   - Data de Vencimento
   - Código de Barras
4. Os campos serão preenchidos e a aba correta selecionada. Verifique os dados antes de calcular.

### INSS (GPS)
- Aba padrão para guias de Previdência Social.
- Multa: 0,33%/dia (max 20%).
- Juros: SELIC acumulada + 1%.

### FGTS
- Aba para guias do Fundo de Garantia.
- Calcula correção TR + Juros 0,5%/mês + Multa (5% ou 10%).
- **Nota**: A tabela TR deve ser alimentada mensalmente (atualmente demonstrativa).

### DART / ICMS
- Suporte para os estados: **SP, MG, RJ, SC**.
- Selecione o **Estado** correto no menu.
- As regras de multa variam conforme a legislação estadual de cada UF.
- Juros seguem o padrão SELIC + 1%.

### Relatórios
- Após realizar um cálculo com sucesso, clique em **"📄 Gerar Relatório"**.
- Um PDF detalhado será salvo na pasta do projeto com todos os dados do cálculo para conferência.

## Solução de Problemas

- **PDF não lido**: Se o PDF for uma imagem (escaneado), certifique-se de ter instalado o Tesseract OCR.
- **Erro de Conexão**: O sistema precisa de internet na primeira execução para baixar as taxas SELIC.
- **Arraste e Solte não funciona**: Requer instalação da biblioteca `tkinterdnd2`. Caso não esteja disponível, use o botão de carregar.
