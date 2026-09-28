import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import app
from core import common as settings
from modules.concepts.controller import ConceptosController
from modules.concepts.module import ConceptsModule
from modules.employees.controller import EmployeeController
from modules.payroll.controller import PayrollController
from modules.users.controller import UsersController


class PayrollWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_name = settings.DB_NAME
        self.original_config_file = settings.CONFIG_FILE
        settings.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        settings.CONFIG_FILE = str(Path(self.temp_dir.name) / "config.json")
        Path(settings.CONFIG_FILE).write_text(
            json.dumps(app.ConfigManager.DEFAULT_CONFIG), encoding="utf-8"
        )
        app.DatabaseManager.init_core_db()
        app.EmployeeModule().initialize()
        app.MonthlyPayrollModule().initialize()
        app.PaymentHistoryModule().initialize()

    def tearDown(self):
        settings.DB_NAME = self.original_db_name
        settings.CONFIG_FILE = self.original_config_file
        self.temp_dir.cleanup()

    def add_employee(self, cedula, tipo, salary=1000, hours=None, rate=None, active=1):
        with app.DatabaseManager.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO empleados
                   (cedula, nombres, apellidos, tipo_personal, fecha_ingreso,
                    salario_mensual, salario_mensual_usd, horas_semanales,
                    valor_hora_catedra_usd, activo)
                   VALUES (?, 'Nombre', 'Prueba', ?, '2020-01-01', ?, ?, ?, ?, ?)""",
                (cedula, tipo, salary, salary, hours, rate, active),
            )
            return cursor.lastrowid

    def test_calculations_for_all_six_personnel_types(self):
        params = app.ConfigManager.load_config()["parametros_laborales"]
        employees = [
            {"tipo_personal": "Docente Tiempo Completo", "salario_mensual_usd": 1000},
            {"tipo_personal": "Docente por Horas", "salario_mensual_usd": 0, "horas_semanales": 10, "valor_hora_catedra_usd": 3.5},
            {"tipo_personal": "Administrativo", "salario_mensual_usd": 1000},
            {"tipo_personal": "Obrero", "salario_mensual_usd": 1000},
            {"tipo_personal": "Directivo", "salario_mensual_usd": 1000},
            {"tipo_personal": "Coordinador", "salario_mensual_usd": 1000},
        ]

        payments = [app.PayrollEngine.calcular_empleado(employee, 40, params) for employee in employees]

        self.assertEqual(payments[0]["sueldo_base_bs"], 20000)
        self.assertEqual(payments[0]["primas_bonos_bs"], 3000)
        self.assertEqual(payments[1]["sueldo_base_bs"], 0)
        self.assertAlmostEqual(payments[1]["horas_catedra_bs"], 3031)
        self.assertAlmostEqual(payments[1]["primas_bonos_bs"], 303.1)
        self.assertEqual(payments[2]["primas_bonos_bs"], 1000)
        self.assertEqual(payments[3]["primas_bonos_bs"], 600)
        self.assertEqual(payments[4]["primas_bonos_bs"], 3000)
        self.assertEqual(payments[5]["primas_bonos_bs"], 3000)
        self.assertTrue(all(payment["cestaticket_bs"] == 800 for payment in payments))

    def test_employee_controller_creates_updates_and_registers_exit(self):
        employee_id = EmployeeController.crear_empleado({
            "cedula": "MVC-1", "nombres": "Ana", "apellidos": "Prueba",
            "tipo": "Administrativo", "departamento": "Dirección",
            "ingreso": "2025-01-01", "salario": 900,
        })
        self.assertEqual(EmployeeController.listar_todos()[0][0], employee_id)
        EmployeeController.actualizar_empleado(employee_id, {
            "cedula": "MVC-1", "nombres": "Ana", "apellidos": "Prueba",
            "tipo": "Administrativo", "departamento": "Dirección",
            "ingreso": "2025-01-01", "salario": 1000,
        })
        self.assertTrue(EmployeeController.registrar_egreso(employee_id, "2026-01-01", "Renuncia voluntaria"))
        self.assertEqual(EmployeeController.listar_empleados(), [])

    def test_concept_and_user_controllers_use_their_repositories(self):
        ConceptsModule().initialize()
        self.assertEqual(len(ConceptosController.listar_conceptos()), 5)
        user_id = UsersController.crear_usuario("operator", "secret", "usuario")
        self.assertTrue(any(row[0] == user_id for row in UsersController.listar_usuarios()))
        self.assertTrue(UsersController.cambiar_estado(user_id, 0))
        user = next(row for row in UsersController.listar_usuarios() if row[0] == user_id)
        self.assertEqual(user[3], 0)

    def test_processing_writes_one_receipt_and_history_row_per_active_employee(self):
        kinds = [
            ("Docente Tiempo Completo", 1000, None, None),
            ("Docente por Horas", 0, 10, 3.5),
            ("Administrativo", 1000, None, None),
            ("Obrero", 1000, None, None),
            ("Directivo", 1000, None, None),
            ("Coordinador", 1000, None, None),
        ]
        for index, (kind, salary, hours, rate) in enumerate(kinds):
            self.add_employee(f"ACTIVE-{index}", kind, salary, hours, rate)
        self.add_employee("INACTIVE", "Obrero", 1000, active=0)

        result = app.PayrollEngine.procesar_nomina("1RA QUINCENA", 40, "tester")

        with app.DatabaseManager.get_connection() as conn:
            history_rows = conn.execute(
                "SELECT empleado_id, horas_catedra_bs, sueldo_base_bs FROM historico_pagos WHERE nomina_id=?",
                (result["nomina_id"],),
            ).fetchall()
            receipt_count = conn.execute(
                "SELECT COUNT(*) FROM recibos_detalle WHERE nomina_id=?",
                (result["nomina_id"],),
            ).fetchone()[0]
        self.assertEqual(result["cantidad_empleados"], 6)
        self.assertEqual(len(history_rows), 6)
        self.assertEqual(receipt_count, 6)
        today = date.today().isoformat()
        self.assertEqual(len(PayrollController.consultar_historico(None, today, today)), 6)
        hourly_row = next(row for row in history_rows if row[1] > 0)
        self.assertEqual(hourly_row[2], 0)

    def test_severance_uses_recent_average_and_falls_back_for_new_employee(self):
        employee_id = self.add_employee("HIST-1", "Docente Tiempo Completo")
        with app.DatabaseManager.get_connection() as conn:
            for days_ago, salary_integral in ((30, 100), (60, 300), (181, 900)):
                conn.execute(
                    """INSERT INTO historico_pagos
                       (empleado_id, periodo, fecha_pago, tasa_bcv, salario_integral_diario_bs)
                       VALUES (?, 'P', ?, 40, ?)""",
                    (employee_id, (date.today() - timedelta(days=days_ago)).isoformat(), salary_integral),
                )
        employee = {
            "id": employee_id, "cedula": "HIST-1", "nombres": "Nombre", "apellidos": "Prueba",
            "cargo": "Docente", "fecha_ingreso": "2020-01-01", "tipo_personal": "Docente Tiempo Completo",
            "salario_mensual": 1000, "salario_mensual_usd": 1000,
        }
        historical = app.SeveranceEngine.calcular_prestaciones(employee, date.today().isoformat(), 40)

        self.assertEqual(historical["salario_integral_diario"], 200)
        self.assertEqual(historical["cantidad_periodos_historicos"], 2)
        self.assertEqual(historical["origen_salario_integral"], "Histórico real (2 períodos)")

        new_employee_id = self.add_employee("NEW-1", "Docente por Horas", 0, 20, 3.5)
        fallback = app.SeveranceEngine.calcular_prestaciones(
            {
                "id": new_employee_id, "cedula": "NEW-1", "nombres": "Nuevo", "apellidos": "Empleado",
                "cargo": "Docente", "fecha_ingreso": "2025-01-01", "tipo_personal": "Docente por Horas",
                "salario_mensual": 0, "salario_mensual_usd": 0, "horas_semanales": 20,
                "valor_hora_catedra_usd": 3.5,
            },
            date.today().isoformat(),
            40,
        )
        self.assertGreater(fallback["salario_integral_diario"], 0)
        self.assertEqual(fallback["origen_salario_integral"], "Calculado con sueldo actual (sin histórico)")


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_name = settings.DB_NAME
        self.original_config_file = settings.CONFIG_FILE
        settings.DB_NAME = str(Path(self.temp_dir.name) / "legacy.db")
        settings.CONFIG_FILE = str(Path(self.temp_dir.name) / "config.json")

    def tearDown(self):
        settings.DB_NAME = self.original_db_name
        settings.CONFIG_FILE = self.original_config_file
        self.temp_dir.cleanup()

    def test_legacy_employee_migration_preserves_receipts_and_foreign_keys(self):
        with app.DatabaseManager.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, cedula TEXT UNIQUE NOT NULL,
                    nombres TEXT NOT NULL, apellidos TEXT NOT NULL,
                    tipo_personal TEXT CHECK(tipo_personal IN ('Docente','Administrativo','Obrero')) DEFAULT 'Docente',
                    cargo TEXT, fecha_ingreso TEXT NOT NULL, fecha_egreso TEXT,
                    salario_mensual REAL NOT NULL, banco TEXT, cuenta_bancaria TEXT, activo INTEGER DEFAULT 1
                );
                CREATE TABLE nominas_generadas (
                    id INTEGER PRIMARY KEY, periodo TEXT NOT NULL, tasa_bcv REAL NOT NULL DEFAULT 1,
                    fecha_proceso TEXT, total_asignaciones REAL NOT NULL, total_deducciones REAL NOT NULL,
                    total_neto REAL NOT NULL, procesado_por TEXT NOT NULL
                );
                CREATE TABLE recibos_detalle (
                    id INTEGER PRIMARY KEY, nomina_id INTEGER NOT NULL REFERENCES nominas_generadas(id),
                    empleado_id INTEGER NOT NULL REFERENCES empleados(id), salario_base REAL NOT NULL,
                    cestaticket REAL NOT NULL, ivss REAL NOT NULL, faov REAL NOT NULL,
                    inces REAL NOT NULL, neto_cobrar REAL NOT NULL
                );
                INSERT INTO empleados (cedula,nombres,apellidos,tipo_personal,cargo,fecha_ingreso,salario_mensual)
                    VALUES ('LEG-1','Ana','Docente','Docente','Docente','2020-01-01',800);
                INSERT INTO nominas_generadas (id,periodo,tasa_bcv,total_asignaciones,total_deducciones,total_neto,procesado_por)
                    VALUES (1,'P',40,1,0,1,'admin');
                INSERT INTO recibos_detalle (nomina_id,empleado_id,salario_base,cestaticket,ivss,faov,inces,neto_cobrar)
                    VALUES (1,1,1,0,0,0,0,1);
            """)

        app.EmployeeModule().initialize()

        with app.DatabaseManager.get_connection() as conn:
            employee = conn.execute(
                "SELECT tipo_personal,salario_mensual_usd FROM empleados WHERE cedula='LEG-1'"
            ).fetchone()
            receipt_count = conn.execute("SELECT COUNT(*) FROM recibos_detalle").fetchone()[0]
            fk_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
        self.assertEqual(employee, ("Docente Tiempo Completo", 800.0))
        self.assertEqual(receipt_count, 1)
        self.assertEqual(fk_issues, [])

    def test_old_config_adds_history_once_and_allows_disabling_it(self):
        Path(settings.CONFIG_FILE).write_text(
            json.dumps({"sistema": {"version": "2.5.0"}, "modulos_activos": ["mod_empleados"]}),
            encoding="utf-8",
        )
        migrated = app.ConfigManager.load_config()
        self.assertIn("mod_historico_pagos", migrated["modulos_activos"])
        self.assertEqual(migrated["sistema"]["version"], "3.0.0")
        self.assertEqual(migrated["institucion"]["nombre"], "Colegio Huyapari")

        app.ConfigManager.toggle_module("mod_historico_pagos", False)
        self.assertFalse(app.ConfigManager.is_module_active("mod_historico_pagos"))


if __name__ == "__main__":
    unittest.main()