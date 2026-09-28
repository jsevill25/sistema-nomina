from .common import *
from .config import ConfigManager

class ModuleBase(ABC):
    """Clase base abstracta que debe implementar cada módulo/plugin."""

    def __init__(self, manifest: dict):
        self.manifest = manifest
        self.module_id = manifest["id"]
        self.name = manifest["nombre"]
        self.version = manifest["version"]
        self.active = False

    @abstractmethod
    def initialize(self):
        """Inicializa esquemas de BD, subscripciones a eventos y lógica del módulo."""
        pass

    @abstractmethod
    def create_ui_tabs(self, parent_notebook: ttk.Notebook) -> List[ttk.Frame]:
        """Retorna las pestañas GUI que este módulo agrega a la ventana principal."""
        pass

    @abstractmethod
    def shutdown(self):
        """Limpia referencias y subscripciones al desactivar el módulo."""
        pass


class ModuleRegistry:
    """Registro y cargador dinámico de módulos/plugins."""
    _registered_modules: Dict[str, ModuleBase] = {}
    _active_instances: Dict[str, ModuleBase] = {}

    @classmethod
    def register_module(cls, module_instance: ModuleBase):
        cls._registered_modules[module_instance.module_id] = module_instance

    @classmethod
    def load_modules(cls):
        """Activa e inicializa únicamente los módulos habilitados en la configuración."""
        for mod_id, mod in cls._registered_modules.items():
            if ConfigManager.is_module_active(mod_id):
                try:
                    mod.initialize()
                    mod.active = True
                    cls._active_instances[mod_id] = mod
                    print(f"[Core] Módulo cargado con éxito: {mod.name} v{mod.version}")
                except Exception as e:
                    print(f"[Core Error] Falló al inicializar módulo '{mod_id}': {e}")

    @classmethod
    def get_active_modules(cls) -> List[ModuleBase]:
        return list(cls._active_instances.values())

    @classmethod
    def get_all_modules(cls) -> List[ModuleBase]:
        return list(cls._registered_modules.values())

    @classmethod
    def set_module_status(cls, module_id: str, enable: bool):
        ConfigManager.toggle_module(module_id, enable)
        if enable and module_id in cls._registered_modules:
            mod = cls._registered_modules[module_id]
            if not mod.active:
                mod.initialize()
                mod.active = True
                cls._active_instances[module_id] = mod
        elif not enable and module_id in cls._active_instances:
            mod = cls._active_instances.pop(module_id)
            mod.shutdown()
            mod.active = False
