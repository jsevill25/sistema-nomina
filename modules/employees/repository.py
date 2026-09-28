"""Repositorio del módulo de empleados."""

from core import DatabaseManager


class EmpleadoRepository:
    """Acceso a datos para empleados."""

    @staticmethod
    def listar_activos():
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT id, cedula, nombres, apellidos, tipo_personal,
                                     departamento, cargo, fecha_ingreso, salario_mensual_usd, activo
                              FROM empleados WHERE activo = 1 ORDER BY apellidos, nombres""")
            return cursor.fetchall()

    @staticmethod
    def listar_todos():
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT id, cedula, nombres, apellidos, tipo_personal, departamento,
                                     cargo, fecha_ingreso, salario_mensual_usd, activo
                              FROM empleados ORDER BY apellidos, nombres""")
            return cursor.fetchall()

    @staticmethod
    def obtener_para_edicion(empleado_id):
        with DatabaseManager.get_connection() as conn:
            return conn.execute(
                """SELECT id, cedula, nombres, apellidos, tipo_personal, cargo, fecha_ingreso,
                          salario_mensual_usd, banco, cuenta_bancaria, departamento,
                          horas_semanales, valor_hora_catedra_usd, observaciones
                   FROM empleados WHERE id = ?""",
                (empleado_id,),
            ).fetchone()

    @staticmethod
    def guardar(empleado):
        data = empleado if isinstance(empleado, dict) else vars(empleado)
        salario_usd = data.get("salario_mensual_usd", data.get("salario", 0)) or 0
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO empleados
                (cedula, nombres, apellidos, tipo_personal, departamento, cargo, fecha_ingreso,
                 salario_mensual, salario_mensual_usd, horas_semanales, valor_hora_catedra_usd,
                 observaciones, banco, cuenta_bancaria, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.get("cedula", ""), data.get("nombres", ""), data.get("apellidos", ""),
                    data.get("tipo_personal", data.get("tipo", "Docente Tiempo Completo")),
                    data.get("departamento", ""), data.get("cargo", ""),
                    data.get("fecha_ingreso", data.get("ingreso", "")), salario_usd, salario_usd,
                    data.get("horas_semanales", data.get("horas")),
                    data.get("valor_hora_catedra_usd", data.get("valor_hora")),
                    data.get("observaciones", ""), data.get("banco", ""),
                    data.get("cuenta_bancaria", data.get("cuenta", "")), data.get("activo", 1),
                ),
            )
            return cursor.lastrowid

    @staticmethod
    def actualizar(empleado_id, empleado):
        data = empleado if isinstance(empleado, dict) else vars(empleado)
        salario_usd = data.get("salario_mensual_usd", data.get("salario", 0)) or 0
        with DatabaseManager.get_connection() as conn:
            conn.execute(
                """UPDATE empleados SET cedula=?, nombres=?, apellidos=?, tipo_personal=?,
                   departamento=?, cargo=?, fecha_ingreso=?, salario_mensual=?, salario_mensual_usd=?,
                   horas_semanales=?, valor_hora_catedra_usd=?, observaciones=?, banco=?, cuenta_bancaria=?
                   WHERE id=?""",
                (
                    data["cedula"], data["nombres"], data["apellidos"], data.get("tipo_personal", data.get("tipo")),
                    data.get("departamento", ""), data.get("cargo", ""), data.get("fecha_ingreso", data.get("ingreso")),
                    salario_usd, salario_usd, data.get("horas_semanales", data.get("horas")),
                    data.get("valor_hora_catedra_usd", data.get("valor_hora")), data.get("observaciones", ""),
                    data.get("banco", ""), data.get("cuenta_bancaria", data.get("cuenta", "")), empleado_id,
                ),
            )

    @staticmethod
    def registrar_egreso(empleado_id, fecha_egreso, motivo):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE empleados SET fecha_egreso=?, motivo_egreso=?, activo=0 WHERE id=? AND activo=1",
                (fecha_egreso, motivo, empleado_id),
            )
            return cursor.rowcount == 1

    @staticmethod
    def eliminar(empleado_id):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.execute("DELETE FROM empleados WHERE id=?", (empleado_id,))
            return cursor.rowcount == 1
