from core.base import *
from .views import EmployeeUITab

class EmployeeModule(ModuleBase):
    """Módulo de Gestión de Empleados y Expedientes."""

    MANIFEST = {
        "id": "mod_empleados",
        "nombre": "👥 Gestión de Empleados",
        "version": "1.4.0",
        "autor": "Liceo Dev Team",
        "descripcion": "Gestión de expediente del personal con salario base expresado en USD o Bolívares."
    }

    def __init__(self):
        super().__init__(self.MANIFEST)

    def initialize(self):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula TEXT UNIQUE NOT NULL,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    tipo_personal TEXT DEFAULT 'Docente Tiempo Completo',
                    cargo TEXT,
                    fecha_ingreso TEXT NOT NULL,
                    fecha_egreso TEXT,
                    motivo_egreso TEXT,
                    salario_mensual REAL DEFAULT 0,
                    salario_mensual_usd REAL DEFAULT 0,
                    horas_semanales INTEGER,
                    valor_hora_catedra_usd REAL,
                    departamento TEXT,
                    observaciones TEXT,
                    banco TEXT,
                    cuenta_bancaria TEXT,
                    activo INTEGER DEFAULT 1
                );
            """)

            # ═══ BLOQUE 3: Migración compatible de expedientes existentes ═══
            cursor.execute("PRAGMA table_info(empleados)")
            columns = {row[1] for row in cursor.fetchall()}
            additions = {
                "motivo_egreso": "TEXT",
                "salario_mensual_usd": "REAL DEFAULT 0",
                "horas_semanales": "INTEGER",
                "valor_hora_catedra_usd": "REAL",
                "departamento": "TEXT",
                "observaciones": "TEXT",
            }
            for column, definition in additions.items():
                if column not in columns:
                    cursor.execute(f"ALTER TABLE empleados ADD COLUMN {column} {definition}")
            if "salario_mensual" not in columns:
                cursor.execute("ALTER TABLE empleados ADD COLUMN salario_mensual REAL DEFAULT 0")
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='empleados'")
            table_sql = (cursor.fetchone() or [""])[0].upper()
            tipos_personal = (
                "DOCENTE TIEMPO COMPLETO", "DOCENTE POR HORAS", "ADMINISTRATIVO",
                "OBRERO", "DIRECTIVO", "COORDINADOR",
            )
            if "CHECK" in table_sql and not all(tipo in table_sql for tipo in tipos_personal):
                cursor.execute("PRAGMA foreign_keys = OFF")
                cursor.execute("""
                    CREATE TABLE empleados_nuevo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cedula TEXT UNIQUE NOT NULL,
                        nombres TEXT NOT NULL,
                        apellidos TEXT NOT NULL,
                        tipo_personal TEXT DEFAULT 'Docente Tiempo Completo',
                        cargo TEXT,
                        fecha_ingreso TEXT NOT NULL,
                        fecha_egreso TEXT,
                        motivo_egreso TEXT,
                        salario_mensual REAL DEFAULT 0,
                        salario_mensual_usd REAL DEFAULT 0,
                        horas_semanales INTEGER,
                        valor_hora_catedra_usd REAL,
                        departamento TEXT,
                        observaciones TEXT,
                        banco TEXT,
                        cuenta_bancaria TEXT,
                        activo INTEGER DEFAULT 1
                    )
                """)
                cursor.execute("""
                    INSERT INTO empleados_nuevo
                    (id, cedula, nombres, apellidos, tipo_personal, cargo, fecha_ingreso,
                     fecha_egreso, motivo_egreso, salario_mensual, salario_mensual_usd,
                     horas_semanales, valor_hora_catedra_usd, departamento, observaciones,
                     banco, cuenta_bancaria, activo)
                    SELECT id, cedula, nombres, apellidos,
                           CASE tipo_personal WHEN 'Docente' THEN 'Docente Tiempo Completo' ELSE tipo_personal END,
                           cargo, fecha_ingreso, fecha_egreso, motivo_egreso, salario_mensual,
                           salario_mensual_usd, horas_semanales, valor_hora_catedra_usd,
                           departamento, observaciones, banco, cuenta_bancaria, activo
                    FROM empleados
                """)
                cursor.execute("DROP TABLE empleados")
                cursor.execute("ALTER TABLE empleados_nuevo RENAME TO empleados")
                conn.commit()
                cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("UPDATE empleados SET salario_mensual_usd = COALESCE(NULLIF(salario_mensual_usd, 0), salario_mensual, 0)")
            cursor.execute("UPDATE empleados SET tipo_personal = 'Docente Tiempo Completo' WHERE tipo_personal = 'Docente'")
            conn.commit()

    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        tab = EmployeeUITab(parent_notebook)
        return [tab]

    def shutdown(self):
        pass
