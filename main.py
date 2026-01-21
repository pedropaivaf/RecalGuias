import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import sys
import os

# Add current directory to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from calculadoras.inss_calculator import CalculadoraINSS
from calculadoras.fgts_calculator import CalculadoraFGTS
from calculadoras.icms_calculator import CalculadoraICMS
from validadores.febraban_validator import FebrabanValidator
from servicos.history_service import HistoryService
from servicos.license_service import LicenseService
from extratores.pdf_extractor import ExtratorGuiaPDF
from relatorios.pdf_generator import GeradorRelatorioPDF

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
    ROOT_CLASS = TkinterDnD.Tk
except ImportError:
    HAS_DND = False
    ROOT_CLASS = tk.Tk

class MainApp:
    def __init__(self, root):
        self.root = root
        
        # ✅ VALIDAR LICENÇA PRIMEIRO
        self.license_service = LicenseService()
        
        if not self._validar_licenca_inicial():
            sys.exit(0)
            
        self.root.title("Recálculo de Guias - FASE 3")
        self.root.geometry("700x850")
        
        # Drag Drop
        if HAS_DND:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        # Inicializa calculadoras e serviços
        self.status_var = tk.StringVar(value="Inicializando serviços...")
        
        # Styles
        style = ttk.Style()
        style.theme_use('clam')
        
        self.history_service = HistoryService()
        self.create_widgets()
        self.create_menu()
        
        self.calc_inss = CalculadoraINSS()
        self.calc_fgts = CalculadoraFGTS()
        self.calc_icms = CalculadoraICMS()
        
        self.ultimo_resultado = None
        self.ultimo_tipo = None
        
        self.status_var.set("Pronto.")
        self.refresh_history()

    def create_menu(self):
        # Criar menubar
        menubar = tk.Menu(self.root)

        # Menu Licença
        menu_licenca = tk.Menu(menubar, tearoff=0)
        menu_licenca.add_command(label="Ver Licença", command=self.ver_info_licenca)
        menu_licenca.add_command(label="Trocar Chave", command=self.trocar_licenca)
        menubar.add_cascade(label="Licença", menu=menu_licenca)

        self.root.config(menu=menubar)

    def _validar_licenca_inicial(self) -> bool:
        """Valida licença ao iniciar"""
        chave_salva = self.license_service.obter_chave_salva()
        
        if chave_salva:
            # Validar silenciosamente se possível, ou mostrar loading? 
            # O código original valida online direto (bloqueante)
            resultado = self.license_service.validar_online(chave_salva)
            
            if resultado['valida']:
                if not resultado.get('online'):
                    dias = resultado.get('dias_offline_restantes', 0)
                    print(f"⚠️  Modo offline - {dias} dias restantes")
                return True
            else:
                messagebox.showerror(
                    "Licença Inválida",
                    f"{resultado['mensagem']}\n\nInsira uma nova chave."
                )
        
        return self._solicitar_chave_usuario()

    def _solicitar_chave_usuario(self) -> bool:
        """Dialog de ativação"""
        # Se self.root já existe e está visível, usar ele?
        # A instrução manda criar root_temp. Mas como já temos self.root (mesmo que vazio), 
        # criar outro Tk() pode dar erro. Vamos tentar usar um Toplevel ou withdraw o root principal se não quisermos mostrar.
        # Vou seguir a instrução USER mas usar Toplevel se root já existir, ou seguir a risca.
        # User diz: root_temp = tk.Tk(); root_temp.withdraw()
        # Isso cria uma segunda instância da Tk. Geralmente não recomendado, mas vou seguir o snippet para garantir comportamento isolado
        # se o init ainda não mostrou a janela principal.
        
        # Mas atenção: self.root já foi criado fora.
        # Melhor usar self.root oculto se necessário, ou usar parent=self.root
        
        # Vou adaptar para usar self.root como parent já que ele foi passado no init
        
        while True:
            chave = simpledialog.askstring(
                "Ativação de Licença",
                "Insira sua chave de licença:\n(Formato: XXXX-XXXX-XXXX-XXXX)",
                parent=self.root
            )
            
            if not chave:
                resposta = messagebox.askyesno(
                    "Sair",
                    "Sem licença, o programa será encerrado.\nSair?",
                    parent=self.root
                )
                if resposta:
                    return False
                continue
            
            resultado = self.license_service.validar_online(chave)
            
            if resultado['valida']:
                messagebox.showinfo(
                    "Sucesso",
                    f"Licença ativada!\n\nCliente: {resultado.get('cliente_nome', 'N/A')}",
                    parent=self.root
                )
                return True
            else:
                messagebox.showerror(
                    "Erro",
                    f"Licença inválida:\n{resultado['mensagem']}",
                    parent=self.root
                )

    def ver_info_licenca(self):
        """Menu: Ver informações da licença"""
        chave = self.license_service.obter_chave_salva()
        if not chave:
            messagebox.showinfo("Licença", "Nenhuma licença ativa")
            return
        
        resultado = self.license_service.validar_online(chave)
        
        status = "✅ ATIVA" if resultado['valida'] else "❌ INVÁLIDA"
        modo = "🌐 Online" if resultado.get('online') else f"📴 Offline ({resultado.get('dias_offline_restantes', 0)} dias)"
        
        info = f"""
Chave: {chave}
Status: {status}
Cliente: {resultado.get('cliente_nome', 'N/A')}
Modo: {modo}

Hardware ID: {self.license_service.hardware_id[:16]}...
        """
        
        messagebox.showinfo("Licença", info.strip())

    def trocar_licenca(self):
        """Menu: Trocar chave de licença"""
        if self._solicitar_chave_usuario():
            messagebox.showinfo("Sucesso", "Licença atualizada!")
            # Reiniciar app ou fechar
            self.root.destroy()
            os.execv(sys.executable, ['python'] + sys.argv)

    def create_widgets(self):
        # Container Principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho e Botão PDF
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        lbl_title = ttk.Label(header_frame, text="Sistema de Recálculo Tributário", font=("Helvetica", 16, "bold"))
        lbl_title.pack(side=tk.LEFT)
        
        btn_txt = "📂 Carregar PDF" if not HAS_DND else "📂 Carregar PDF (ou arraste aqui)"
        btn_load_pdf = ttk.Button(header_frame, text=btn_txt, command=self.carregar_pdf)
        btn_load_pdf.pack(side=tk.RIGHT)
        
        # Tabs
        self.tab_control = ttk.Notebook(main_frame)
        
        self.tab_inss = ttk.Frame(self.tab_control)
        self.tab_fgts = ttk.Frame(self.tab_control)
        self.tab_dart = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_inss, text='INSS (GPS)')
        self.tab_control.add(self.tab_fgts, text='FGTS')
        self.tab_control.add(self.tab_dart, text='DART/ICMS')
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Configuração das ABAS
        self._setup_generic_tab(self.tab_inss, "INSS")
        self._setup_generic_tab(self.tab_fgts, "FGTS")
        self._setup_generic_tab(self.tab_dart, "DART")
        
        # --- HISTORICO ---
        hist_frame = ttk.LabelFrame(main_frame, text="Histórico Recente", padding="10")
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        cols = ('Data', 'Tipo', 'Principal', 'Total')
        self.tree = ttk.Treeview(hist_frame, columns=cols, show='headings', height=6)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status Bar
        lbl_status = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        lbl_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    def _setup_generic_tab(self, parent_frame, tipo):
        """Cria layout padrão para cada aba"""
        frame = ttk.Frame(parent_frame, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Store references to widgets in a dict keyed by tab type/name
        if not hasattr(self, 'widgets'):
            self.widgets = {}
        
        w = {}
        
        grid_frame = ttk.Frame(frame)
        grid_frame.pack(fill=tk.X, pady=10)
        
        # Helpers for AutoFormat
        def setup_date_entry(entry):
            entry.bind('<KeyRelease>', lambda e: self._autoformat_date(e))
            
        def setup_money_entry(entry):
            # Future implementation
            pass

        def setup_barcode_entry(entry):
            entry.bind('<KeyRelease>', lambda e: self._autoformat_digits(e))
            
        # Valor
        ttk.Label(grid_frame, text="Valor Principal (R$):").grid(row=0, column=0, sticky=tk.W, pady=5)
        w['valor'] = ttk.Entry(grid_frame)
        w['valor'].grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # Vencimento
        ttk.Label(grid_frame, text="Vencimento (DD/MM/AAAA):").grid(row=1, column=0, sticky=tk.W, pady=5)
        w['vencimento'] = ttk.Entry(grid_frame)
        w['vencimento'].grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        setup_date_entry(w['vencimento'])
        
        # Pagamento
        ttk.Label(grid_frame, text="Data Pagamento (DD/MM/AAAA):").grid(row=2, column=0, sticky=tk.W, pady=5)
        w['pagamento'] = ttk.Entry(grid_frame)
        w['pagamento'].insert(0, datetime.now().strftime("%d/%m/%Y"))
        w['pagamento'].grid(row=2, column=1, sticky=tk.EW, pady=5, padx=5)
        setup_date_entry(w['pagamento'])
        
        current_row = 3
        
        # Campos Específicos
        if tipo == 'DART':
            ttk.Label(grid_frame, text="Estado:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
            # Lista completa de estados brasileiros
            estados_br = [
                'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
                'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
                'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
            ]
            w['estado'] = ttk.Combobox(grid_frame, values=estados_br)
            w['estado'].current(estados_br.index('SP'))
            w['estado'].grid(row=current_row, column=1, sticky=tk.EW, pady=5, padx=5)
            # w['estado'].state(['readonly']) # Optional
            current_row += 1
            
        # Barcode
        ttk.Label(grid_frame, text="Cód. Barras (Opcional):").grid(row=current_row, column=0, sticky=tk.W, pady=5)
        w['barcode'] = ttk.Entry(grid_frame)
        w['barcode'].grid(row=current_row, column=1, sticky=tk.EW, pady=5, padx=5)
        setup_barcode_entry(w['barcode'])
        
        grid_frame.columnconfigure(1, weight=1)
        
        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        ttk.Button(btn_frame, text="CALCULAR REAJUSTE", command=lambda t=tipo: self.calcular(t)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text="📄 Gerar Relatório", command=self.gerar_relatorio_pdf).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Resultados
        res_frame = ttk.LabelFrame(frame, text="Resultados Detalhados", padding="10")
        res_frame.pack(fill=tk.BOTH, expand=True)
        
        w['res_total'] = ttk.Label(res_frame, text="Total: R$ 0,00", font=("Consolas", 14, "bold"))
        w['res_total'].pack(anchor=tk.W)
        
        w['res_details'] = ttk.Label(res_frame, text="Aguardando cálculo...", font=("Consolas", 10))
        w['res_details'].pack(anchor=tk.W, pady=5)
        
        w['msg'] = ttk.Label(res_frame, text="", foreground="red", wraplength=500)
        w['msg'].pack(pady=5)
        
        self.widgets[tipo] = w

    def _autoformat_date(self, event):
        """Format DD/MM/AAAA while typing"""
        if event.keysym.lower() in ('backspace', 'delete', 'left', 'right'):
            return

        entry = event.widget
        text = entry.get()
        
        # Remove chars non digits
        clean = ''.join(c for c in text if c.isdigit())
        
        # Logic to insert /
        formatted = ""
        if len(clean) > 0:
            formatted += clean[:2]
        if len(clean) >= 3:
            formatted += "/" + clean[2:4]
        if len(clean) >= 5:
            formatted += "/" + clean[4:8]
            
        if text != formatted:
            entry.delete(0, tk.END)
            entry.insert(0, formatted)

    def _autoformat_digits(self, event):
        """Allow only digits"""
        if event.keysym.lower() in ('backspace', 'delete', 'left', 'right'):
            return

        entry = event.widget
        text = entry.get()
        
        # Remove chars non digits
        clean = ''.join(c for c in text if c.isdigit())
            
        if text != clean:
            entry.delete(0, tk.END)
            entry.insert(0, clean)

    def on_drop(self, event):
        arquivo = event.data
        # Clean path formatting from dnd
        if arquivo.startswith('{') and arquivo.endswith('}'):
            arquivo = arquivo[1:-1]
            
        if arquivo.lower().endswith('.pdf'):
            self.processar_pdf_path(arquivo)
        else:
            messagebox.showwarning("Arquivo Inválido", "Apenas arquivos PDF são aceitos")

    def carregar_pdf(self):
        arquivo = filedialog.askopenfilename(
            title="Selecione a guia PDF",
            filetypes=[("PDF", "*.pdf")]
        )
        if arquivo:
            self.processar_pdf_path(arquivo)
            
    def processar_pdf_path(self, arquivo):
            try:
                self.status_var.set("Processando PDF...")
                self.root.update()
                
                extrator = ExtratorGuiaPDF(arquivo)
                dados = extrator.extrair_dados_completos()
                
                if dados['tipo_guia'] == 'DESCONHECIDO' and dados['confianca'] < 0.2:
                     messagebox.showwarning("Atenção", "Não foi possível identificar o tipo de guia ou extrair dados com segurança.")
                     self.status_var.set("Falha na leitura do PDF.")
                     return

                # Identificar aba
                tipo_map = {'INSS': 'INSS', 'FGTS': 'FGTS', 'DART': 'DART'}
                aba_target = tipo_map.get(dados['tipo_guia'])
                
                if aba_target:
                    # Selecionar aba
                    idx = ['INSS', 'FGTS', 'DART'].index(aba_target)
                    self.tab_control.select(idx)
                    
                    w = self.widgets[aba_target]
                    
                    if dados['valor_principal']:
                        w['valor'].delete(0, tk.END)
                        w['valor'].insert(0, str(dados['valor_principal']).replace('.', ','))
                    
                    if dados['data_vencimento']:
                        w['vencimento'].delete(0, tk.END)
                        w['vencimento'].insert(0, dados['data_vencimento'])
                        
                    if dados['codigo_barras']:
                        w['barcode'].delete(0, tk.END)
                        w['barcode'].insert(0, dados['codigo_barras'])
                        
                    msg = f"Dados extraídos de guia {dados['tipo_guia']}.\nConfiança: {dados['confianca']*100:.0f}%"
                    messagebox.showinfo("Sucesso", msg)
                    self.status_var.set("PDF carregado com sucesso.")
                    
                else:
                    messagebox.showwarning("Aviso", f"Tipo de guia detectado: {dados['tipo_guia']}, mas não mapeado para as abas.")
                    
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao processar PDF: {e}")
                self.status_var.set("Erro ao ler PDF.")

    def calcular(self, tipo):
        w = self.widgets[tipo]
        w['msg'].config(text="")
        
        # Read Inputs
        try:
            val_str = w['valor'].get().replace('R$', '').replace('.', '').replace(',', '.').strip()
            if not val_str: raise ValueError("Informe o valor principal.")
            principal = Decimal(val_str)
            
            venc_str = w['vencimento'].get().strip()
            pag_str = w['pagamento'].get().strip()
            
            dt_venc = datetime.strptime(venc_str, "%d/%m/%Y").date()
            dt_pag = datetime.strptime(pag_str, "%d/%m/%Y").date()
            
            # Validation
            barcode = w['barcode'].get().strip()
            if barcode:
                v = FebrabanValidator.validar(barcode)
                if not v['valido']:
                    messagebox.showwarning("Barcode", v.get('mensagem'))
            
            self.status_var.set(f"Calculando {tipo}...")
            self.root.update()
            
            res = {}
            if tipo == 'INSS':
                res = self.calc_inss.calcular(principal, dt_venc, dt_pag)
            elif tipo == 'FGTS':
                res = self.calc_fgts.calcular(principal, dt_venc, dt_pag)
            elif tipo == 'DART':
                estado = w['estado'].get()
                res = self.calc_icms.calcular(estado, principal, dt_venc, dt_pag)
            
            # Store for Report
            self.ultimo_resultado = res
            self.ultimo_tipo = tipo
            
            # Update UI
            # Helpers for consistent formatting
            def fmt(val): 
                if isinstance(val, (Decimal, float)):
                    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                return str(val)
            
            total = res.get('total', res.get('valor_total', 0))
            w['res_total'].config(text=f"TOTAL: {fmt(total)}")
            
            # Build details string
            detalhes = f"Principal: {fmt(principal)}\n"
            
            # Generic extraction of common fields across calculators
            dias_atraso = res.get('dias_atraso') or res.get('meses_atraso', 0)
            prefixo_tempo = "Meses" if 'meses_atraso' in res else "Dias"
            detalhes += f"Atraso: {dias_atraso} {prefixo_tempo}\n"
            
            if 'multa_valor' in res and res['multa_valor']:
                 perc = res.get('multa_perc', res.get('multa_percentual', ''))
                 detalhes += f"Multa ({perc}): {fmt(res['multa_valor'])}\n"
            
            if 'juros_valor' in res and res['juros_valor']:
                 perc = res.get('juros_selic_acum', res.get('juros_perc', ''))
                 detalhes += f"Juros ({perc}): {fmt(res['juros_valor'])}\n"
                 
            if 'correcao_monetaria' in res and res['correcao_monetaria']:
                 detalhes += f"Correção TR: {fmt(res['correcao_monetaria'])}\n"
            
            w['res_details'].config(text=detalhes)
            self.status_var.set("Cálculo realizado.")
            
            # Save History
            try:
                self.history_service.salvar_calculo({
                    'tipo': tipo,
                    'principal': principal,
                    'vencimento': venc_str,
                    'pagamento': pag_str,
                    'total': total,
                    'detalhes': {k: str(v) for k, v in res.items()}
                })
                self.refresh_history()
            except Exception as e:
                print(f"History error: {e}")

        except Exception as e:
            w['msg'].config(text=str(e))
            self.status_var.set("Erro no cálculo.")
            messagebox.showerror("Erro", str(e))

    def gerar_relatorio_pdf(self):
        if not self.ultimo_resultado:
            messagebox.showinfo("Aviso", "Realize um cálculo antes de gerar o relatório.")
            return
            
        try:
            gerador = GeradorRelatorioPDF()
            arquivo = gerador.gerar(self.ultimo_resultado, self.ultimo_tipo)
            if arquivo:
                messagebox.showinfo("PDF Gerado", f"Relatório salvo com sucesso:\n{os.path.abspath(arquivo)}")
                # Opcional: abrir o arquivo
                os.startfile(arquivo)
            else:
                 messagebox.showerror("Erro", "Não foi possível salvar o arquivo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {e}")

    def refresh_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            rows = self.history_service.obter_ultimos()
            for row in rows:
                # db: id, data_calculo, tipo, principal, vencimento, pagamento, total, json
                self.tree.insert('', 'end', values=(row[1], row[2], f"R$ {float(row[3]):.2f}", f"R$ {float(row[6]):.2f}"))
        except:
            pass

if __name__ == "__main__":
    app_root = ROOT_CLASS()
    app = MainApp(app_root)
    app_root.mainloop()
