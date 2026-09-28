"""Entry point and compatibility facade for the payroll desktop application."""

from core.base import *  # noqa: F401,F403
from modules.employees import EmployeeModule, EmployeeUITab, EmployeeDialog, EgresoDialog
from modules.concepts import ConceptsModule, ConceptsUITab
from modules.payroll import (
    MonthlyPayrollModule, PayrollEngine, PayrollUITab,
    PaymentHistoryModule, PaymentHistoryUITab,
)
from modules.severance import SeveranceEngine, SeveranceModule, SeveranceUITab
from modules.reports import ReportsModule, ReportsUITab
from modules.users import UsersModule, UsersUITab, UserDialog
from modules.audit import AuditModule, AuditUITab
from ui.application import (
    ModuleManagerDialog, ThemeSelectorDialog, LoginWindow, MainWindow,
    bootstrap_application,
)


if __name__ == "__main__":
    bootstrap_application()
