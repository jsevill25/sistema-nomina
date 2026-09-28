"""Controlador del módulo de empleados."""

from .repository import EmpleadoRepository


class EmployeeController:
    """Coordina la lógica del módulo de empleados."""

    @staticmethod
    def listar_empleados():
        return EmpleadoRepository.listar_activos()

    @staticmethod
    def listar_todos():
        return EmpleadoRepository.listar_todos()

    @staticmethod
    def crear_empleado(empleado):
        return EmpleadoRepository.guardar(empleado)

    @staticmethod
    def obtener_para_edicion(empleado_id):
        return EmpleadoRepository.obtener_para_edicion(empleado_id)

    @staticmethod
    def actualizar_empleado(empleado_id, empleado):
        EmpleadoRepository.actualizar(empleado_id, empleado)

    @staticmethod
    def registrar_egreso(empleado_id, fecha_egreso, motivo):
        return EmpleadoRepository.registrar_egreso(empleado_id, fecha_egreso, motivo)

    @staticmethod
    def eliminar_empleado(empleado_id):
        return EmpleadoRepository.eliminar(empleado_id)
