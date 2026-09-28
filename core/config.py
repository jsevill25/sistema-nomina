from .common import *
from . import common as settings

class BCVClient:
    """Cliente HTTP automático para consultar tasa oficial del Banco Central de Venezuela con respaldo manual."""

    @staticmethod
    def obtener_tasa_bcv() -> float:
        """
        Consulta la tasa oficial del BCV mediante cliente HTTP seguro con timeout de 3 segundos.
        Si no hay internet o falla el servicio, retorna un valor por defecto o la última tasa registrada.
        """
        url = "https://rates.dolarvzla.com/bcv/current.json"
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=3.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))

                tasa = None

                # Verificamos si la respuesta es un diccionario directo o anidado común
                if isinstance(data, dict):
                    # Buscamos claves típicas para la tasa actual
                    tasa = (
                        data.get("current") or
                        data.get("usd") or
                        data.get("price") or
                        data.get("tasa")
                    )

                    # Si viene en un sub-diccionario (ej. {"current": {"usd": 36.5}})
                    if isinstance(tasa, dict):
                        tasa = tasa.get("usd") or tasa.get("price")

                if tasa is not None:
                    return float(tasa)
        except Exception as e:
            print(f"[BCV Aviso] No se pudo conectar con la API BCV automática ({e}). Usando valor referencial.")

        return 36.50  # Valor fallback oficial por defecto si no hay conectividad


class ConfigManager:
    """Manejador de lectura y escritura para config.json."""

    DEFAULT_CONFIG = {
        "sistema": {
            "nombre": "SISTEMA DE NÓMINA Y PRESTACIONES - COLEGIO HUYAPARI v3.0.0",
            "version": "3.0.0",
            "institucion": "Colegio Huyapari",
            "moneda": "Bs.",
            "tema_activo": "Corporativo Ejecutivo (Azul Petróleo)"
        },
        # ═══ BLOQUE 1: Datos institucionales y parámetros laborales ═══
        "institucion": {
            "nombre": "Colegio Huyapari",
            "rif": "",
            "direccion": "",
            "telefono": ""
        },
        "parametros_laborales": {
            "horas_semana_completo": 30,
            "valor_hora_catedra_base_usd": 3.50,
            "dias_utilidades": 30,
            "dias_bono_vacacional_base": 15,
            "cestaticket_mensual_usd": 40.00,
            "porcentaje_ivss": 4.0,
            "porcentaje_faov": 1.0,
            "porcentaje_inces": 0.5
        },
        "modulos_activos": [
            "mod_empleados",
            "mod_conceptos",
            "mod_nomina_mensual",
            "mod_prestaciones",
            "mod_historico_pagos",
            "mod_reportes",
            "mod_usuarios",
            "mod_auditoria"
        ]
    }

    @classmethod
    def load_config(cls) -> dict:
        if not os.path.exists(settings.CONFIG_FILE):
            cls.save_config(cls.DEFAULT_CONFIG)
            return cls.DEFAULT_CONFIG
        try:
            with open(settings.CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                version_anterior = cfg.get("sistema", {}).get("version")
                # ═══ BLOQUE 2: Migración no destructiva de configuración ═══
                for section, defaults in cls.DEFAULT_CONFIG.items():
                    if isinstance(defaults, dict):
                        cfg.setdefault(section, {})
                        for key, value in defaults.items():
                            cfg[section].setdefault(key, value)
                    else:
                        cfg.setdefault(section, defaults)
                cfg["sistema"]["nombre"] = cls.DEFAULT_CONFIG["sistema"]["nombre"]
                cfg["sistema"]["version"] = cls.DEFAULT_CONFIG["sistema"]["version"]
                cfg["sistema"]["institucion"] = "Colegio Huyapari"
                cfg["institucion"]["nombre"] = "Colegio Huyapari"
                if version_anterior != cls.DEFAULT_CONFIG["sistema"]["version"]:
                    if "mod_historico_pagos" not in cfg["modulos_activos"]:
                        cfg["modulos_activos"].append("mod_historico_pagos")
                    cls.save_config(cfg)
                return cfg
        except Exception:
            return cls.DEFAULT_CONFIG

    @classmethod
    def save_config(cls, config: dict):
        with open(settings.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    @classmethod
    def is_module_active(cls, module_id: str) -> bool:
        cfg = cls.load_config()
        return module_id in cfg.get("modulos_activos", [])

    @classmethod
    def toggle_module(cls, module_id: str, active: bool):
        cfg = cls.load_config()
        activos = set(cfg.get("modulos_activos", []))
        if active:
            activos.add(module_id)
        else:
            activos.discard(module_id)
        cfg["modulos_activos"] = list(activos)
        cls.save_config(cfg)

    @classmethod
    def set_tema(cls, nombre_tema: str):
        cfg = cls.load_config()
        if "sistema" not in cfg:
            cfg["sistema"] = {}
        cfg["sistema"]["tema_activo"] = nombre_tema
        cls.save_config(cfg)
