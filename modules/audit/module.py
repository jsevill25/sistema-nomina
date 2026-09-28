from core.base import *
from .views import AuditUITab

class AuditModule(ModuleBase):
    """Módulo de Consulta de Bitácora de Auditoría."""

    MANIFEST = {
        "id": "mod_auditoria",
        "nombre": "📋 Bitácora de Auditoría",
        "version": "1.0.0",
        "autor": "Liceo Dev Team",
        "descripcion": "Visualización de eventos de seguridad y modificaciones."
    }

    def __init__(self):
        super().__init__(self.MANIFEST)

    def initialize(self):
        pass

    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        if AuthController.es_admin():
            return [AuditUITab(parent_notebook)]
        return []

    def shutdown(self):
        pass
