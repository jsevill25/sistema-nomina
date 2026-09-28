from core.base import *
from modules.employees import EmployeeModule
from modules.concepts import ConceptsModule
from modules.payroll import MonthlyPayrollModule, PaymentHistoryModule
from modules.severance import SeveranceModule
from modules.reports import ReportsModule
from modules.users import UsersModule
from modules.audit import AuditModule

class ModuleManagerDialog(tk.Toplevel):
    """Interfaz gráfica interactiva para activar/desactivar plugins dinámicamente."""

    def __init__(self, parent, on_status_changed_callback: Callable):
        super().__init__(parent)
        self.title("Gestor de Módulos / Plugins del Sistema")
        self.geometry("600x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_status_changed_callback = on_status_changed_callback
        self._create_ui()

    def _create_ui(self):
        lbl = ttk.Label(self, text="MÓDULOS DE NÓMINA ACTIVOS / DISPONIBLES", font=("Segoe UI", 11, "bold"))
        lbl.pack(pady=10)

        f = ttk.Frame(self, padding=10)
        f.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "nombre", "version", "estado")
        self.tree = ttk.Treeview(f, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID Módulo")
        self.tree.heading("nombre", text="Nombre del Módulo")
        self.tree.heading("version", text="Versión")
        self.tree.heading("estado", text="Estado Actual")

        self.tree.column("id", width=130)
        self.tree.column("nombre", width=220)
        self.tree.column("version", width=80, anchor=tk.CENTER)
        self.tree.column("estado", width=100, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True)

        btn_f = ttk.Frame(self, padding=10)
        btn_f.pack(fill=tk.X)

        ttk.Button(btn_f, text="⚡ Activar / Desactivar Módulo", command=self._toggle_modulo).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        self.cargar_modulos()

    def cargar_modulos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for mod in ModuleRegistry.get_all_modules():
            est = "🟢 ACTIVO" if mod.active else "🔴 INACTIVO"
            self.tree.insert("", tk.END, iid=mod.module_id, values=(mod.module_id, mod.name, mod.version, est))

    def _toggle_modulo(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un módulo de la lista.")
            return

        mod_id = sel[0]
        mod = ModuleRegistry._registered_modules[mod_id]
        nuevo_est = not mod.active

        ModuleRegistry.set_module_status(mod_id, nuevo_est)
        self.cargar_modulos()
        self.on_status_changed_callback()


class ThemeSelectorDialog(tk.Toplevel):
    """Diálogo modal para la selección de temas de apariencia empresarial."""

    def __init__(self, parent, on_theme_changed: Callable):
        super().__init__(parent)
        self.title("Selección de Tema Corporativo")
        self.geometry("380x230")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.on_theme_changed = on_theme_changed
        self._init_ui()

    def _init_ui(self):
        f = ttk.Frame(self, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Seleccione el tema visual corporativo:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        cfg = ConfigManager.load_config()
        tema_actual = cfg.get("sistema", {}).get("tema_activo", "Corporativo Ejecutivo (Azul Petróleo)")

        self.cbo_temas = ttk.Combobox(f, values=list(CorporateThemeManager.TEMAS.keys()), state="readonly", width=38)
        if tema_actual in CorporateThemeManager.TEMAS:
            self.cbo_temas.set(tema_actual)
        else:
            self.cbo_temas.current(0)
        self.cbo_temas.pack(pady=10)

        btn_f = ttk.Frame(f)
        btn_f.pack(fill=tk.X, pady=15)

        ttk.Button(btn_f, text="Aplicar Tema", command=self._aplicar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _aplicar(self):
        nuevo_tema = self.cbo_temas.get()
        ConfigManager.set_tema(nuevo_tema)
        self.on_theme_changed(nuevo_tema)
        messagebox.showinfo("Tema Actualizado", f"Se ha aplicado correctamente el tema:\n{nuevo_tema}")
        self.destroy()


class LoginWindow(tk.Tk):
    """Ventana de acceso y login del sistema."""

    def __init__(self):
        super().__init__()
        self.title("Acceso al Sistema - Colegio Huyapari")
        self.geometry("400x320")
        self.resizable(False, False)
        self.eval('tk::PlaceWindow . center')

        # Aplicar tema guardado en configuración
        cfg = ConfigManager.load_config()
        tema_inicial = cfg.get("sistema", {}).get("tema_activo", "Corporativo Ejecutivo (Azul Petróleo)")
        CorporateThemeManager.aplicar_tema(self, tema_inicial)

        self._create_ui()

    def _create_ui(self):
        mf = ttk.Frame(self, padding=25)
        mf.pack(fill=tk.BOTH, expand=True)

        lbl = ttk.Label(mf, text="SISTEMA DE NÓMINA Y PRESTACIONES\nCOLEGIO HUYAPARI", font=("Segoe UI", 11, "bold"), justify=tk.CENTER)
        lbl.pack(pady=(0, 15))

        f = ttk.Frame(mf)
        f.pack(fill=tk.X)

        ttk.Label(f, text="Usuario:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.ent_u = ttk.Entry(f, width=22)
        self.ent_u.grid(row=0, column=1, pady=8, padx=5)
        self.ent_u.focus_set()

        ttk.Label(f, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.ent_p = ttk.Entry(f, show="*", width=22)
        self.ent_p.grid(row=1, column=1, pady=8, padx=5)
        self.ent_p.bind("<Return>", lambda e: self._intentar_login())

        btn = ttk.Button(mf, text="Iniciar Sesión", command=self._intentar_login)
        btn.pack(pady=20)

    def _intentar_login(self):
        u = self.ent_u.get().strip()
        p = self.ent_p.get().strip()

        if not u or not p:
            messagebox.showerror("Error", "Ingrese usuario y contraseña.")
            return

        try:
            if AuthController.login(u, p):
                self.withdraw()
                app = MainWindow(self)
                app.protocol("WM_DELETE_WINDOW", lambda: self._cerrar_app(app))
                app.mainloop()
            else:
                messagebox.showerror("Acceso Denegado", "Usuario o contraseña incorrectos.")
        except Exception as ex:
            messagebox.showerror("Error de Sesión", str(ex))

    def _cerrar_app(self, app_win):
        AuthController.logout()
        app_win.destroy()
        self.destroy()


class MainWindow(tk.Toplevel):
    """Ventana Principal con Pestañas Dinámicas según Plugins Activos y Selector de Temas."""

    def __init__(self, parent):
        super().__init__(parent)
        user = AuthController.get_current_user()
        self.title(f"Sistema de Nómina y Prestaciones LOTTT - Usuario: {user['username']} [{user['rol'].upper()}]")
        self.geometry("1020x700")
        self.minsize(850, 550)

        # Aplicar tema actual en la ventana principal
        cfg = ConfigManager.load_config()
        self.tema_activo = cfg.get("sistema", {}).get("tema_activo", "Corporativo Ejecutivo (Azul Petróleo)")
        CorporateThemeManager.aplicar_tema(self, self.tema_activo)

        self._build_menu()
        self._build_ui()

    def _build_menu(self):
        mb = tk.Menu(self)

        # Menú Sistema
        m_sis = tk.Menu(mb, tearoff=0)
        m_sis.add_command(label="🎨 Elegir Tema Corporativo...", command=self._abrir_selector_temas)
        m_sis.add_command(label="🔌 Gestor de Módulos/Plugins", command=self._abrir_gestor_modulos)
        m_sis.add_separator()
        m_sis.add_command(label="Cerrar Sesión", command=self._cerrar_sesion)
        m_sis.add_command(label="Salir", command=self.destroy)
        mb.add_cascade(label="Sistema", menu=m_sis)

        # Menú Ayuda
        m_ayu = tk.Menu(mb, tearoff=0)
        m_ayu.add_command(label="Acerca de LOTTT Venezuela", command=self._acerca_de)
        mb.add_cascade(label="Ayuda", menu=m_ayu)

        self.config(menu=mb)

    def _build_ui(self):
        top_bar = ttk.Frame(self, padding=5, relief=tk.RAISED)
        top_bar.pack(fill=tk.X)

        usr = AuthController.get_current_user()
        ttk.Label(top_bar, text=f"👤 Usuario: {usr['username']} ({usr['rol']})", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10)

        btn_tema = ttk.Button(top_bar, text="🎨 Cambiar Tema", command=self._abrir_selector_temas)
        btn_tema.pack(side=tk.RIGHT, padx=5)

        btn_mod = ttk.Button(top_bar, text="⚙️ Administrar Plugins", command=self._abrir_gestor_modulos)
        btn_mod.pack(side=tk.RIGHT, padx=5)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.cargar_pestanas_modulos()

    def cargar_pestanas_modulos(self):
        for tab in self.notebook.tabs():
            widget = self.notebook.nametowidget(tab)
            self.notebook.forget(tab)
            widget.destroy()

        modulos_activos = ModuleRegistry.get_active_modules()

        if not modulos_activos:
            empty_frame = ttk.Frame(self.notebook, padding=30)
            ttk.Label(empty_frame, text="⚠️ NO HAY MÓDULOS O PLUGINS ACTIVOS", font=("Segoe UI", 14, "bold")).pack(pady=20)
            ttk.Label(empty_frame, text="El Núcleo del sistema sigue operativo.\nUse el menú 'Sistema -> Gestor de Módulos' para activar funcionalidades.", justify=tk.CENTER).pack(pady=10)
            self.notebook.add(empty_frame, text="🏠 Inicio Núcleo")
            return

        for mod in modulos_activos:
            try:
                tabs = mod.create_ui_tabs(self.notebook)
                for tab in tabs:
                    self.notebook.add(tab, text=mod.name)
            except Exception as e:
                print(f"Error cargando UI del módulo '{mod.module_id}': {e}")

    def _abrir_gestor_modulos(self):
        ModuleManagerDialog(self, on_status_changed_callback=self.cargar_pestanas_modulos)

    def _abrir_selector_temas(self):
        ThemeSelectorDialog(self, on_theme_changed=self._aplicar_nuevo_tema)

    def _aplicar_nuevo_tema(self, nombre_tema: str):
        self.tema_activo = nombre_tema
        CorporateThemeManager.aplicar_tema(self, nombre_tema)
        # Recargar pestañas para refrescar estilos globales de ttk
        self.cargar_pestanas_modulos()

    def _cerrar_sesion(self):
        AuthController.logout()
        self.destroy()
        self.master.deiconify()

    def _acerca_de(self):
        messagebox.showinfo(
            "Acerca del Sistema",
            "SISTEMA DE NÓMINA Y PRESTACIONES SOCIALES\n"
            "Arquitectura de Plugins con Soporte de Tasa BCV Diaria (API + Manual)\n\n"
            "• Cumple con LOTTT Artículo 142 (Garantía vs Retroactivo).\n"
            "• Conversión y cálculo en Bolívares (Bs.) según Tasa BCV oficial.\n"
            "• Generación de recibos y liquidaciones formales en PDF (ReportLab).\n"
            "• Copias de seguridad de registros en Excel (OpenPyXL)."
        )


def bootstrap_application():
    """Inicializa la base de datos core, registra plugins integrados y arranca la app."""
    DatabaseManager.init_core_db()

    ModuleRegistry.register_module(EmployeeModule())
    ModuleRegistry.register_module(ConceptsModule())
    ModuleRegistry.register_module(MonthlyPayrollModule())
    ModuleRegistry.register_module(PaymentHistoryModule())
    ModuleRegistry.register_module(SeveranceModule())
    ModuleRegistry.register_module(ReportsModule())
    ModuleRegistry.register_module(UsersModule())
    ModuleRegistry.register_module(AuditModule())

    ModuleRegistry.load_modules()

    app = LoginWindow()
    app.mainloop()
