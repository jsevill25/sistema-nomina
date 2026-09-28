# Sistema de Nómina y Prestaciones - Colegio Huyapari v3.0.0
# Cambios: personal diferenciado, cálculo quincenal por tipo, histórico de pagos,
# prestaciones basadas en pagos reales, egresos y consulta/exportación de histórico.
# Instalación opcional: pip install reportlab openpyxl bcrypt
# Credenciales iniciales: admin / admin123. Cambie esta contraseña en producción.

import os
import sys
import json
import sqlite3
import hashlib
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from typing import Dict, List, Callable, Any, Optional

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Intentar importar dependencias avanzadas profesionales (ReportLab, OpenPyXL, Bcrypt)
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

DB_NAME = "nomina.db"
CONFIG_FILE = "config.json"

def format_bs(amount: float) -> str:
    """
    Formatea un número flotante al formato oficial de Bolívares venezolanos:
    Ejemplo: 1234567.89 -> 'Bs. 1.234.567,89'
    """
    if amount is None:
        amount = 0.0
    formatted = f"{amount:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Bs. {formatted}"

def format_usd(amount: float) -> str:
    """Formatea un número flotante al formato USD."""
    if amount is None:
        amount = 0.0
    return f"${amount:,.2f}"

def parse_date(date_str: str) -> date:
    """Convierte un string YYYY-MM-DD a objeto datetime.date."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def hash_password(password: str) -> str:
    """Genera hash seguro para contraseñas usando bcrypt si está disponible, o SHA-256 con salt corporativo."""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback robusto con SHA-256 corporativo y salt interno
        salt_corp = "LiceoVenezuela2026_SecureKey"
        return hashlib.sha256((password + salt_corp).encode("utf-8")).hexdigest()

def verify_password(password_plain: str, stored_hash: str) -> bool:
    """Verifica contraseña considerando bcrypt o SHA-256."""
    if HAS_BCRYPT and stored_hash.startswith("$2b$"):
        try:
            return bcrypt.checkpw(password_plain.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            return False
    else:
        return hash_password(password_plain) == stored_hash
