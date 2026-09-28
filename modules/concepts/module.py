from core.base import *
from .views import ConceptsUITab

class ConceptsModule(ModuleBase):
    """Módulo de Configuración de Conceptos de Nómina (Asignaciones y Deducciones Ley)."""

    MANIFEST = {
        "id": "mod_conceptos",
        "nombre": "⚙️ Conceptos de Nómina",
        "version": "1.1.0",
        "autor": "Liceo Dev Team",
        "descripcion": "Definición de leyes venezolanas: IVSS (4%), FAOV (1%), INCES (0.5%), Cestaticket."
    }

    def __init__(self):
        super().__init__(self.MANIFEST)

    def initialize(self):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conceptos_nomina (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    tipo TEXT CHECK(tipo IN ('Asignacion','Deduccion')) NOT NULL,
                    formula_tipo TEXT CHECK(formula_tipo IN ('Porcentaje','Fijo','Cestaticket')) NOT NULL,
                    valor REAL NOT NULL,
                    aplica_prestaciones INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1
                );
            """)

            cursor.execute("SELECT COUNT(*) FROM conceptos_nomina")
            if cursor.fetchone()[0] == 0:
                conceptos_default = [
                    ("ASIG_SUELDO", "Sueldo Base Mensual", "Asignacion", "Fijo", 0.0, 1),
                    ("ASIG_CESTATICKET", "Cestaticket Socialista Ley", "Asignacion", "Cestaticket", 1400.0, 0),
                    ("DED_IVSS", "Seguro Social Obligatorio (IVSS 4%)", "Deduccion", "Porcentaje", 4.0, 0),
                    ("DED_FAOV", "Fondo Ahorro Habitación (FAOV 1%)", "Deduccion", "Porcentaje", 1.0, 0),
                    ("DED_INCES", "Aporte INCES (0.5%)", "Deduccion", "Porcentaje", 0.5, 0),
                ]
                cursor.executemany("""
                    INSERT INTO conceptos_nomina (codigo, nombre, tipo, formula_tipo, valor, aplica_prestaciones)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, conceptos_default)

            conn.commit()

    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        return [ConceptsUITab(parent_notebook)]

    def shutdown(self):
        pass
