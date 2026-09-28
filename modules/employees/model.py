"""Modelo del módulo de empleados.

Este archivo encapsula la entidad principal del dominio y sirve como base
para la separación MVC.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Empleado:
    id: Optional[int] = None
    cedula: str = ""
    nombres: str = ""
    apellidos: str = ""
    tipo_personal: str = "Docente Tiempo Completo"
    departamento: str = ""
    cargo: str = ""
    fecha_ingreso: str = ""
    fecha_egreso: Optional[str] = None
    motivo_egreso: Optional[str] = None
    salario_mensual: float = 0.0
    salario_mensual_usd: float = 0.0
    horas_semanales: Optional[int] = None
    valor_hora_catedra_usd: Optional[float] = None
    observaciones: str = ""
    banco: Optional[str] = None
    cuenta_bancaria: Optional[str] = None
    activo: int = 1
