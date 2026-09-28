"""Controlador del módulo de conceptos."""

from .repository import ConceptosRepository


class ConceptosController:
    @staticmethod
    def listar_conceptos():
        return ConceptosRepository.listar()
