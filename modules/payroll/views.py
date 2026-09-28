from core.base import *
from .controller import PayrollController

class PayrollUITab(ttk.Frame):
    """Pestaña para cálculo masivo incorporando la tasa BCV automática de la API o manual y generación de recibos PDF."""

    def __init__(self, parent):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        pnl = ttk.LabelFrame(self, text="Generador de Nómina Quincenal con Tasa BCV (API / Manual)", padding=12)
        pnl.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(pnl, text="Período de Nómina:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_periodo = ttk.Entry(pnl, width=22)
        mes_actual = datetime.now().strftime("%B %Y").upper()
        self.ent_periodo.insert(0, f"1RA QUINCENA - {mes_actual}")
        self.ent_periodo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(pnl, text="Tasa BCV (Bs./$):").grid(row=0, column=2, sticky=tk.W, padx=(10, 5), pady=5)
        self.ent_bcv = ttk.Entry(pnl, width=12)

        # Consultar API BCV automáticamente al iniciar la pestaña
        tasa_inicial = BCVClient.obtener_tasa_bcv()
        self.ent_bcv.insert(0, f"{tasa_inicial:.2f}")
        self.ent_bcv.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(pnl, text="🌐 Consultar API BCV", command=self._actualizar_bcv_api).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(pnl, text="⚡ Procesar Nómina", command=self._procesar_nomina).grid(row=0, column=5, padx=10, pady=5)

        # Historial de Nóminas
        lbl_f = ttk.LabelFrame(self, text="Historial de Nóminas Procesadas y Generación de Recibos PDF", padding=10)
        lbl_f.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Barra inferior para exportar PDF o reporte individual
        btn_bar = ttk.Frame(lbl_f, padding=5)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        ttk.Button(btn_bar, text="📄 Generar Recibos PDF (Seleccionada)", command=self._exportar_recibos_pdf).pack(side=tk.LEFT, padx=5)

        columns = ("id", "periodo", "bcv", "fecha", "asig", "ded", "neto", "usuario")
        self.tree = ttk.Treeview(lbl_f, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("periodo", text="Período")
        self.tree.heading("bcv", text="Tasa BCV")
        self.tree.heading("fecha", text="Fecha Procesado")
        self.tree.heading("asig", text="Total Asignaciones")
        self.tree.heading("ded", text="Total Deducciones")
        self.tree.heading("neto", text="Monto Neto Pagado")
        self.tree.heading("usuario", text="Procesado Por")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("periodo", width=170)
        self.tree.column("bcv", width=90, anchor=tk.E)
        self.tree.column("fecha", width=130, anchor=tk.CENTER)
        self.tree.column("asig", width=130, anchor=tk.E)
        self.tree.column("ded", width=130, anchor=tk.E)
        self.tree.column("neto", width=130, anchor=tk.E)
        self.tree.column("usuario", width=100, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.cargar_historial()

    def _actualizar_bcv_api(self):
        tasa = BCVClient.obtener_tasa_bcv()
        self.ent_bcv.delete(0, tk.END)
        self.ent_bcv.insert(0, f"{tasa:.2f}")
        messagebox.showinfo("BCV Actualizado", f"Tasa oficial obtenida desde el BCV / API:\nBs. {tasa:.2f} por Dólar")

    def cargar_historial(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in PayrollController.listar_nominas():
            tasa_fmt = format_bs(r[2])
            self.tree.insert("", tk.END, iid=r[0], values=(
                r[0], r[1], tasa_fmt, r[3], format_bs(r[4]), format_bs(r[5]), format_bs(r[6]), r[7]
            ))

    def _procesar_nomina(self):
        periodo = self.ent_periodo.get().strip()
        if not periodo:
            messagebox.showerror("Error", "Ingrese la descripción del período.")
            return

        bcv_str = self.ent_bcv.get().strip()
        try:
            tasa_bcv = float(bcv_str.replace(",", "."))
            if tasa_bcv <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "La tasa BCV debe ser un número positivo válido.")
            return

        usuario_act = AuthController.get_current_user()["username"]
        try:
            resultado = PayrollController.procesar_nomina(periodo, tasa_bcv, usuario_act)
        except ValueError as exc:
            messagebox.showwarning("Atención", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo procesar la nómina:\n{exc}")
            return

        nom_id = resultado["nomina_id"]
        tot_neto = resultado["total_neto"]
        DatabaseManager.log_auditoria(usuario_act, "PROCESAR_NOMINA", f"Nómina ID: {nom_id}, Período: {periodo}, Tasa BCV: {tasa_bcv}")
        EventBus.publish("PAYROLL_PROCESSED", nomina_id=nom_id)
        messagebox.showinfo("Éxito", f"Nómina procesada con Tasa BCV: {tasa_bcv}\nPersonal: {resultado['cantidad_empleados']} empleados\nMonto Neto Total: {format_bs(tot_neto)}")
        self.cargar_historial()

    def _exportar_recibos_pdf(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una nómina del historial para generar sus recibos en PDF.")
            return

        nomina_id = sel[0]

        if not HAS_REPORTLAB:
            messagebox.showerror("Librería Faltante", "La librería 'ReportLab' no está instalada.\nInstálela ejecutando: pip install reportlab")
            return

        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Recibos_Nomina_{nomina_id}.pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not path:
            return

        try:
            with DatabaseManager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT periodo, tasa_bcv, fecha_proceso FROM nominas_generadas WHERE id = ?", (nomina_id,))
                nom_info = cursor.fetchone()

                cursor.execute("""
                    SELECT e.cedula, e.nombres, e.apellidos, e.cargo, e.tipo_personal,
                           r.salario_base, r.horas_catedra, r.cestaticket, r.primas_bonos,
                           r.total_asignaciones, r.ivss, r.faov, r.inces,
                           r.total_deducciones, r.neto_cobrar
                    FROM recibos_detalle r
                    JOIN empleados e ON r.empleado_id = e.id
                    WHERE r.nomina_id = ?
                """, (nomina_id,))
                recibos = cursor.fetchall()

            doc = SimpleDocTemplate(path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#1A365D'),
                alignment=1,
                spaceAfter=6
            )

            subtitle_style = ParagraphStyle(
                'SubTitleStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#4A5568'),
                alignment=1,
                spaceAfter=12
            )

            for rec in recibos:
                (cedula, nombres, apellidos, cargo, tipo_personal, sal_base, horas_catedra,
                 cestaticket, primas_bonos, asig_tot, ivss, faov, inces, ded_tot, neto) = rec

                story.append(Paragraph("<b>COLEGIO HUYAPARI</b>", title_style))
                story.append(Paragraph(f"<b>COMPROBANTE INDIVIDUAL DE PAGO DE NÓMINA</b><br/>Período: {nom_info[0]} | Tasa BCV: {format_bs(nom_info[1])}", subtitle_style))

                data_empleado = [
                    [Paragraph(f"<b>Trabajador:</b> {apellidos}, {nombres}", styles['Normal']), Paragraph(f"<b>Cédula:</b> {cedula}", styles['Normal'])],
                    [Paragraph(f"<b>Tipo:</b> {tipo_personal}", styles['Normal']), Paragraph(f"<b>Cargo:</b> {cargo or 'N/A'}", styles['Normal'])],
                    [Paragraph(f"<b>Fecha Emisión:</b> {nom_info[2]}", styles['Normal']), ""]
                ]
                t_emp = Table(data_empleado, colWidths=[280, 260])
                t_emp.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(t_emp)
                story.append(Spacer(1, 8))

                # Detalle de conceptos
                data_conceptos = [
                    ['Concepto / Descripción', 'Asignaciones (Bs.)', 'Deducciones (Bs.)'],
                    ['Sueldo Base Quincenal', format_bs(sal_base), ''],
                    ['Horas Cátedra', format_bs(horas_catedra), ''],
                    ['Cestaticket Socialista', format_bs(cestaticket), ''],
                    ['Primas / Bonos', format_bs(primas_bonos), ''],
                    ['Seguro Social Obligatorio (IVSS 4%)', '', format_bs(ivss)],
                    ['Fondo Ahorro Habitación (FAOV 1%)', '', format_bs(faov)],
                    ['Aporte INCES (0.5%)', '', format_bs(inces)],
                    ['<b>TOTALES</b>', f'<b>{format_bs(asig_tot)}</b>', f'<b>{format_bs(ded_tot)}</b>']
                ]

                t_con = Table(data_conceptos, colWidths=[260, 140, 140])
                t_con.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8FAFC')]),
                    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2E8F0')),
                ]))
                story.append(t_con)
                story.append(Spacer(1, 6))

                neto_style = ParagraphStyle(
                    'NetoStyle',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.HexColor('#2C7A7B'),
                    alignment=2,
                    fontName='Helvetica-Bold'
                )
                story.append(Paragraph(f"NETO A COBRAR EN BOLÍVARES: {format_bs(neto)}", neto_style))
                story.append(Spacer(1, 15))

            doc.build(story)
            messagebox.showinfo("Éxito", f"Recibos de pago en PDF generados correctamente en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al generar el PDF:\n{e}")


class PaymentHistoryUITab(ttk.Frame):
    """Vista de consulta del historial de pagos con filtros y exportación PDF."""

    def __init__(self, parent):
        super().__init__(parent)
        self.empleados = {}
        self.resultados = []
        self._create_ui()
        self._cargar_empleados()
        EventBus.subscribe("PAYROLL_PROCESSED", self._al_procesar_nomina)

    def destroy(self):
        EventBus.unsubscribe("PAYROLL_PROCESSED", self._al_procesar_nomina)
        super().destroy()

    def _create_ui(self):
        filtros = ttk.LabelFrame(self, text="Consulta de pagos", padding=10)
        filtros.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(filtros, text="Empleado:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.cbo_empleado = ttk.Combobox(filtros, state="readonly", width=34)
        self.cbo_empleado.grid(row=0, column=1, padx=5, pady=5)

        hoy = date.today()
        ttk.Label(filtros, text="Desde (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.ent_desde = ttk.Entry(filtros, width=12)
        self.ent_desde.insert(0, hoy.replace(day=1).isoformat())
        self.ent_desde.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filtros, text="Hasta:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.ent_hasta = ttk.Entry(filtros, width=12)
        self.ent_hasta.insert(0, hoy.isoformat())
        self.ent_hasta.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(filtros, text="🔎 Consultar", command=self.consultar).grid(row=0, column=6, padx=6, pady=5)
        ttk.Button(filtros, text="📄 Exportar PDF", command=self.exportar_pdf).grid(row=0, column=7, padx=6, pady=5)

        self.lbl_resumen = ttk.Label(self, text="Períodos: 0 | Asignaciones: Bs. 0,00 | Deducciones: Bs. 0,00 | Neto: Bs. 0,00", font=("Segoe UI", 9, "bold"))
        self.lbl_resumen.pack(fill=tk.X, padx=12, pady=(0, 5))

        frame_tabla = ttk.Frame(self)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        columnas = ("id", "periodo", "fecha", "tasa", "sueldo", "horas", "cesta", "primas", "asig", "ded", "neto", "integral")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        titulos = {
            "id": "ID", "periodo": "Período", "fecha": "Fecha", "tasa": "Tasa BCV",
            "sueldo": "Sueldo base", "horas": "Horas cátedra", "cesta": "Cestaticket",
            "primas": "Primas / bonos", "asig": "Asignaciones", "ded": "Deducciones",
            "neto": "Neto", "integral": "Salario integral diario"
        }
        anchos = {"id": 48, "periodo": 145, "fecha": 92, "tasa": 90, "sueldo": 120,
                  "horas": 120, "cesta": 115, "primas": 120, "asig": 120, "ded": 120,
                  "neto": 120, "integral": 145}
        for columna in columnas:
            self.tree.heading(columna, text=titulos[columna])
            self.tree.column(columna, width=anchos[columna], anchor=tk.E if columna not in ("id", "periodo", "fecha") else tk.W, stretch=False)
        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        frame_tabla.rowconfigure(0, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

    def _cargar_empleados(self):
        self.empleados = {"Todos los empleados": None}
        rows = PayrollController.listar_empleados()
        for empleado_id, cedula, nombres, apellidos in rows:
            label = f"{cedula} - {apellidos}, {nombres}"
            self.empleados[label] = empleado_id
        self.cbo_empleado["values"] = list(self.empleados)
        self.cbo_empleado.set("Todos los empleados")

    def _al_procesar_nomina(self, **kwargs):
        self._cargar_empleados()
        self.consultar()

    def consultar(self):
        empleado_label = self.cbo_empleado.get()
        empleado_id = self.empleados.get(empleado_label)
        desde = self.ent_desde.get().strip()
        hasta = self.ent_hasta.get().strip()
        try:
            parse_date(desde)
            parse_date(hasta)
            if desde > hasta:
                raise ValueError("La fecha inicial debe ser anterior o igual a la fecha final.")
        except ValueError as exc:
            messagebox.showerror("Fechas inválidas", str(exc) or "Use el formato YYYY-MM-DD.", parent=self)
            return

            self.resultados = PayrollController.consultar_historico(empleado_id, desde, hasta)

        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.resultados:
            self.tree.insert("", tk.END, values=(
                row[0], row[1], row[2], format_bs(row[3]), format_bs(row[4]),
                format_bs(row[5]), format_bs(row[6]), format_bs(row[7]),
                format_bs(row[8]), format_bs(row[9]), format_bs(row[10]), format_bs(row[11]),
            ))
        asignaciones = sum(row[8] for row in self.resultados)
        deducciones = sum(row[9] for row in self.resultados)
        neto = sum(row[10] for row in self.resultados)
        self.lbl_resumen.config(text=(
            f"Períodos: {len(self.resultados)} | Asignaciones: {format_bs(asignaciones)} | "
            f"Deducciones: {format_bs(deducciones)} | Neto: {format_bs(neto)}"
        ))

    def exportar_pdf(self):
        if not self.resultados:
            messagebox.showwarning("Sin datos", "Consulte un empleado y período con pagos antes de exportar.", parent=self)
            return
        if not HAS_REPORTLAB:
            messagebox.showerror("Librería faltante", "Instale ReportLab con: pip install reportlab", parent=self)
            return
        empleado_label = self.cbo_empleado.get().replace("/", "-") or "Todos"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", initialfile=f"Historico_Pagos_{empleado_label}.pdf",
            filetypes=[("Archivos PDF", "*.pdf")], parent=self
        )
        if not path:
            return
        try:
            doc = SimpleDocTemplate(path, pagesize=(letter[1], letter[0]), leftMargin=22, rightMargin=22, topMargin=26, bottomMargin=26)
            styles = getSampleStyleSheet()
            story = [
                Paragraph("<b>COLEGIO HUYAPARI</b>", styles["Title"]),
                Paragraph(f"Histórico de pagos: {empleado_label} | {self.ent_desde.get()} a {self.ent_hasta.get()}", styles["Normal"]),
                Spacer(1, 10),
            ]
            headers = ["ID", "Período", "Fecha", "Tasa", "Sueldo", "Horas", "Cesta", "Primas", "Asig.", "Deduc.", "Neto", "Integral/día"]
            data = [headers]
            for row in self.resultados:
                data.append([
                    str(row[0]), row[1], row[2], format_bs(row[3]), format_bs(row[4]),
                    format_bs(row[5]), format_bs(row[6]), format_bs(row[7]), format_bs(row[8]),
                    format_bs(row[9]), format_bs(row[10]), format_bs(row[11]),
                ])
            tabla = Table(data, colWidths=[25, 82, 48, 54, 62, 62, 58, 58, 62, 62, 62, 69], repeatRows=1)
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3d59")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 5.5),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F9")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.extend([tabla, Spacer(1, 10), Paragraph(self.lbl_resumen.cget("text"), styles["Normal"])])
            doc.build(story)
            messagebox.showinfo("PDF generado", f"Histórico exportado correctamente:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{exc}", parent=self)
