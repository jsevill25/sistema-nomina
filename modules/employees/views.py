from core.base import *
from .controller import EmployeeController

class EmployeeUITab(ttk.Frame):
    """Interfaz gráfica para gestión de empleados."""

    def __init__(self, parent):
        super().__init__(parent)
        self.controller = EmployeeController()
        self._create_ui()
        self.cargar_empleados()

    def _create_ui(self):
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="➕ Nuevo Empleado", command=self._nuevo_empleado).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="✏️ Editar", command=self._editar_empleado).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="🚪 Registrar Egreso", command=self._registrar_egreso).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="❌ Eliminar", command=self._eliminar_empleado).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="🔄 Refrescar", command=self.cargar_empleados).pack(side=tk.LEFT, padx=4)

        ttk.Label(toolbar, text="Buscar:").pack(side=tk.LEFT, padx=(20, 5))
        self.ent_search = ttk.Entry(toolbar, width=20)
        self.ent_search.pack(side=tk.LEFT, padx=4)
        self.ent_search.bind("<KeyRelease>", self._filtrar)

        columns = ("id", "cedula", "nombre_completo", "tipo", "departamento", "cargo", "ingreso", "salario", "estado")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("cedula", text="Cédula")
        self.tree.heading("nombre_completo", text="Nombres y Apellidos")
        self.tree.heading("tipo", text="Tipo Personal")
        self.tree.heading("departamento", text="Departamento")
        self.tree.heading("cargo", text="Cargo")
        self.tree.heading("ingreso", text="F. Ingreso")
        self.tree.heading("salario", text="Salario Mensual (Base)")
        self.tree.heading("estado", text="Estado")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("cedula", width=90, anchor=tk.CENTER)
        self.tree.column("nombre_completo", width=200)
        self.tree.column("tipo", width=110, anchor=tk.CENTER)
        self.tree.column("departamento", width=120)
        self.tree.column("cargo", width=140)
        self.tree.column("ingreso", width=90, anchor=tk.CENTER)
        self.tree.column("salario", width=140, anchor=tk.E)
        self.tree.column("estado", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

    def cargar_empleados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in self.controller.listar_todos():
            estado = "Activo" if r[9] == 1 else "Egresado"
            nombre_comp = f"{r[3]}, {r[2]}"
            self.tree.insert("", tk.END, iid=r[0], values=(
                r[0], r[1], nombre_comp, r[4], r[5] or "N/A", r[6] or "N/A",
                r[7], format_usd(r[8] or 0), estado
            ))

    def _filtrar(self, event=None):
        q = self.ent_search.get().strip().lower()
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            if any(q in str(v).lower() for v in vals):
                self.tree.reattach(item, "", tk.END)
            else:
                self.tree.detach(item)

    def _nuevo_empleado(self):
        dlg = EmployeeDialog(self, title="Registrar Nuevo Empleado")
        self.wait_window(dlg)
        if dlg.result:
            d = dlg.result
            try:
                self.controller.crear_empleado(d)

                user = AuthController.get_current_user()["username"]
                DatabaseManager.log_auditoria(user, "CREAR_EMPLEADO", f"Cédula: {d['cedula']}")
                EventBus.publish("EMPLOYEE_UPDATED")
                messagebox.showinfo("Éxito", "Empleado registrado correctamente.")
                self.cargar_empleados()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "La cédula de identidad ya existe en la base de datos.")

    def _editar_empleado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un empleado.")
            return

        emp_id = sel[0]
        data = self.controller.obtener_para_edicion(emp_id)

        if not data:
            return

        dlg = EmployeeDialog(self, title="Editar Empleado", emp_data=data)
        self.wait_window(dlg)
        if dlg.result:
            d = dlg.result
            self.controller.actualizar_empleado(emp_id, d)

            user = AuthController.get_current_user()["username"]
            DatabaseManager.log_auditoria(user, "EDITAR_EMPLEADO", f"ID: {emp_id}, Cédula: {d['cedula']}")
            EventBus.publish("EMPLOYEE_UPDATED")
            messagebox.showinfo("Éxito", "Datos de empleado actualizados.")
            self.cargar_empleados()

    # ═══ BLOQUE 4: Registro de egreso con baja lógica y auditoría ═══
    def _registrar_egreso(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un empleado activo.")
            return
        emp_id = int(sel[0])
        if self.tree.item(sel[0], "values")[-1] != "Activo":
            messagebox.showwarning("Atención", "El empleado seleccionado ya está egresado.")
            return
        dlg = EgresoDialog(self)
        self.wait_window(dlg)
        if not dlg.result:
            return
        if not self.controller.registrar_egreso(emp_id, dlg.result["fecha"], dlg.result["motivo"]):
            messagebox.showwarning("Atención", "El empleado ya no está activo.")
            return
        user = AuthController.get_current_user()["username"]
        DatabaseManager.log_auditoria(user, "EGRESO_EMPLEADO", f"ID: {emp_id}; fecha: {dlg.result['fecha']}; motivo: {dlg.result['motivo']}")
        EventBus.publish("EMPLOYEE_UPDATED")
        self.cargar_empleados()

    def _eliminar_empleado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un empleado.")
            return

        emp_id = sel[0]
        vals = self.tree.item(emp_id, "values")
        if messagebox.askyesno("Confirmación", f"¿Desea eliminar al empleado {vals[2]} (C.I.: {vals[1]})?"):
            self.controller.eliminar_empleado(emp_id)

            user = AuthController.get_current_user()["username"]
            DatabaseManager.log_auditoria(user, "ELIMINAR_EMPLEADO", f"Cédula: {vals[1]}")
            EventBus.publish("EMPLOYEE_UPDATED")
            messagebox.showinfo("Éxito", "Empleado eliminado.")
            self.cargar_empleados()


class EmployeeDialog(tk.Toplevel):
    """Diálogo modal para crear/editar expedientes de empleados."""

    def __init__(self, parent, title="Empleado", emp_data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("560x660")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.emp_data = emp_data
        self.result = None
        self._init_ui()

    def _init_ui(self):
        pad = {'padx': 10, 'pady': 5}
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # ═══ BLOQUE 5: Campos de personal con salario dinámico por tipo ═══
        ttk.Label(frame, text="Cédula de Identidad:").grid(row=0, column=0, sticky=tk.W, **pad)
        self.ent_ced = ttk.Entry(frame, width=25)
        self.ent_ced.grid(row=0, column=1, **pad)

        ttk.Label(frame, text="Nombres:").grid(row=1, column=0, sticky=tk.W, **pad)
        self.ent_nom = ttk.Entry(frame, width=25)
        self.ent_nom.grid(row=1, column=1, **pad)

        ttk.Label(frame, text="Apellidos:").grid(row=2, column=0, sticky=tk.W, **pad)
        self.ent_ape = ttk.Entry(frame, width=25)
        self.ent_ape.grid(row=2, column=1, **pad)

        ttk.Label(frame, text="Tipo Personal:").grid(row=3, column=0, sticky=tk.W, **pad)
        self.cbo_tipo = ttk.Combobox(frame, values=[
            "Docente Tiempo Completo", "Docente por Horas", "Administrativo",
            "Obrero", "Directivo", "Coordinador"
        ], state="readonly", width=30)
        self.cbo_tipo.current(0)
        self.cbo_tipo.grid(row=3, column=1, **pad)
        self.cbo_tipo.bind("<<ComboboxSelected>>", self._actualizar_campos_tipo)

        ttk.Label(frame, text="Departamento:").grid(row=4, column=0, sticky=tk.W, **pad)
        self.ent_departamento = ttk.Entry(frame, width=32)
        self.ent_departamento.grid(row=4, column=1, **pad)

        ttk.Label(frame, text="Cargo:").grid(row=5, column=0, sticky=tk.W, **pad)
        self.ent_cargo = ttk.Entry(frame, width=25)
        self.ent_cargo.grid(row=5, column=1, **pad)

        ttk.Label(frame, text="Fecha Ingreso (YYYY-MM-DD):").grid(row=6, column=0, sticky=tk.W, **pad)
        self.ent_ing = ttk.Entry(frame, width=25)
        self.ent_ing.insert(0, date.today().strftime("%Y-%m-%d"))
        self.ent_ing.grid(row=6, column=1, **pad)

        self.lbl_salario = ttk.Label(frame, text="Salario Mensual (USD):")
        self.lbl_salario.grid(row=7, column=0, sticky=tk.W, **pad)
        self.ent_sal = ttk.Entry(frame, width=25)
        self.ent_sal.grid(row=7, column=1, **pad)

        self.lbl_horas = ttk.Label(frame, text="Horas Semanales:")
        self.ent_horas = ttk.Entry(frame, width=25)
        self.lbl_valor_hora = ttk.Label(frame, text="Valor Hora Cátedra (USD):")
        self.ent_valor_hora = ttk.Entry(frame, width=25)
        valor_base = ConfigManager.load_config().get("parametros_laborales", {}).get("valor_hora_catedra_base_usd", 3.50)
        self.ent_valor_hora.insert(0, str(valor_base))

        ttk.Label(frame, text="Banco:").grid(row=10, column=0, sticky=tk.W, **pad)
        self.ent_banco = ttk.Entry(frame, width=25)
        self.ent_banco.insert(0, "Banco de Venezuela")
        self.ent_banco.grid(row=10, column=1, **pad)

        ttk.Label(frame, text="Nº Cuenta Bancaria:").grid(row=11, column=0, sticky=tk.W, **pad)
        self.ent_cuenta = ttk.Entry(frame, width=25)
        self.ent_cuenta.grid(row=11, column=1, **pad)

        ttk.Label(frame, text="Observaciones:").grid(row=12, column=0, sticky=tk.W, **pad)
        self.ent_observaciones = ttk.Entry(frame, width=32)
        self.ent_observaciones.grid(row=12, column=1, **pad)

        if self.emp_data:
            self.ent_ced.insert(0, self.emp_data[1])
            self.ent_nom.insert(0, self.emp_data[2])
            self.ent_ape.insert(0, self.emp_data[3])
            self.cbo_tipo.set(self.emp_data[4])
            self.ent_cargo.insert(0, self.emp_data[5] or "")
            self.ent_ing.delete(0, tk.END)
            self.ent_ing.insert(0, self.emp_data[6])
            self.ent_sal.insert(0, str(self.emp_data[7] or 0))
            self.ent_banco.delete(0, tk.END)
            self.ent_banco.insert(0, self.emp_data[8] or "")
            self.ent_cuenta.insert(0, self.emp_data[9] or "")
            self.ent_departamento.insert(0, self.emp_data[10] or "")
            self.ent_horas.insert(0, str(self.emp_data[11] or ""))
            if self.emp_data[12] is not None:
                self.ent_valor_hora.delete(0, tk.END)
                self.ent_valor_hora.insert(0, str(self.emp_data[12]))
            self.ent_observaciones.insert(0, self.emp_data[13] or "")

        btn_f = ttk.Frame(frame)
        btn_f.grid(row=13, column=0, columnspan=2, pady=15)
        ttk.Button(btn_f, text="Guardar", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=5)
        self._actualizar_campos_tipo()

    def _actualizar_campos_tipo(self, event=None):
        if self.cbo_tipo.get() == "Docente por Horas":
            self.lbl_salario.grid_remove()
            self.ent_sal.grid_remove()
            self.lbl_horas.grid(row=7, column=0, sticky=tk.W, padx=10, pady=5)
            self.ent_horas.grid(row=7, column=1, padx=10, pady=5)
            self.lbl_valor_hora.grid(row=8, column=0, sticky=tk.W, padx=10, pady=5)
            self.ent_valor_hora.grid(row=8, column=1, padx=10, pady=5)
        else:
            self.lbl_salario.grid(row=7, column=0, sticky=tk.W, padx=10, pady=5)
            self.ent_sal.grid(row=7, column=1, padx=10, pady=5)
            self.lbl_horas.grid_remove()
            self.ent_horas.grid_remove()
            self.lbl_valor_hora.grid_remove()
            self.ent_valor_hora.grid_remove()

    def _on_save(self):
        ced = self.ent_ced.get().strip()
        nom = self.ent_nom.get().strip()
        ape = self.ent_ape.get().strip()
        ing = self.ent_ing.get().strip()
        tipo = self.cbo_tipo.get()

        if not (ced and nom and ape and ing):
            messagebox.showerror("Error", "Complete los campos obligatorios.", parent=self)
            return

        try:
            parse_date(ing)
        except ValueError:
            messagebox.showerror("Error", "Fecha inválida (YYYY-MM-DD).", parent=self)
            return

        sal, horas, valor_hora = 0.0, None, None
        try:
            if tipo == "Docente por Horas":
                horas = int(self.ent_horas.get().strip())
                valor_hora = float(self.ent_valor_hora.get().strip().replace(",", "."))
                if horas <= 0 or valor_hora <= 0:
                    raise ValueError()
            else:
                sal = float(self.ent_sal.get().strip().replace(",", "."))
                if sal <= 0:
                    raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Indique salario, horas o valor hora con montos positivos válidos.", parent=self)
            return

        self.result = {
            "cedula": ced,
            "nombres": nom,
            "apellidos": ape,
            "tipo": tipo,
            "departamento": self.ent_departamento.get().strip(),
            "cargo": self.ent_cargo.get().strip(),
            "ingreso": ing,
            "salario": sal,
            "horas": horas,
            "valor_hora": valor_hora,
            "observaciones": self.ent_observaciones.get().strip(),
            "banco": self.ent_banco.get().strip(),
            "cuenta": self.ent_cuenta.get().strip()
        }
        self.destroy()


class EgresoDialog(tk.Toplevel):
    """Captura la fecha y el motivo para una baja laboral."""

    MOTIVOS = ["Renuncia voluntaria", "Despido justificado", "Despido injustificado",
               "Jubilación", "Fin de contrato", "Fallecimiento"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Registrar Egreso")
        self.geometry("420x190")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Fecha de egreso (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=8)
        self.ent_fecha = ttk.Entry(frame, width=18)
        self.ent_fecha.insert(0, date.today().strftime("%Y-%m-%d"))
        self.ent_fecha.grid(row=0, column=1, padx=5, pady=8)
        ttk.Label(frame, text="Motivo:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=8)
        self.cbo_motivo = ttk.Combobox(frame, values=self.MOTIVOS, state="readonly", width=25)
        self.cbo_motivo.current(0)
        self.cbo_motivo.grid(row=1, column=1, padx=5, pady=8)
        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(buttons, text="Guardar egreso", command=self._guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _guardar(self):
        fecha = self.ent_fecha.get().strip()
        try:
            parse_date(fecha)
        except ValueError:
            messagebox.showerror("Error", "Fecha inválida (YYYY-MM-DD).", parent=self)
            return
        self.result = {"fecha": fecha, "motivo": self.cbo_motivo.get()}
        self.destroy()
