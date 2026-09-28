from core.base import *
from .views import SeveranceUITab

class SeveranceModule(ModuleBase):
    """Módulo de Liquidación y Prestaciones Sociales con Tasa BCV y PDF."""

    MANIFEST = {
        "id": "mod_prestaciones",
        "nombre": "💰 Prestaciones LOTTT",
        "version": "2.3.0",
        "autor": "Liceo Dev Team",
        "descripcion": "Cálculo con garantía trimestral, días adicionales y retroactivo en Bolívares a tasa BCV."
    }

    def __init__(self):
        super().__init__(self.MANIFEST)

    def initialize(self):
        pass

    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        return [SeveranceUITab(parent_notebook)]

    def shutdown(self):
        pass
