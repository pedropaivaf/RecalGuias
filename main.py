import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from decimal import Decimal
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Offline Security Core
import src.security_core as sec

from calculadoras.inss_calculator import CalculadoraINSS
from calculadoras.fgts_calculator import CalculadoraFGTS
from calculadoras.icms_calculator import CalculadoraICMS
from servicos.history_service import HistoryService
from extratores.pdf_extractor import ExtratorGuiaPDF
from relatorios.pdf_generator import GeradorRelatorioPDF

# --- DND Setup ---
HAS_DND = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    pass

# define Base App Class
if HAS_DND:
    class BaseApp(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class BaseApp(ctk.CTk):
        pass

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, corner_radius=15)
        self.on_login_success = on_login_success
        self.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.title = ctk.CTkLabel(self, text="Autenticação RecalGuias", font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(padx=40, pady=(40, 20))

        self.user_entry = ctk.CTkEntry(self, placeholder_text="Usuário", width=300, height=40)
        self.user_entry.pack(padx=40, pady=(0, 15))
        self.user_entry.focus()

        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=300, height=40)
        self.pass_entry.pack(padx=40, pady=(0, 20))
        self.pass_entry.bind('<Return>', lambda e: self.login())

        self.btn_login = ctk.CTkButton(self, text="ENTRAR", command=self.login, width=300, height=40, font=ctk.CTkFont(weight="bold"))
        self.btn_login.pack(padx=40, pady=(0, 10))

        self.status = ctk.CTkLabel(self, text="", text_color="#ff5555")
        self.status.pack(pady=(0, 20))

    def login(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()
        
        if sec.login(u, p):
            self.place_forget() # Hide login
            self.on_login_success() 
        else:
            self.status.configure(text="Usuário ou senha inválidos.")
            self.pass_entry.delete(0, tk.END)

class RecalApp(BaseApp):
    def __init__(self, license_payload):
        super().__init__()
        self.license_info = license_payload
        
        self.title("Recálculo de Guias - OFFLINE (Modern)")
        self.geometry("500x450") # Login Size
        
        # --- ICON SETUP ---
        try:
            # Handle Nuitka/PyInstaller temp paths
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, "assets", "icon.ico")
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                print(f"DEBUG: Icon not found at {icon_path}")
        except Exception as e:
            print(f"DEBUG: Failed to set icon: {e}")
        
        # DND
        if HAS_DND:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind('<<Drop>>', self.on_drop)
                print("DEBUG: DnD registered successfully.")
            except Exception as e:
                print(f"DEBUG: DnD registration failed: {e}")

        self.status_var = tk.StringVar(value="Pronto.")
        
        # Services
        self.history_service = HistoryService()
        self.calc_inss = CalculadoraINSS()
        self.calc_fgts = CalculadoraFGTS()
        self.calc_icms = CalculadoraICMS()
        
        self.ultimo_resultado = None
        self.ultimo_tipo = None
        self.widgets = {}
        
        self._setup_styles()
        # Widgets will be created after login
        
    def load_main_interface(self):
        self.geometry("1000x800")
        self.minsize(900, 700)
        self.create_widgets()
        self.create_menu()
        self.refresh_history()

    def _setup_styles(self):
        # Configure Treeview style for Dark Mode
        style = ttk.Style()
        style.theme_use("clam")
        
        # Treeview colors
        bg_color = "#2b2b2b"
        fg_color = "white"
        selected_bg = "#1f6aa5"
        
        style.configure("Treeview", 
                        background=bg_color, 
                        foreground=fg_color, 
                        fieldbackground=bg_color, 
                        borderwidth=0,
                        rowheight=30)
        
        style.configure("Treeview.Heading", 
                        background="#1f1f1f", 
                        foreground="white", 
                        relief="flat",
                        font=("Roboto", 10, "bold"))
        
        style.map("Treeview", background=[('selected', selected_bg)])
        style.map("Treeview.Heading", background=[('active', "#333333")])

    def create_menu(self):
        menubar = tk.Menu(self)
        menu_licenca = tk.Menu(menubar, tearoff=0)
        menu_licenca.add_command(label="Sobre (Licença)", command=self.ver_info_licenca)
        menubar.add_cascade(label="Ajuda", menu=menu_licenca)
        self.configure(menu=menubar)

    def ver_info_licenca(self):
        client = self.license_info.get('client', 'Desconhecido')
        hwid = self.license_info.get('hwid', 'N/A')
        info = f"CLIENTE: {client}\nHWID: {hwid}\nMachine ID: {sec.get_machine_id()}"
        messagebox.showinfo("Sobre", info)

    def create_widgets(self):
        # Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Side Menu (Optional, or just header)
        # Let's stick to the previous layout but modernized.
        
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="Sistema de Recálculo Tributário", font=("Roboto", 24, "bold")).pack(side=tk.LEFT)
        
        btn_txt = "📂 Carregar ou Arrastar PDF" if HAS_DND else "📂 Carregar PDF"
        ctk.CTkButton(header_frame, text=btn_txt, command=self.carregar_pdf, height=40).pack(side=tk.RIGHT)
        
        # Tabview
        self.tabview = ctk.CTkTabview(main_frame, width=500)
        self.tabview.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.tabview.add("INSS")
        self.tabview.add("FGTS")
        self.tabview.add("DART/ICMS")
        
        self._setup_generic_tab(self.tabview.tab("INSS"), "INSS")
        self._setup_generic_tab(self.tabview.tab("FGTS"), "FGTS")
        self._setup_generic_tab(self.tabview.tab("DART/ICMS"), "DART") # Use internal key DART
        
        # History
        hist_frame = ctk.CTkFrame(main_frame)
        hist_frame.pack(fill=tk.BOTH, expand=True)
        
        ctk.CTkLabel(hist_frame, text="Histórico Recente", font=("Roboto", 16, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        cols = ('Data', 'Tipo', 'Principal', 'Total')
        self.tree = ttk.Treeview(hist_frame, columns=cols, show='headings', height=6)
        for col in cols: 
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150 if col == 'Data' else 100)
            
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Footer / Status
        self.status_lbl = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", fg_color="#1a1a1a", height=30)
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_generic_tab(self, parent, tipo):
        if not hasattr(self, 'widgets'): self.widgets = {}
        
        # Use a grid layout inside the tab
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        w = {}
        
        # Input Section (Left)
        input_frame = ctk.CTkFrame(container)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Result Section (Right)
        res_frame = ctk.CTkFrame(container)
        res_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # --- Inputs ---
        r = 0
        def _add_entry(row, label, key, default=None):
            ctk.CTkLabel(input_frame, text=label).grid(row=row, column=0, sticky="w", padx=15, pady=(15, 5))
            e = ctk.CTkEntry(input_frame, placeholder_text=label)
            e.grid(row=row+1, column=0, sticky="ew", padx=15, pady=(0, 5))
            if default: e.insert(0, default)
            w[key] = e
            return row + 2

        r = _add_entry(r, "Valor Principal (R$)", 'valor')
        r = _add_entry(r, "Vencimento (DD/MM/AAAA)", 'vencimento')
        
        ctk.CTkLabel(input_frame, text="Pagamento (DD/MM/AAAA)").grid(row=r, column=0, sticky="w", padx=15, pady=(15, 5))
        w['pagamento'] = ctk.CTkEntry(input_frame)
        w['pagamento'].insert(0, datetime.now().strftime("%d/%m/%Y"))
        w['pagamento'].grid(row=r+1, column=0, sticky="ew", padx=15, pady=(0, 5))
        r += 2

        if tipo == 'DART':
            ctk.CTkLabel(input_frame, text="Estado").grid(row=r, column=0, sticky="w", padx=15, pady=(15, 5))
            w['estado'] = ctk.CTkOptionMenu(input_frame, values=['SP','RJ','MG','RS','PR','SC','BA'])
            w['estado'].grid(row=r+1, column=0, sticky="ew", padx=15, pady=(0, 5))
            r += 2
            
        r = _add_entry(r, "Código Barras", 'barcode')
        
        # Bindings for Date Format
        w['vencimento'].bind('<KeyRelease>', self._fmt_date)
        w['pagamento'].bind('<KeyRelease>', self._fmt_date)
        
        # Buttons
        btn_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_frame.grid(row=r, column=0, sticky="ew", padx=15, pady=20)
        
        ctk.CTkButton(btn_frame, text="CALCULAR", command=lambda: self.calcular(tipo), font=("Roboto", 14, "bold"), height=40)\
           .pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ctk.CTkButton(btn_frame, text="PDF", command=self.gerar_relatorio_pdf, width=60, height=40, fg_color="#E04F5F", hover_color="#C03545")\
           .pack(side=tk.RIGHT, padx=(5, 0))

        # --- Results ---
        ctk.CTkLabel(res_frame, text="Resultados", font=("Roboto", 18, "bold")).pack(anchor="w", padx=20, pady=20)
        
        w['res_total_frame'] = ctk.CTkFrame(res_frame, fg_color="#1f6aa5", corner_radius=10)
        w['res_total_frame'].pack(fill=tk.X, padx=20, pady=(0, 20))
        
        w['res_total'] = ctk.CTkLabel(w['res_total_frame'], text="R$ 0,00", font=("Roboto", 28, "bold"))
        w['res_total'].pack(pady=15)
        ctk.CTkLabel(w['res_total_frame'], text="Total a Pagar").pack(pady=(0, 15))

        w['res_details'] = ctk.CTkLabel(res_frame, text="Aguardando cálculo...", justify="left", font=("Consolas", 14))
        w['res_details'].pack(anchor="w", padx=20)
        
        w['msg'] = ctk.CTkLabel(res_frame, text="", text_color="#FF5555")
        w['msg'].pack(pady=10)

        # Make input frame columns expandable
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.widgets[tipo] = w

    def _fmt_date(self, event):
        if event.keysym.lower() in ('backspace','delete','left','right'): return
        
        # Get the widget (could be the internal Entry or the CTkEntry)
        # For CTkEntry, current ctk versions, bind on the widget passes the internal entry as event.widget?
        # Let's handle both.
        
        widget = event.widget
        # If it's a CTkEntry (doubtful in event), we use .get(). If it's tk.Entry, we use .get().
        if isinstance(widget, ctk.CTkEntry):
            txt_full = widget.get()
        else:
            txt_full = widget.get()
            
        txt = ''.join(c for c in txt_full if c.isdigit())
        fmt = ""
        if len(txt) > 0: fmt += txt[:2]
        if len(txt) >= 3: fmt += "/" + txt[2:4]
        if len(txt) >= 5: fmt += "/" + txt[4:8]
        
        if txt_full != fmt:
            # Need to update properly
            # If widget is tk.Entry (internal)
            try:
                widget.delete(0, tk.END)
                widget.insert(0, fmt)
            except:
                pass

    def on_drop(self, event):
        f = event.data
        if f.startswith('{') and f.endswith('}'): f = f[1:-1]
        if f.lower().endswith('.pdf'): self.processar_pdf_path(f)
        else: messagebox.showwarning("Erro", "Apenas PDF")

    def carregar_pdf(self):
        f = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if f: self.processar_pdf_path(f)

    def processar_pdf_path(self, f):
        try:
            self.status_var.set("Lendo PDF...")
            self.update()
            ext = ExtratorGuiaPDF(f)
            d = ext.extrair_dados_completos()
            
            tipo = d.get('tipo_guia')
            if tipo in self.widgets:
                # Select tab
                # The tab name in tabview is INSS, FGTS, DART/ICMS
                # our key in widgets is INSS, FGTS, DART
                
                target_tab = ""
                if tipo == "INSS": target_tab = "INSS"
                elif tipo == "FGTS": target_tab = "FGTS"
                elif tipo == "DART": target_tab = "DART/ICMS"
                
                if target_tab:
                     self.tabview.set(target_tab)
                
                w = self.widgets[tipo]
                if d['valor_principal']: 
                    w['valor'].delete(0,tk.END)
                    w['valor'].insert(0, str(d['valor_principal']).replace('.',','))
                if d['data_vencimento']: 
                    w['vencimento'].delete(0,tk.END)
                    w['vencimento'].insert(0, d['data_vencimento'])
                if d['codigo_barras']: 
                    w['barcode'].delete(0,tk.END)
                    w['barcode'].insert(0, d['codigo_barras'])
                
                messagebox.showinfo("Sucesso", f"Guia {tipo} carregada!")
            else:
                messagebox.showwarning("Erro", f"Tipo {tipo} não reconhecido.")
            self.status_var.set("Pronto.")
        except Exception as e:
            messagebox.showerror("Erro PDF", str(e))
            self.status_var.set("Erro PDF")

    def calcular(self, tipo):
        w = self.widgets[tipo]
        w['msg'].configure(text="")
        try:
            v_str = w['valor'].get().replace('R$','').replace('.','').replace(',','.').strip()
            if not v_str: raise ValueError("Valor inválido")
            princ = Decimal(v_str)
            dt_v = datetime.strptime(w['vencimento'].get(), "%d/%m/%Y").date()
            dt_p = datetime.strptime(w['pagamento'].get(), "%d/%m/%Y").date()
            
            self.status_var.set("Calculando...")
            self.update()
            
            res = {}
            if tipo == 'INSS': res = self.calc_inss.calcular(princ, dt_v, dt_p)
            elif tipo == 'FGTS': res = self.calc_fgts.calcular(princ, dt_v, dt_p)
            elif tipo == 'DART': res = self.calc_icms.calcular(w['estado'].get(), princ, dt_v, dt_p)
            
            self.ultimo_resultado = res; self.ultimo_tipo = tipo
            
            def fmt(x): return f"R$ {x:,.2f}".replace(',','X').replace('.',',').replace('X','.')
            
            tot = res.get('total', res.get('valor_total', 0))
            w['res_total'].configure(text=fmt(tot))
            
            det = f"Principal: {fmt(princ)}\n"
            if 'juros_valor' in res: det += f"Juros: {fmt(res['juros_valor'])}\n"
            if 'multa_valor' in res: det += f"Multa: {fmt(res['multa_valor'])}\n"
            if 'correcao_monetaria' in res and res['correcao_monetaria']: det += f"Correção: {fmt(res['correcao_monetaria'])}\n"
            
            w['res_details'].configure(text=det)
            self.status_var.set("Cálculo OK")
            
            self.history_service.salvar_calculo({
                'tipo': tipo, 'principal': princ, 'vencimento': w['vencimento'].get(),
                'pagamento': w['pagamento'].get(), 'total': tot, 'detalhes': {k:str(v) for k,v in res.items()}
            })
            self.refresh_history()
            
        except Exception as e:
            w['msg'].configure(text=str(e))
            self.status_var.set("Erro no Cálculo")
            import traceback
            traceback.print_exc()

    def gerar_relatorio_pdf(self):
        if self.ultimo_resultado:
            try:
                path = GeradorRelatorioPDF().gerar(self.ultimo_resultado, self.ultimo_tipo)
                if path: os.startfile(path)
            except Exception as e: messagebox.showerror("Erro", str(e))

    def refresh_history(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in self.history_service.obter_ultimos():
            self.tree.insert('', 'end', values=(r[1], r[2], f"R$ {float(r[3]):.2f}", f"R$ {float(r[6]):.2f}"))

def main():
    print("DEBUG: Starting main() [Modern UI]...")
    
    # Check dependencies
    try:
        import customtkinter
    except ImportError:
        messagebox.showerror("Erro Fatal", "Módulo 'customtkinter' não encontrado.\nExecute: pip install customtkinter")
        return

    # 1. License Check
    try:
        valid, msg, payload = sec.validate_license()
        print(f"DEBUG: Valid? {valid}")
    except Exception as e:
        valid, msg, payload = False, str(e), {}

    if not valid:
        # Create a temp root just to show error
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror("Erro Licença", f"{msg}\nID: {sec.get_machine_id()}")
        temp_root.destroy()
        sys.exit(1)

    # 2. Main App Logic
    app = RecalApp(payload)
    
    def on_login_success():
        print("DEBUG: Login Success. Loading Main Interface.")
        login_layer.destroy()
        app.load_main_interface()
    
    login_layer = LoginFrame(app, on_login_success)
    # Ensure login layer is centered
    login_layer.place(relx=0.5, rely=0.5, anchor="center")
    
    app.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL: {e}")
        import traceback
        traceback.print_exc()
