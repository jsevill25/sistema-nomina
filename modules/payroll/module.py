from core.base import *
from .views import PayrollUITab, PaymentHistoryUITab

class MonthlyPayrollModule(ModuleBase):
    """Módulo de Generación y Procesamiento de Nómina Quincenal / Mensual con Tasa BCV Automática/Manual y PDF."""

    MANIFEST = {
        "id": "mod_nomina_mensual",
        "nombre": "🗓️ Procesamiento de Nómina",
        "version": "1.8.0",
        "autor": "Liceo Dev Team",
        "descripcion": "Cálculo masivo de recibos de pago con tasa BCV automática API/manual y exportación PDF."
    }

    def __init__(self):
        super().__init__(self.MANIFEST)

    def initialize(self):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nominas_generadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    periodo TEXT NOT NULL,
                    tasa_bcv REAL NOT NULL DEFAULT 1.0,
                    fecha_proceso TEXT DEFAULT CURRENT_TIMESTAMP,
                    total_asignaciones REAL NOT NULL,
                    total_deducciones REAL NOT NULL,
                    total_neto REAL NOT NULL,
                    procesado_por TEXT NOT NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recibos_detalle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nomina_id INTEGER NOT NULL,
                    empleado_id INTEGER NOT NULL,
                    salario_base REAL NOT NULL,
                    cestaticket REAL NOT NULL,
                    ivss REAL NOT NULL,
                    faov REAL NOT NULL,
                    inces REAL NOT NULL,
                    neto_cobrar REAL NOT NULL,
                    FOREIGN KEY (nomina_id) REFERENCES nominas_generadas(id) ON DELETE CASCADE,
                    FOREIGN KEY (empleado_id) REFERENCES empleados(id)
                );
            """)

            # ═══ BLOQUE 7: Histórico persistente y extensión de recibos ═══
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico_pagos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id INTEGER NOT NULL,
                    nomina_id INTEGER,
                    periodo TEXT NOT NULL,
                    fecha_pago TEXT NOT NULL,
                    tasa_bcv REAL NOT NULL,
                    sueldo_base_bs REAL NOT NULL DEFAULT 0,
                    horas_catedra_bs REAL NOT NULL DEFAULT 0,
                    cestaticket_bs REAL NOT NULL DEFAULT 0,
                    primas_bonos_bs REAL NOT NULL DEFAULT 0,
                    total_asignaciones_bs REAL NOT NULL DEFAULT 0,
                    ivss_bs REAL NOT NULL DEFAULT 0,
                    faov_bs REAL NOT NULL DEFAULT 0,
                    inces_bs REAL NOT NULL DEFAULT 0,
                    otras_deducciones_bs REAL NOT NULL DEFAULT 0,
                    total_deducciones_bs REAL NOT NULL DEFAULT 0,
                    neto_pagado_bs REAL NOT NULL DEFAULT 0,
                    salario_integral_diario_bs REAL NOT NULL DEFAULT 0,
                    tipo_pago TEXT DEFAULT 'Quincenal',
                    procesado_por TEXT,
                    FOREIGN KEY (empleado_id) REFERENCES empleados(id),
                    FOREIGN KEY (nomina_id) REFERENCES nominas_generadas(id)
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_empleado_fecha ON historico_pagos (empleado_id, fecha_pago)")
            cursor.execute("PRAGMA table_info(recibos_detalle)")
            receipt_columns = {row[1] for row in cursor.fetchall()}
            receipt_additions = {
                "horas_catedra": "REAL DEFAULT 0",
                "primas_bonos": "REAL DEFAULT 0",
                "total_asignaciones": "REAL DEFAULT 0",
                "otras_deducciones": "REAL DEFAULT 0",
                "total_deducciones": "REAL DEFAULT 0",
                "salario_integral_diario": "REAL DEFAULT 0",
            }
            for column, definition in receipt_additions.items():
                if column not in receipt_columns:
                    cursor.execute(f"ALTER TABLE recibos_detalle ADD COLUMN {column} {definition}")
            conn.commit()

    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        return [PayrollUITab(parent_notebook)]

    def shutdown(self):
        pass


class PaymentHistoryModule(ModuleBase):
    """Consulta y exportación del histórico persistente de pagos."""

    MANIFEST = {
        "id": "mod_historico_pagos",
        "nombre": "📚 Histórico de Pagos",
        "version": "1.0.0",
        "autor": "Colegio Huyapari",
        "descripcion": "Consulta de pagos quincenales y sus salarios integrales históricos."
    }

    def __init__(self):
        super().__init__(self.MANIFEST)

    def initialize(self):
        with DatabaseManager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historico_pagos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id INTEGER NOT NULL,
                    nomina_id INTEGER,
                    periodo TEXT NOT NULL,
                    fecha_pago TEXT NOT NULL,
                    tasa_bcv REAL NOT NULL,
                    sueldo_base_bs REAL NOT NULL DEFAULT 0,
                    horas_catedra_bs REAL NOT NULL DEFAULT 0,
                    cestaticket_bs REAL NOT NULL DEFAULT 0,
                    primas_bonos_bs REAL NOT NULL DEFAULT 0,
                    total_asignaciones_bs REAL NOT NULL DEFAULT 0,
                    ivss_bs REAL NOT NULL DEFAULT 0,
                    faov_bs REAL NOT NULL DEFAULT 0,
                    inces_bs REAL NOT NULL DEFAULT 0,
                    otras_deducciones_bs REAL NOT NULL DEFAULT 0,
                    total_deducciones_bs REAL NOT NULL DEFAULT 0,
                    neto_pagado_bs REAL NOT NULL DEFAULT 0,
                    salario_integral_diario_bs REAL NOT NULL DEFAULT 0,
                    tipo_pago TEXT DEFAULT 'Quincenal',
                    procesado_por TEXT,
                    FOREIGN KEY (empleado_id) REFERENCES empleados(id),
                    FOREIGN KEY (nomina_id) REFERENCES nominas_generadas(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_historico_empleado_fecha ON historico_pagos (empleado_id, fecha_pago)")

    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        return [PaymentHistoryUITab(parent_notebook)]

    def shutdown(self):
        pass
