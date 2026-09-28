from core.base import *
from .controller import UsersController

class UsersUITab(ttk.Frame):
    """Pestaña de administración de usuarios y claves."""

    def __init__(self, parent):
        super().__init__(parent)
        self.controller = UsersController()
        self._create_ui()
        self.cargar_usuarios()

    def _create_ui(self):
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="➕ Crear Usuario", command=self._nuevo_usuario).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="🔄 Activar/Desactivar", command=self._toggle_usuario).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="🔄 Refrescar", command=self.cargar_usuarios).pack(side=tk.LEFT, padx=4)

        columns = ("id", "username", "rol", "activo", "creado")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Usuario")
        self.tree.heading("rol", text="Rol")
        self.tree.heading("activo", text="Estado")
        self.tree.heading("creado", text="Fecha Creación")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("username", width=150)
        self.tree.column("rol", width=110, anchor=tk.CENTER)
        self.tree.column("activo", width=100, anchor=tk.CENTER)
        self.tree.column("creado", width=180, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def cargar_usuarios(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in self.controller.listar_usuarios():
            est = "Activo" if r[3] == 1 else "Inactivo"
            self.tree.insert("", tk.END, iid=r[0], values=(r[0], r[1], r[2], est, r[4]))

    def _nuevo_usuario(self):
        dlg = UserDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            u, p, r = dlg.result["user"], dlg.result["pass"], dlg.result["rol"]
            try:
                self.controller.crear_usuario(u, p, r)

                usr_act = AuthController.get_current_user()["username"]
                DatabaseManager.log_auditoria(usr_act, "CREAR_USUARIO", f"Usuario creado: {u}")
                messagebox.showinfo("Éxito", f"Usuario '{u}' creado.")
                self.cargar_usuarios()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El nombre de usuario ya existe.")

    def _toggle_usuario(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un usuario.")
            return

        u_id = sel[0]
        vals = self.tree.item(u_id, "values")
        if vals[1] == "admin":
            messagebox.showerror("Error", "No se puede desactivar al usuario admin principal.")
            return

        nuevo_est = 0 if vals[3] == "Activo" else 1
        self.controller.cambiar_estado(u_id, nuevo_est)

        self.cargar_usuarios()


class UserDialog(tk.Toplevel):
    """Diálogo modal para crear usuarios."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nuevo Usuario")
        self.geometry("320x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self._init_ui()

    def _init_ui(self):
        p = {'padx': 8, 'pady': 6}
        f = ttk.Frame(self, padding=10)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Usuario:").grid(row=0, column=0, sticky=tk.W, **p)
        self.ent_u = ttk.Entry(f, width=18)
        self.ent_u.grid(row=0, column=1, **p)

        ttk.Label(f, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, **p)
        self.ent_p = ttk.Entry(f, show="*", width=18)
        self.ent_p.grid(row=1, column=1, **p)

        ttk.Label(f, text="Rol:").grid(row=2, column=0, sticky=tk.W, **p)
        self.cbo_r = ttk.Combobox(f, values=["usuario", "supervisor", "admin"], state="readonly", width=15)
        self.cbo_r.current(0)
        self.cbo_r.grid(row=2, column=1, **p)

        btn_f = ttk.Frame(f)
        btn_f.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(btn_f, text="Guardar", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_f, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=4)

    def _save(self):
        u, p, r = self.ent_u.get().strip(), self.ent_p.get().strip(), self.cbo_r.get()
        if not (u and p):
            messagebox.showerror("Error", "Ingrese usuario y contraseña.", parent=self)
            return
        self.result = {"user": u, "pass": p, "rol": r}
        self.destroy()
