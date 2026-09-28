"""Repositorio del módulo de conceptos."""

from core import DatabaseManager


class ConceptosRepository:
    @staticmethod
    def listar():
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT id, codigo, nombre, tipo, formula_tipo, valor,
                                     aplica_prestaciones, activo
                              FROM conceptos_nomina ORDER BY nombre""")
            return cursor.fetchall()
