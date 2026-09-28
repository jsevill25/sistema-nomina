from core.base import *

class AuditUITab(ttk.Frame):
    """Pestaña de visor de auditoría del sistema."""

    def __init__(self, parent):
        super().__init__(parent)
        self._create_ui()
        self.cargar_auditoria()

    def _create_ui(self):
        tb = ttk.Frame(self, padding=8)
        tb.pack(fill=tk.X)
        ttk.Button(tb, text="🔄 Refrescar Auditoría", command=self.cargar_auditoria).pack(side=tk.LEFT, padx=4)

        columns = ("id", "usuario", "accion", "detalle", "fecha")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("usuario", text="Usuario")
        self.tree.heading("accion", text="Acción")
        self.tree.heading("detalle", text="Detalle de Operación")
        self.tree.heading("fecha", text="Fecha / Hora")

        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("usuario", width=110)
        self.tree.column("accion", width=150)
        self.tree.column("detalle", width=380)
        self.tree.column("fecha", width=150, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def cargar_auditoria(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, usuario, accion, detalle, fecha FROM auditoria ORDER BY id DESC LIMIT 300")
            for r in cursor.fetchall():
                self.tree.insert("", tk.END, values=r)
