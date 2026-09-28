from core.base import *
from .services import SeveranceEngine

class SeveranceUITab(ttk.Frame):
    """Pestaña interactiva de cálculo de prestaciones con reporte TXT y PDF."""

    def __init__(self, parent):
        super().__init__(parent)
        self.emp_map = {}
        self.reporte_actual = None
        self._create_ui()
        EventBus.subscribe("EMPLOYEE_UPDATED", self.refrescar_empleados)

    def destroy(self):
        EventBus.unsubscribe("EMPLOYEE_UPDATED", self.refrescar_empleados)
        super().destroy()

    def _create_ui(self):
        top_pnl = ttk.LabelFrame(self, text="Parámetros de Liquidación LOTTT Art. 142 y Tasa BCV", padding=10)
        top_pnl.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_pnl, text="Empleado:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cbo_emp = ttk.Combobox(top_pnl, width=28, state="readonly")
        self.cbo_emp.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(top_pnl, text="F. Cálculo:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.ent_fecha = ttk.Entry(top_pnl, width=11)
        self.ent_fecha.insert(0, date.today().strftime("%Y-%m-%d"))
        self.ent_fecha.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(top_pnl, text="Tasa BCV:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        self.ent_bcv = ttk.Entry(top_pnl, width=9)
        tasa_ini = BCVClient.obtener_tasa_bcv()
        self.ent_bcv.insert(0, f"{tasa_ini:.2f}")
        self.ent_bcv.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(top_pnl, text="🧮 Calcular", command=self._ejecutar_calculo).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(top_pnl, text="📄 PDF", command=self._exportar_pdf_prestaciones).grid(row=0, column=7, padx=3, pady=5)
        ttk.Button(top_pnl, text="💾 TXT", command=self._exportar_txt).grid(row=0, column=8, padx=3, pady=5)

        res_frame = ttk.LabelFrame(self, text="Informe Oficial de Liquidación en Bolívares (BCV)", padding=10)
        res_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.txt_res = tk.Text(res_frame, wrap=tk.WORD, font=("Consolas", 10))
        sc = ttk.Scrollbar(res_frame, orient=tk.VERTICAL, command=self.txt_res.yview)
        self.txt_res.configure(yscroll=sc.set)

        self.txt_res.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sc.pack(side=tk.RIGHT, fill=tk.Y)

        self.refrescar_empleados()

    def refrescar_empleados(self, **kwargs):
        self.emp_map.clear()
        opts = []
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT id, cedula, nombres, apellidos, cargo, fecha_ingreso,
                                     salario_mensual, salario_mensual_usd, tipo_personal,
                                     horas_semanales, valor_hora_catedra_usd
                              FROM empleados ORDER BY apellidos, nombres""")
            for r in cursor.fetchall():
                label = f"{r[3]}, {r[2]} | C.I.: {r[1]}"
                self.emp_map[label] = {
                    "id": r[0], "cedula": r[1], "nombres": r[2], "apellidos": r[3],
                    "cargo": r[4], "fecha_ingreso": r[5], "salario_mensual": r[6],
                    "salario_mensual_usd": r[7], "tipo_personal": r[8],
                    "horas_semanales": r[9], "valor_hora_catedra_usd": r[10]
                }
                opts.append(label)

        self.cbo_emp["values"] = opts
        if opts:
            self.cbo_emp.current(0)

    def _ejecutar_calculo(self):
        lbl = self.cbo_emp.get()
        if not lbl or lbl not in self.emp_map:
            messagebox.showwarning("Atención", "Seleccione un empleado.")
            return

        f_str = self.ent_fecha.get().strip()
        try:
            parse_date(f_str)
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido (YYYY-MM-DD).")
            return

        bcv_str = self.ent_bcv.get().strip()
        try:
            tasa_bcv = float(bcv_str.replace(",", "."))
            if tasa_bcv <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "La tasa BCV debe ser un número positivo.")
            return

        emp = self.emp_map[lbl]
        try:
            r = SeveranceEngine.calcular_prestaciones(emp, f_str, tasa_bcv)
            self.reporte_actual = r
            self._mostrar_informe(r)

            usr = AuthController.get_current_user()["username"]
            DatabaseManager.log_auditoria(usr, "CALCULO_PRESTACIONES", f"C.I.: {r['cedula']}, Tasa BCV: {tasa_bcv}, Total Bs: {format_bs(r['monto_definitivo'])}")
        except Exception as ex:
            messagebox.showerror("Error en Cálculo", str(ex))

    def _mostrar_informe(self, r: dict):
        self.txt_res.delete("1.0", tk.END)
        tasa_fmt = f"Bs. {r['tasa_bcv']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        txt = f"""
================================================================================
           COLEGIO HUYAPARI - NÓMINA Y PRESTACIONES
          REPORTE DE LIQUIDACIÓN EN BOLÍVARES A TASA BCV DEL DÍA
================================================================================

1. DATOS DEL TRABAJADOR Y TASA CAMBIARIA
--------------------------------------------------------------------------------
• Apellidos y Nombres : {r['nombre_completo']}
• Cédula de Identidad : {r['cedula']}
• Cargo Desempeñado   : {r['cargo']}
• Tipo de Personal    : {r['tipo_personal']}
• Fecha de Ingreso    : {r['fecha_ingreso']}
• Fecha de Cálculo    : {r['fecha_calculo']}
• Tiempo Servido      : {r['antiguedad_str']} ({r['dias_totales']} días)
• Tasa BCV Aplicada   : {tasa_fmt} por Dólar
• Origen Salario Integral: {r['origen_salario_integral']}

2. SALARIO INTEGRAL DIARIO CALCULADO EN BOLÍVARES
--------------------------------------------------------------------------------
• Salario Mensual Base (Convertido) : {format_bs(r['salario_mensual'])}
• Salario Diario Base               : {format_bs(r['salario_diario'])} / día
• Alícuota Utilidades (30d)         : {format_bs(r['alicuota_utilidades'])} / día
• Alícuota Bono Vacacional          : {format_bs(r['alicuota_bono_vacacional'])} / día
--------------------------------------------------------------------------------
=> SALARIO INTEGRAL DIARIO EN BS.   : {format_bs(r['salario_integral_diario'])} / día

3. COMPARATIVA DOBLE MECANISMO ART. 142 LOTTT (EN BOLÍVARES)
--------------------------------------------------------------------------------
a) GARANTÍA TRIMESTRAL (Art. 142 a):
   - Trimestres devengados: {r['num_trimestres']} (15 días por trimestre)
   - Monto Garantía en Bs.: {format_bs(r['monto_literal_a'])}

b) DÍAS ADICIONALES (Art. 142 b):
   - Días adicionales     : {r['dias_literal_b']} días
   - Monto Días Adicionales: {format_bs(r['monto_literal_b'])}
--------------------------------------------------------------------------------
   [SUBTOTAL A + B (Garantía + Días Adicionales)]: {format_bs(r['subtotal_ab'])}

c) CÁLCULO RETROACTIVO (Art. 142 c):
   - Años computables (>6m): {r['anos_c']} año(s)
   - Días aplicables (30d/a): {r['dias_literal_c']} días
   - Monto Retroactivo Bs. : {format_bs(r['monto_literal_c'])}

================================================================================
4. MONTO DEFINITIVO A PAGAR EN BOLÍVARES (MÁS FAVORABLE AL TRABAJADOR)
================================================================================
• Criterio Aplicado: {r['concepto_favorable']}

>>> MONTO TOTAL PRESTACIONES SOCIALES: {format_bs(r['monto_definitivo'])} <<<
================================================================================
        """
        self.txt_res.insert(tk.END, txt)

    def _exportar_pdf_prestaciones(self):
        if not self.reporte_actual:
            messagebox.showwarning("Atención", "Realice un cálculo de prestaciones antes de exportar en PDF.")
            return

        if not HAS_REPORTLAB:
            messagebox.showerror("Librería Faltante", "La librería 'ReportLab' no está instalada.\nInstálela ejecutando: pip install reportlab")
            return

        r = self.reporte_actual
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Liquidacion_Prestaciones_{r['cedula']}.pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not path:
            return

        try:
            doc = SimpleDocTemplate(path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'TitleStyle', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1A365D'), alignment=1, spaceAfter=6
            )
            sub_style = ParagraphStyle(
                'SubStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#4A5568'), alignment=1, spaceAfter=12
            )

            story.append(Paragraph("<b>COLEGIO HUYAPARI</b>", title_style))
            story.append(Paragraph("<b>INFORME OFICIAL DE PRESTACIONES SOCIALES (LOTTT ART. 142)</b>", sub_style))

            t_data = [
                [Paragraph(f"<b>Trabajador:</b> {r['nombre_completo']}", styles['Normal']), Paragraph(f"<b>Cédula:</b> {r['cedula']}", styles['Normal'])],
                [Paragraph(f"<b>Cargo:</b> {r['cargo']}", styles['Normal']), Paragraph(f"<b>Antigüedad:</b> {r['antiguedad_str']}", styles['Normal'])],
                [Paragraph(f"<b>F. Ingreso:</b> {r['fecha_ingreso']}", styles['Normal']), Paragraph(f"<b>F. Cálculo:</b> {r['fecha_calculo']}", styles['Normal'])],
                [Paragraph(f"<b>Tasa BCV:</b> {format_bs(r['tasa_bcv'])}", styles['Normal']), Paragraph(f"<b>Salario Integral Diario:</b> {format_bs(r['salario_integral_diario'])}", styles['Normal'])],
                [Paragraph(f"<b>Origen salario integral:</b> {r['origen_salario_integral']}", styles['Normal']), ""],
            ]
            t = Table(t_data, colWidths=[270, 270])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

            resumen_data = [
                ['Concepto / Mecanismo Legal LOTTT', 'Monto en Bolívares (Bs.)'],
                ['Garantía Trimestral (Literal a)', format_bs(r['monto_literal_a'])],
                ['Días Adicionales (Literal b)', format_bs(r['monto_literal_b'])],
                ['Subtotal Garantía + Adicionales (a + b)', format_bs(r['subtotal_ab'])],
                ['Cálculo Retroactivo Anual (Literal c)', format_bs(r['monto_literal_c'])],
                ['<b>MONTO DEFINITIVO A PAGAR</b>', f'<b>{format_bs(r["monto_definitivo"])}</b>']
            ]
            t_res = Table(resumen_data, colWidths=[340, 200])
            t_res.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#C6F6D5')),
            ]))
            story.append(t_res)
            story.append(Spacer(1, 12))

            crit_style = ParagraphStyle(
                'CritStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#1A202C'), fontName='Helvetica-Bold'
            )
            story.append(Paragraph(f"Criterio Aplicado (Más favorable): {r['concepto_favorable']}", crit_style))

            doc.build(story)
            messagebox.showinfo("Éxito", f"Reporte de prestaciones en PDF generado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")

    def _exportar_txt(self):
        if not self.reporte_actual:
            messagebox.showwarning("Atención", "Realice un cálculo antes de exportar.")
            return

        fn = f"prestaciones_bcv_{self.reporte_actual['cedula']}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=fn, filetypes=[("Archivos TXT", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.txt_res.get("1.0", tk.END))
            messagebox.showinfo("Éxito", f"Reporte guardado en:\n{path}")
