"""Repositorio del módulo de usuarios."""

from core import DatabaseManager


class UsersRepository:
    @staticmethod
    def listar():
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, rol, activo, creado FROM usuarios ORDER BY id")
            return cursor.fetchall()

    @staticmethod
    def crear(username, password_hash, role):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
            return cursor.lastrowid

    @staticmethod
    def cambiar_estado(user_id, active):
        with DatabaseManager.get_connection() as conn:
            cursor = conn.execute("UPDATE usuarios SET activo=? WHERE id=?", (active, user_id))
            return cursor.rowcount == 1
