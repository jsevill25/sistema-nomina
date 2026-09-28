"""Controlador del módulo de usuarios."""

from .repository import UsersRepository
from core import hash_password


class UsersController:
    @staticmethod
    def listar_usuarios():
        return UsersRepository.listar()

    @staticmethod
    def crear_usuario(username, password, role):
        return UsersRepository.crear(username, hash_password(password), role)

    @staticmethod
    def cambiar_estado(user_id, active):
        return UsersRepository.cambiar_estado(user_id, active)
