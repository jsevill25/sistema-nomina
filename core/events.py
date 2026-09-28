from .common import *

class EventBus:
    """Sistema de Publicación/Suscripción desacoplado para comunicación entre módulos."""
    _listeners: Dict[str, List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_name: str, callback: Callable):
        if event_name not in cls._listeners:
            cls._listeners[event_name] = []
        cls._listeners[event_name].append(callback)

    @classmethod
    def unsubscribe(cls, event_name: str, callback: Callable):
        if event_name in cls._listeners:
            cls._listeners[event_name] = [cb for cb in cls._listeners[event_name] if cb != callback]

    @classmethod
    def publish(cls, event_name: str, **data):
        if event_name in cls._listeners:
            for callback in cls._listeners[event_name]:
                try:
                    callback(**data)
                except Exception as e:
                    print(f"Error en listener para evento '{event_name}': {e}")
