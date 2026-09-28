"""Modelo del módulo de conceptos."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Concepto:
    id: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    tipo: str = "Asignacion"
    formula_tipo: str = "Fijo"
    valor: float = 0.0
    aplica_prestaciones: int = 0
    activo: int = 1
