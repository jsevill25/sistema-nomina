"""Consultas y persistencia del dominio de nómina."""

from core import DatabaseManager


class PayrollRepository:
    @staticmethod
    def listar_empleados():
        with DatabaseManager.get_connection() as conn:
            return conn.execute(
                "SELECT id, cedula, nombres, apellidos FROM empleados ORDER BY apellidos, nombres"
            ).fetchall()

    @staticmethod
    def listar_nominas():
        with DatabaseManager.get_connection() as conn:
            return conn.execute(
                """SELECT id, periodo, tasa_bcv, fecha_proceso, total_asignaciones,
                          total_deducciones, total_neto, procesado_por
                   FROM nominas_generadas ORDER BY id DESC"""
            ).fetchall()

    @staticmethod
    def listar_empleados_activos():
        with DatabaseManager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM empleados WHERE activo=1 ORDER BY id")
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def guardar_nomina(periodo, tasa_bcv, procesado_por, tipo_pago, fecha_pago, calculos, totales):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO nominas_generadas
                   (periodo, tasa_bcv, total_asignaciones, total_deducciones, total_neto, procesado_por)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (periodo, tasa_bcv, totales["asignaciones"], totales["deducciones"], totales["neto"], procesado_por),
            )
            nomina_id = cursor.lastrowid

            for empleado, pago in calculos:
                conn.execute(
                    """INSERT INTO recibos_detalle
                       (nomina_id, empleado_id, salario_base, cestaticket, ivss, faov, inces,
                        neto_cobrar, horas_catedra, primas_bonos, total_asignaciones,
                        otras_deducciones, total_deducciones, salario_integral_diario)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        nomina_id, empleado["id"], pago["sueldo_base_bs"], pago["cestaticket_bs"],
                        pago["ivss_bs"], pago["faov_bs"], pago["inces_bs"], pago["neto_pagado_bs"],
                        pago["horas_catedra_bs"], pago["primas_bonos_bs"], pago["total_asignaciones_bs"],
                        pago["otras_deducciones_bs"], pago["total_deducciones_bs"],
                        pago["salario_integral_diario_bs"],
                    ),
                )
                conn.execute(
                    """INSERT INTO historico_pagos
                       (empleado_id, nomina_id, periodo, fecha_pago, tasa_bcv, sueldo_base_bs,
                        horas_catedra_bs, cestaticket_bs, primas_bonos_bs, total_asignaciones_bs,
                        ivss_bs, faov_bs, inces_bs, otras_deducciones_bs, total_deducciones_bs,
                        neto_pagado_bs, salario_integral_diario_bs, tipo_pago, procesado_por)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        empleado["id"], nomina_id, periodo, fecha_pago, tasa_bcv, pago["sueldo_base_bs"],
                        pago["horas_catedra_bs"], pago["cestaticket_bs"], pago["primas_bonos_bs"],
                        pago["total_asignaciones_bs"], pago["ivss_bs"], pago["faov_bs"], pago["inces_bs"],
                        pago["otras_deducciones_bs"], pago["total_deducciones_bs"], pago["neto_pagado_bs"],
                        pago["salario_integral_diario_bs"], tipo_pago, procesado_por,
                    ),
                )
            conn.commit()
            return nomina_id

    @staticmethod
    def listar_historico(empleado_id, fecha_desde, fecha_hasta):
        with DatabaseManager.get_connection() as conn:
            return conn.execute(
                """SELECT h.id, h.periodo, h.fecha_pago, h.tasa_bcv, h.sueldo_base_bs,
                          h.horas_catedra_bs, h.cestaticket_bs, h.primas_bonos_bs,
                          h.total_asignaciones_bs, h.total_deducciones_bs, h.neto_pagado_bs,
                          h.salario_integral_diario_bs, e.cedula, e.nombres, e.apellidos
                   FROM historico_pagos h JOIN empleados e ON e.id = h.empleado_id
                   WHERE (? IS NULL OR h.empleado_id = ?)
                     AND date(h.fecha_pago) BETWEEN date(?) AND date(?)
                   ORDER BY date(h.fecha_pago), h.id""",
                (empleado_id, empleado_id, fecha_desde, fecha_hasta),
            ).fetchall()
