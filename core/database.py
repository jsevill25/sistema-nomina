from .common import *
from . import common as settings

class _ClosingSQLiteConnection(sqlite3.Connection):
    """SQLite connection that also closes when used as a context manager."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class DatabaseManager:
    """Manejador central de base de datos SQLite con soporte para esquemas modulares."""

    @staticmethod
    def get_connection():
        conn = sqlite3.connect(settings.DB_NAME, factory=_ClosingSQLiteConnection)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @staticmethod
    def init_core_db():
        """Inicializa las tablas esenciales inmutables del núcleo."""
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()

            # Tabla Usuarios Core
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    rol TEXT CHECK(rol IN ('admin','usuario','supervisor')) NOT NULL,
                    activo INTEGER DEFAULT 1,
                    creado TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Tabla Auditoría Core
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    detalle TEXT,
                    fecha TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Insertar administrador predeterminado
            cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
            if not cursor.fetchone():
                admin_pass = hash_password("admin123")
                cursor.execute("""
                    INSERT INTO usuarios (username, password_hash, rol, activo)
                    VALUES ('admin', ?, 'admin', 1)
                """, (admin_pass,))

            conn.commit()

    @staticmethod
    def log_auditoria(usuario: str, accion: str, detalle: str = ""):
        """Registra un evento en la bitácora de auditoría."""
        try:
            with DatabaseManager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO auditoria (usuario, accion, detalle, fecha)
                    VALUES (?, ?, ?, datetime('now', 'localtime'))
                """, (usuario, accion, detalle))
                conn.commit()
        except Exception as e:
            print(f"Error registrando auditoría: {e}")
