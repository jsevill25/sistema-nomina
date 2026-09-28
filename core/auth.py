from .common import *
from .database import DatabaseManager
from .events import EventBus

class AuthController:
    """Controlador central de sesión y autenticación."""
    _current_user = None

    @classmethod
    def login(cls, username: str, password_plain: str) -> bool:
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, rol, activo FROM usuarios
                WHERE username = ?
            """, (username,))
            row = cursor.fetchone()

            if row:
                if row[4] == 0:
                    raise Exception("El usuario se encuentra desactivado.")

                stored_hash = row[2]
                if verify_password(password_plain, stored_hash):
                    cls._current_user = {
                        "id": row[0],
                        "username": row[1],
                        "rol": row[3]
                    }
                    DatabaseManager.log_auditoria(row[1], "INICIO_SESION", "Inicio de sesión exitoso")
                    EventBus.publish("USER_LOGGED_IN", user=cls._current_user)
                    return True
                else:
                    DatabaseManager.log_auditoria(username, "LOGIN_FALLIDO", "Contraseña incorrecta")
                    return False
            else:
                DatabaseManager.log_auditoria(username or "ANONIMO", "LOGIN_FALLIDO", "Usuario no encontrado")
                return False

    @classmethod
    def logout(cls):
        if cls._current_user:
            DatabaseManager.log_auditoria(cls._current_user["username"], "CIERRE_SESION", "Sesión finalizada")
            EventBus.publish("USER_LOGGED_OUT", username=cls._current_user["username"])
            cls._current_user = None

    @classmethod
    def get_current_user(cls):
        return cls._current_user

    @classmethod
    def es_admin(cls) -> bool:
        return cls._current_user is not None and cls._current_user.get("rol") == "admin"
