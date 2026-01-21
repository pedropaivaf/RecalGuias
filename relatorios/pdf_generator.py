from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

class GeradorRelatorioPDF:
    """Gera relatório profissional de recálculo"""
    
    def gerar(self, dados_calculo: dict, tipo_guia: str, 
              nome_arquivo: str = None):
        """
        dados_calculo: dict retornado pela calculadora
        tipo_guia: 'INSS', 'FGTS', 'DART'
        """
        if not nome_arquivo:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"recalculo_{tipo_guia}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(nome_arquivo, pagesize=A4,
                               topMargin=20*mm, bottomMargin=20*mm)
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        titulo_style = ParagraphStyle(
            'Titulo', parent=styles['Heading1'],
            fontSize=18, textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=12, alignment=1
        )
        story.append(Paragraph(f"RELATÓRIO DE RECÁLCULO - {tipo_guia}", titulo_style))
        story.append(Spacer(1, 10*mm))
        
        # Info básica
        story.append(Paragraph(f"Data do Cálculo: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                              styles['Normal']))
        story.append(Spacer(1, 5*mm))
        
        # Tabela de valores
        # Tratar dados decimais e formatar
        principal_val = dados_calculo.get('principal', 0.0)
        
        tabela_dados = [
            ['Descrição', 'Valor'],
            ['Valor Principal', f"R$ {principal_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')],
        ]
        
        if 'dias_atraso' in dados_calculo:
            tabela_dados.append(['Dias em Atraso', str(dados_calculo['dias_atraso'])])
        if 'meses_atraso' in dados_calculo:
            tabela_dados.append(['Meses em Atraso', str(dados_calculo['meses_atraso'])])
            
        # Multa
        multa_val = dados_calculo.get('multa_valor', 0.0)
        if multa_val:
            multa_perc = dados_calculo.get('multa_perc', dados_calculo.get('multa_percentual', ''))
            tabela_dados.append([
                f"Multa ({multa_perc})",
                f"R$ {multa_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ])
            
        # Juros
        juros_val = dados_calculo.get('juros_valor', 0.0)
        if juros_val:
            juros_perc = dados_calculo.get('juros_selic_acum', dados_calculo.get('juros_perc', ''))
            tabela_dados.append([
                f"Juros ({juros_perc})",
                f"R$ {juros_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ])

        # FGTS Extras
        if 'correcao_monetaria' in dados_calculo and dados_calculo['correcao_monetaria'] > 0:
             tabela_dados.append([
                f"Correção Monetária (TR)",
                f"R$ {dados_calculo['correcao_monetaria']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ])
        
        tabela_dados.append(['', ''])  # Linha vazia
        
        total_val = dados_calculo.get('total', dados_calculo.get('valor_total', 0.0))
        tabela_dados.append([
            'VALOR TOTAL ATUALIZADO',
            f"R$ {total_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        ])
        
        tabela = Table(tabela_dados, colWidths=[100*mm, 60*mm])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('GRID', (0, 0), (-1, -2), 1, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        
        story.append(tabela)
        story.append(Spacer(1, 10*mm))
        
        # Rodapé
        story.append(Paragraph(
            "Este documento foi gerado automaticamente pelo Sistema de Recálculo Tributário.",
            styles['Normal']
        ))
        
        try:
            doc.build(story)
            return nome_arquivo
        except Exception as e:
            # Em caso de erro (ex: arquivo aberto), tentar salvar com nome diferente
            novo_nome = f"erro_salvar_{datetime.now().microsecond}.pdf"
            print(f"Erro ao salvar PDF: {e}. Tentando {novo_nome}")
            return None
