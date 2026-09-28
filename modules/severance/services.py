from core.base import *
from modules.payroll.services import PayrollEngine

class SeveranceEngine:
    """Motor de cálculo exacto según Ley Orgánica del Trabajo de Venezuela (LOTTT Art. 142) con Tasa BCV."""

    @staticmethod
    def calcular_prestaciones(emp_data: dict, fecha_calculo_str: str, tasa_bcv: float) -> dict:
        fecha_ingreso = parse_date(emp_data["fecha_ingreso"])
        fecha_fin = parse_date(fecha_calculo_str)

        if fecha_fin < fecha_ingreso:
            raise ValueError("La fecha de cálculo no puede ser anterior al ingreso del empleado.")

        dias_totales = (fecha_fin - fecha_ingreso).days
        anos_servicio = fecha_fin.year - fecha_ingreso.year
        meses_servicio = fecha_fin.month - fecha_ingreso.month
        dias_resto = fecha_fin.day - fecha_ingreso.day

        if dias_resto < 0:
            meses_servicio -= 1
        if meses_servicio < 0:
            anos_servicio -= 1
            meses_servicio += 12

        total_meses = (anos_servicio * 12) + meses_servicio

        parametros = ConfigManager.load_config().get("parametros_laborales", {})
        dias_utilidades = float(parametros.get("dias_utilidades", 30))
        dias_bono_vac = float(parametros.get("dias_bono_vacacional_base", 15))
        salario_integral_diario = 0.0
        cantidad_periodos = 0
        empleado_id = emp_data.get("id")
        if empleado_id is not None:
            fecha_desde = (fecha_fin - timedelta(days=180)).isoformat()
            try:
                with DatabaseManager.get_connection() as conn:
                    row = conn.execute(
                        """SELECT AVG(salario_integral_diario_bs), COUNT(*)
                           FROM historico_pagos
                           WHERE empleado_id = ?
                             AND date(fecha_pago) BETWEEN date(?) AND date(?)""",
                        (empleado_id, fecha_desde, fecha_fin.isoformat()),
                    ).fetchone()
                salario_integral_diario = float(row[0] or 0)
                cantidad_periodos = int(row[1] or 0)
            except sqlite3.OperationalError:
                cantidad_periodos = 0

        factor_integral = 1.0 + (dias_utilidades + dias_bono_vac) / 360.0
        if cantidad_periodos:
            origen_salario_integral = f"Histórico real ({cantidad_periodos} períodos)"
            salario_diario = salario_integral_diario / factor_integral
        else:
            origen_salario_integral = "Calculado con sueldo actual (sin histórico)"
            pago_actual = PayrollEngine.calcular_empleado(emp_data, tasa_bcv, parametros)
            base_mensual_bs = (
                pago_actual["sueldo_base_bs"]
                + pago_actual["horas_catedra_bs"]
                + pago_actual["primas_bonos_bs"]
            ) * 2.0
            salario_diario = base_mensual_bs / 30.0
            alicuota_util = (salario_diario * dias_utilidades) / 360.0
            alicuota_vac = (salario_diario * dias_bono_vac) / 360.0
            salario_integral_diario = salario_diario + alicuota_util + alicuota_vac

        salario_mensual = salario_diario * 30.0
        alicuota_util = (salario_diario * dias_utilidades) / 360.0
        alicuota_vac = (salario_diario * dias_bono_vac) / 360.0

        num_trimestres = total_meses // 3
        dias_literal_a = num_trimestres * 15
        monto_literal_a = dias_literal_a * salario_integral_diario

        if anos_servicio >= 2:
            dias_literal_b = min((anos_servicio - 1) * 2, 30)
        else:
            dias_literal_b = 0
        monto_literal_b = dias_literal_b * salario_integral_diario

        subtotal_ab = monto_literal_a + monto_literal_b

        anos_c = anos_servicio
        if meses_servicio > 6 or (anos_servicio == 0 and total_meses > 6):
            anos_c += 1
        elif anos_servicio == 0 and total_meses <= 6 and total_meses > 0:
            anos_c = 1

        dias_literal_c = anos_c * 30
        monto_literal_c = dias_literal_c * salario_integral_diario

        monto_definitivo = max(subtotal_ab, monto_literal_c)
        favorable = "Garantía Trimestral + Días Adicionales (Art. 142 a + b)" if subtotal_ab >= monto_literal_c else "Cálculo Retroactivo (Art. 142 c)"

        return {
            "nombre_completo": f"{emp_data['nombres']} {emp_data['apellidos']}",
            "cedula": emp_data["cedula"],
            "cargo": emp_data.get("cargo") or "N/A",
            "tipo_personal": emp_data.get("tipo_personal") or "N/A",
            "fecha_ingreso": fecha_ingreso.strftime("%d/%m/%Y"),
            "fecha_calculo": fecha_fin.strftime("%d/%m/%Y"),
            "tasa_bcv": tasa_bcv,
            "antiguedad_str": f"{anos_servicio} años, {meses_servicio} meses",
            "dias_totales": dias_totales,
            "salario_mensual": salario_mensual,
            "salario_diario": salario_diario,
            "alicuota_utilidades": alicuota_util,
            "alicuota_bono_vacacional": alicuota_vac,
            "salario_integral_diario": salario_integral_diario,
            "origen_salario_integral": origen_salario_integral,
            "cantidad_periodos_historicos": cantidad_periodos,
            "num_trimestres": num_trimestres,
            "dias_literal_a": dias_literal_a,
            "monto_literal_a": monto_literal_a,
            "dias_literal_b": dias_literal_b,
            "monto_literal_b": monto_literal_b,
            "subtotal_ab": subtotal_ab,
            "anos_c": anos_c,
            "dias_literal_c": dias_literal_c,
            "monto_literal_c": monto_literal_c,
            "monto_definitivo": monto_definitivo,
            "concepto_favorable": favorable
        }


def calcular_antiguedad(fecha_ingreso, fecha_calculo):
    """Devuelve años, meses y días transcurridos entre dos fechas ISO."""
    ingreso = parse_date(fecha_ingreso)
    calculo = parse_date(fecha_calculo)
    if calculo < ingreso:
        raise ValueError("La fecha de cálculo no puede ser anterior al ingreso del empleado.")
    dias = (calculo - ingreso).days
    anos = calculo.year - ingreso.year
    meses = calculo.month - ingreso.month
    if calculo.day < ingreso.day:
        meses -= 1
    if meses < 0:
        anos -= 1
        meses += 12
    return {"anos": anos, "meses": meses, "dias": dias}
