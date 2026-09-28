from core.base import *
from .views import ReportsUITab

class ReportsModule(ModuleBase):
    """Módulo de Exportación de Reportes, Archivos Bancarios TXT y Respaldo en Excel (XLSX)."""

    MANIFEST = {
        "id": "mod_reportes",
        "nombre": "📊 Reportes & Respaldos",
        "version": "1.5.0",
        "autor": "Liceo Dev Team",
        "descripcion": "Generación de TXT bancarios, reportes PDF y respaldos automáticos en Excel (XLSX)."
    }

    def __init__(self):
        super().__init__(self.MANIFEST)

    def initialize(self):
        pass

    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        return [ReportsUITab(parent_notebook)]

    def shutdown(self):
        pass
