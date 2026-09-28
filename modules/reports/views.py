from core.base import *

class ReportsUITab(ttk.Frame):
    """Pestaña para exportación de archivos bancarios y respaldo Excel."""

    def __init__(self, parent):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        pnl = ttk.LabelFrame(self, text="Gestión de Archivos Bancarios y Copias de Seguridad (Excel / XLSX)", padding=15)
        pnl.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        ttk.Label(pnl, text="Formato de Banco:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        cbo_banco = ttk.Combobox(pnl, values=["Banco de Venezuela (TXT Lote)", "Banco Mercantil (TXT)", "Banesco (CSV)"], state="readonly", width=30)
        cbo_banco.current(0)
        cbo_banco.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(pnl, text="💾 Generar Archivo de Pago Bancario en Bolívares", command=self._generar_txt_banco).grid(row=1, column=0, columnspan=2, pady=10, sticky=tk.W)

        sep = ttk.Separator(pnl, orient=tk.HORIZONTAL)
        sep.grid(row=2, column=0, columnspan=2, sticky="ew", pady=20)

        ttk.Label(pnl, text="Respaldo de Seguridad de Registros (Excel):", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(pnl, text="Exporta todos los expedientes de empleados, nóminas e historial a una hoja de cálculo Excel (XLSX) para salvaguarda de datos.", font=("Segoe UI", 9, "italic")).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        ttk.Button(pnl, text="📊 Generar Respaldo Completo en Excel (.xlsx)", command=self._exportar_respaldo_excel).grid(row=5, column=0, columnspan=2, pady=15, sticky=tk.W)

    def _generar_txt_banco(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="PAGO_NOMINA_BDV.txt", filetypes=[("Archivos TXT", "*.txt")])
        if path:
            with DatabaseManager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT cedula, nombres, apellidos, banco, cuenta_bancaria, salario_mensual FROM empleados WHERE activo = 1")
                rows = cursor.fetchall()

            with open(path, "w", encoding="utf-8") as f:
                f.write("HEADER_BDV_NOMINA_LICEO\n")
                for r in rows:
                    monto = f"{r[5]:.2f}".replace(".", "")
                    f.write(f"01|{r[0]}|{r[3] or 'BDV'}|{r[4] or '00000000000000000000'}|{monto}\n")

            messagebox.showinfo("Éxito", f"Archivo generado exitosamente para {len(rows)} empleados.")

    def _exportar_respaldo_excel(self):
        if not HAS_OPENPYXL:
            messagebox.showerror("Librería Faltante", "La librería 'openpyxl' no está instalada.\nInstálela ejecutando: pip install openpyxl")
            return

        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Respaldo_Nomina_{datetime.now().strftime('%Y%m%d')}.xlsx", filetypes=[("Archivos Excel", "*.xlsx")])
        if not path:
            return

        try:
            wb = openpyxl.Workbook()
            ws_emp = wb.active
            ws_emp.title = "Empleados"
            ws_emp.append(["ID", "Cédula", "Nombres", "Apellidos", "Tipo Personal", "Cargo", "Fecha Ingreso", "Salario Base Mensual", "Banco", "Nº Cuenta", "Estado"])

            with DatabaseManager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, cedula, nombres, apellidos, tipo_personal, cargo, fecha_ingreso, salario_mensual, banco, cuenta_bancaria, activo FROM empleados")
                for r in cursor.fetchall():
                    ws_emp.append(list(r))

                ws_nom = wb.create_sheet(title="Nominas_Procesadas")
                ws_nom.append(["ID", "Período", "Tasa BCV", "Fecha Proceso", "Total Asignaciones", "Total Deducciones", "Total Neto", "Procesado Por"])
                cursor.execute("SELECT id, periodo, tasa_bcv, fecha_proceso, total_asignaciones, total_deducciones, total_neto, procesado_por FROM nominas_generadas")
                for r in cursor.fetchall():
                    ws_nom.append(list(r))

                ws_aud = wb.create_sheet(title="Auditoria_Sistema")
                ws_aud.append(["ID", "Usuario", "Acción", "Detalle", "Fecha"])
                cursor.execute("SELECT id, usuario, accion, detalle, fecha FROM auditoria")
                for r in cursor.fetchall():
                    ws_aud.append(list(r))

            wb.save(path)
            messagebox.showinfo("Respaldo Exitoso", f"El archivo de respaldo en Excel se ha guardado correctamente en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el archivo Excel:\n{e}")
