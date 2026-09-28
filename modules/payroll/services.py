from core.base import *

class PayrollEngine:
    """Calcula asignaciones, deducciones y salario integral en Bolívares."""

    @staticmethod
    def calcular_empleado(emp_row, tasa_bcv, parametros):
        emp = dict(emp_row)
        tipo = emp.get("tipo_personal", "Docente Tiempo Completo")
        tasa = float(tasa_bcv)
        salario_usd = float(emp.get("salario_mensual_usd") or emp.get("salario_mensual") or 0)
        horas = float(emp.get("horas_semanales") or 0)
        valor_hora = float(emp.get("valor_hora_catedra_usd") or parametros.get("valor_hora_catedra_base_usd", 3.50))
        sueldo_base_bs = 0.0
        horas_catedra_bs = 0.0
        primas_bonos_bs = 0.0

        if tipo == "Docente por Horas":
            pago_mensual_usd = horas * 4.33 * valor_hora
            horas_catedra_bs = pago_mensual_usd * tasa / 2.0
            primas_bonos_bs = horas_catedra_bs * 0.10
        else:
            sueldo_base_bs = salario_usd * tasa / 2.0
            if tipo == "Docente Tiempo Completo" or tipo in ("Directivo", "Coordinador"):
                primas_bonos_bs = sueldo_base_bs * 0.15
            elif tipo == "Administrativo":
                primas_bonos_bs = sueldo_base_bs * 0.05
            elif tipo == "Obrero":
                primas_bonos_bs = sueldo_base_bs * 0.03

        cestaticket_bs = float(parametros.get("cestaticket_mensual_usd", 40.0)) * tasa / 2.0
        base_quincenal = sueldo_base_bs + horas_catedra_bs + primas_bonos_bs
        ivss_bs = base_quincenal * float(parametros.get("porcentaje_ivss", 4.0)) / 100.0
        faov_bs = base_quincenal * float(parametros.get("porcentaje_faov", 1.0)) / 100.0
        inces_bs = base_quincenal * float(parametros.get("porcentaje_inces", 0.5)) / 100.0
        total_asignaciones_bs = base_quincenal + cestaticket_bs
        total_deducciones_bs = ivss_bs + faov_bs + inces_bs

        salario_diario_bs = base_quincenal * 2.0 / 30.0
        alicuota_utilidades_bs = salario_diario_bs * float(parametros.get("dias_utilidades", 30)) / 360.0
        alicuota_vacacional_bs = salario_diario_bs * float(parametros.get("dias_bono_vacacional_base", 15)) / 360.0
        return {
            "sueldo_base_bs": sueldo_base_bs,
            "horas_catedra_bs": horas_catedra_bs,
            "cestaticket_bs": cestaticket_bs,
            "primas_bonos_bs": primas_bonos_bs,
            "total_asignaciones_bs": total_asignaciones_bs,
            "ivss_bs": ivss_bs,
            "faov_bs": faov_bs,
            "inces_bs": inces_bs,
            "otras_deducciones_bs": 0.0,
            "total_deducciones_bs": total_deducciones_bs,
            "neto_pagado_bs": total_asignaciones_bs - total_deducciones_bs,
            "salario_integral_diario_bs": salario_diario_bs + alicuota_utilidades_bs + alicuota_vacacional_bs,
        }

    @staticmethod
    def procesar_nomina(periodo, tasa_bcv, procesado_por, tipo_pago="Quincenal"):
        from .controller import PayrollController

        return PayrollController.procesar_nomina(periodo, tasa_bcv, procesado_por, tipo_pago)


def calcular_nomina_simple(salario_mensual, tasa_bcv):
    """Compatibilidad para cálculos simples; el flujo usa PayrollEngine."""
    parametros = ConfigManager.DEFAULT_CONFIG["parametros_laborales"]
    empleado = {
        "tipo_personal": "Docente Tiempo Completo",
        "salario_mensual_usd": salario_mensual,
    }
    return PayrollEngine.calcular_empleado(empleado, tasa_bcv, parametros)
