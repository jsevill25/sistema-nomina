"""Cálculo de prestaciones sociales LOTTT."""

from .module import SeveranceModule
from .services import SeveranceEngine, calcular_antiguedad
from .views import SeveranceUITab

__all__ = ["SeveranceModule", "SeveranceEngine", "SeveranceUITab", "calcular_antiguedad"]
