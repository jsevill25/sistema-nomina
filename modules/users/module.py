from core.base import *
from .views import UsersUITab

class UsersModule(ModuleBase):
    """Módulo de Control de Usuarios y Roles."""

    MANIFEST = {
        "id": "mod_usuarios",
        "nombre": "👥 Gestión de Usuarios",
        "version": "1.0.0",
        "autor": "Liceo Dev Team",
        "descripcion": "Administración de accesos de operadores del sistema."
    }

    def __init__(self):
        super().__init__(self.MANIFEST)

    def initialize(self):
        pass

    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        if AuthController.es_admin():
            return [UsersUITab(parent_notebook)]
        return []

    def shutdown(self):
        pass
