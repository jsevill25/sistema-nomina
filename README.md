# Sistema de Nómina - Colegio Huyapari

## Arquitectura

`app.py` es el entry point y fachada de compatibilidad. La implementación está organizada así:

- `core/`: utilidades compartidas, temas, configuración/BCV, SQLite, eventos, autenticación y registro de plugins.
- `modules/employees/`: entidad, repositorio, controlador, plugin y vistas para personal y egresos.
- `modules/concepts/`: conceptos, repositorio/controlador y vista.
- `modules/payroll/`: motor de cálculo, persistencia de nómina/histórico, plugin y vistas.
- `modules/severance/`: cálculo LOTTT, plugin y vistas.
- `modules/reports/`, `modules/users/`, `modules/audit/`: plugins y vistas de sus dominios; usuarios incluye repository/controller.
- `ui/application.py`: login, ventana principal, gestor de plugins y bootstrap.
- `tests/`: pruebas de cálculos, persistencia e integridad de migración.

Los plugins implementan `ModuleBase`; el núcleo los activa desde `ModuleRegistry`. Los módulos se notifican mediante `EventBus` y no requieren modificar la ventana principal para construir sus pestañas, aunque un plugin nuevo sí debe registrarse en `ui/application.py`.

## Pruebas

Desde la carpeta raíz del proyecto:

```bash
python -m compileall -q app.py core modules shared ui tests
python -m unittest discover -s tests -v
```

Las pruebas usan bases SQLite temporales; no modifican `nomina.db`.

## Ejecución local en escritorio Linux

El proyecto es una aplicación de escritorio Tkinter, no una aplicación web. Para abrir sus ventanas, ejecuta estos pasos en un equipo Linux con sesión gráfica, no dentro de un Codespace sin `DISPLAY`:

```bash
sudo apt update
sudo apt install python3-tk python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install reportlab openpyxl bcrypt
python app.py
```

Ejecuta `python app.py` desde la carpeta raíz. En el primer inicio se crean `config.json` y `nomina.db`. ReportLab, OpenPyXL y bcrypt son opcionales; instalarlos habilita exportación PDF, exportación Excel y hash bcrypt.

## Ejecución local en Windows

Instala Python desde python.org con Tcl/Tk habilitado, abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
py -m pip install reportlab openpyxl bcrypt
py app.py
```

Usuario inicial de prueba: `admin`. Contraseña inicial: `admin123`. No uses estas credenciales en una instalación de producción.

## Obtener el código desde GitHub

En el repositorio de GitHub, selecciona **Code > Download ZIP** y descomprímelo en el equipo local. El ZIP del repositorio no incluye la base de datos ni la configuración generadas en Codespaces; ambas se crean al primer inicio local.