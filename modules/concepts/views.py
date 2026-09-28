from core.base import *
from .controller import ConceptosController

class ConceptsUITab(ttk.Frame):
    """Pestaña para visualizar y modificar parámetros de asignaciones y deducciones."""

    def __init__(self, parent):
        super().__init__(parent)
        self.controller = ConceptosController()
        self._create_ui()
        self.cargar_conceptos()

    def _create_ui(self):
        top_bar = ttk.Frame(self, padding=8)
        top_bar.pack(fill=tk.X)

        ttk.Button(top_bar, text="🔄 Refrescar Conceptos", command=self.cargar_conceptos).pack(side=tk.LEFT, padx=5)

        info_lbl = ttk.Label(top_bar, text="ℹ️ Los cálculos de la nómina y prestaciones se realizan en Bolívares usando la Tasa BCV automática o manual.", font=("Segoe UI", 9, "italic"))
        info_lbl.pack(side=tk.RIGHT, padx=10)

        columns = ("id", "codigo", "nombre", "tipo", "formula", "valor", "prestaciones")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("nombre", text="Descripción")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("formula", text="Cálculo")
        self.tree.heading("valor", text="Valor / Monto")
        self.tree.heading("prestaciones", text="Incidencia LOTTT")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("codigo", width=120)
        self.tree.column("nombre", width=250)
        self.tree.column("tipo", width=100, anchor=tk.CENTER)
        self.tree.column("formula", width=110, anchor=tk.CENTER)
        self.tree.column("valor", width=110, anchor=tk.E)
        self.tree.column("prestaciones", width=110, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def cargar_conceptos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in self.controller.listar_conceptos():
            val_fmt = f"{r[5]}%" if r[4] == "Porcentaje" else format_bs(r[5])
            incidencia = "SI (Salarial)" if r[6] == 1 else "NO (Excluido)"
            self.tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], val_fmt, incidencia))
