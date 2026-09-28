"""Casos de uso de nómina e histórico de pagos."""

from datetime import datetime

from core import ConfigManager
from .repository import PayrollRepository
from .services import PayrollEngine


class PayrollController:
    @staticmethod
    def listar_empleados():
        return PayrollRepository.listar_empleados()

    @staticmethod
    def listar_nominas():
        return PayrollRepository.listar_nominas()

    @staticmethod
    def procesar_nomina(periodo, tasa_bcv, procesado_por, tipo_pago="Quincenal"):
        if not periodo or float(tasa_bcv) <= 0:
            raise ValueError("El período es obligatorio y la tasa BCV debe ser positiva.")
        empleados = PayrollRepository.listar_empleados_activos()
        if not empleados:
            raise ValueError("No hay empleados activos para procesar la nómina.")

        parametros = ConfigManager.load_config().get("parametros_laborales", {})
        calculos = [
            (empleado, PayrollEngine.calcular_empleado(empleado, tasa_bcv, parametros))
            for empleado in empleados
        ]
        totales = {
            "asignaciones": sum(pago["total_asignaciones_bs"] for _, pago in calculos),
            "deducciones": sum(pago["total_deducciones_bs"] for _, pago in calculos),
            "neto": sum(pago["neto_pagado_bs"] for _, pago in calculos),
        }
        nomina_id = PayrollRepository.guardar_nomina(
            periodo, tasa_bcv, procesado_por, tipo_pago,
            datetime.now().strftime("%Y-%m-%d"), calculos, totales,
        )
        return {
            "nomina_id": nomina_id,
            "cantidad_empleados": len(calculos),
            "total_asignaciones": totales["asignaciones"],
            "total_deducciones": totales["deducciones"],
            "total_neto": totales["neto"],
            "calculos": calculos,
        }

    @staticmethod
    def consultar_historico(empleado_id, fecha_desde, fecha_hasta):
        return PayrollRepository.listar_historico(empleado_id, fecha_desde, fecha_hasta)
