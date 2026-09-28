"""Compatibility exports for the employee Tkinter views."""

from .views import EmployeeDialog, EmployeeUITab, EgresoDialog

EmployeeView = EmployeeUITab

__all__ = ["EmployeeView", "EmployeeDialog", "EmployeeUITab", "EgresoDialog"]
