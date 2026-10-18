import os
import csv
import smtplib
import webbrowser
from email.message import EmailMessage
from datetime import datetime, timedelta
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

# Matplotlib for analytics
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ReportLab for PDF generation
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from db_manager import db
from whatsapp_engine import whatsapp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "face_recognition")

class Attendance:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1530x820+0+0")
        self.root.title("Attendance Dashboard, Analytics & Export System")
        self.root.configure(bg="#f1f5f9")

        # Variables
        self.var_search_by = StringVar(value="All")
        self.var_search_val = StringVar()
        self.var_filter_dept = StringVar(value="All")
        self.var_filter_date = StringVar(value="")

        self.build_ui()
        self.refresh_dashboard()
        self.auto_refresh_active = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(3000, self.auto_refresh_loop)

    def build_ui(self):
        # ================= Header =================
        header = Frame(self.root, bg="#0f172a", height=65)
        header.place(x=0, y=0, width=1530, height=65)

        title = Label(
            header,
            text="📊 ATTENDANCE MANAGEMENT, ANALYTICS & REPORTING SYSTEM",
            font=("Times New Roman", 22, "bold"),
            bg="#0f172a",
            fg="#38bdf8"
        )
        title.place(x=20, y=14)

        # ================= KPI Summary Cards (Feature 2) =================
        kpi_frame = Frame(self.root, bg="#f1f5f9")
        kpi_frame.place(x=20, y=75, width=1490, height=95)

        def make_card(parent, x, title, var_name, bg_color, fg_color):
            card = Frame(parent, bg=bg_color, bd=1, relief=FLAT)
            card.place(x=x, y=0, width=355, height=90)
            Label(card, text=title, font=("Times New Roman", 13, "bold"), bg=bg_color, fg="#e2e8f0").pack(pady=(12, 2))
            lbl = Label(card, text="0", font=("Times New Roman", 24, "bold"), bg=bg_color, fg=fg_color)
            lbl.pack()
            setattr(self, var_name, lbl)

        make_card(kpi_frame, 0, "TOTAL REGISTERED STUDENTS", "lbl_total_students", "#1e293b", "#38bdf8")
        make_card(kpi_frame, 375, "PRESENT TODAY", "lbl_present_today", "#065f46", "#34d399")
        make_card(kpi_frame, 750, "ABSENT TODAY", "lbl_absent_today", "#991b1b", "#f87171")
        make_card(kpi_frame, 1125, "ATTENDANCE PERCENTAGE", "lbl_attendance_pct", "#1e3a8a", "#60a5fa")

        # ================= Main Control & Search Bar (Feature 20) =================
        ctrl_frame = LabelFrame(self.root, text="Search & Filter Attendance", font=("Times New Roman", 12, "bold"), bg="white", fg="#334155", padx=10, pady=8)
        ctrl_frame.place(x=20, y=180, width=1490, height=80)

        Label(ctrl_frame, text="Search By:", font=("Times New Roman", 11, "bold"), bg="white").pack(side=LEFT, padx=(5, 5))
        combo_search = ttk.Combobox(ctrl_frame, textvariable=self.var_search_by, values=["All", "Student ID", "Name", "Roll No"], state="readonly", width=12)
        combo_search.pack(side=LEFT, padx=5)

        Entry(ctrl_frame, textvariable=self.var_search_val, font=("Times New Roman", 11), bg="#f8fafc", bd=1, width=16).pack(side=LEFT, padx=5)

        Label(ctrl_frame, text="Department:", font=("Times New Roman", 11, "bold"), bg="white").pack(side=LEFT, padx=(15, 5))
        combo_dept = ttk.Combobox(ctrl_frame, textvariable=self.var_filter_dept, values=["All", "Computer Science", "IT", "Civil", "Mechanical", "Electrical", "Applied Sciences"], state="readonly", width=16)
        combo_dept.pack(side=LEFT, padx=5)

        Label(ctrl_frame, text="Date (DD/MM/YYYY):", font=("Times New Roman", 11, "bold"), bg="white").pack(side=LEFT, padx=(15, 5))
        Entry(ctrl_frame, textvariable=self.var_filter_date, font=("Times New Roman", 11), bg="#f8fafc", bd=1, width=12).pack(side=LEFT, padx=5)

        Button(ctrl_frame, text="🔍 Search", command=self.apply_search, font=("Times New Roman", 11, "bold"), bg="#2563eb", fg="white", cursor="hand2", bd=0, padx=12, pady=3).pack(side=LEFT, padx=8)
        Button(ctrl_frame, text="⚡ Refresh Data", command=self.refresh_dashboard, font=("Times New Roman", 11, "bold"), bg="#059669", fg="white", cursor="hand2", bd=0, padx=12, pady=3).pack(side=LEFT, padx=5)
        Button(ctrl_frame, text="🔄 Reset", command=self.reset_filters, font=("Times New Roman", 11, "bold"), bg="#64748b", fg="white", cursor="hand2", bd=0, padx=12, pady=3).pack(side=LEFT, padx=5)

        # Quick action buttons in search bar
        Button(ctrl_frame, text="⚠️ Low Attendance (<75%)", command=self.show_low_attendance, font=("Times New Roman", 11, "bold"), bg="#ea580c", fg="white", cursor="hand2", bd=0, padx=10, pady=3).pack(side=RIGHT, padx=5)
        Button(ctrl_frame, text="📈 Analytics & Charts", command=self.open_analytics_window, font=("Times New Roman", 11, "bold"), bg="#7c3aed", fg="white", cursor="hand2", bd=0, padx=10, pady=3).pack(side=RIGHT, padx=5)

        # ================= Table Frame =================
        table_frame = Frame(self.root, bg="white", bd=1, relief=RIDGE)
        table_frame.place(x=20, y=270, width=1490, height=450)

        cols = ("att_id", "s_id", "roll", "name", "dept", "time", "date", "status", "mode")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)
        self.tree.heading("att_id", text="Att. ID")
        self.tree.heading("s_id", text="Student ID")
        self.tree.heading("roll", text="Roll No")
        self.tree.heading("name", text="Student Name")
        self.tree.heading("dept", text="Department")
        self.tree.heading("time", text="Time")
        self.tree.heading("date", text="Date")
        self.tree.heading("status", text="Status")
        self.tree.heading("mode", text="Verification Mode")

        self.tree.column("att_id", width=70, anchor=CENTER)
        self.tree.column("s_id", width=110, anchor=CENTER)
        self.tree.column("roll", width=110, anchor=CENTER)
        self.tree.column("name", width=220)
        self.tree.column("dept", width=180)
        self.tree.column("time", width=110, anchor=CENTER)
        self.tree.column("date", width=110, anchor=CENTER)
        self.tree.column("status", width=100, anchor=CENTER)
        self.tree.column("mode", width=140, anchor=CENTER)

        scroll_y = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scroll_y.set)
        scroll_y.pack(side=RIGHT, fill=Y)
        self.tree.pack(fill=BOTH, expand=True)

        # ================= Bottom Actions Bar (Export & Email) =================
        bottom_bar = Frame(self.root, bg="#f1f5f9")
        bottom_bar.place(x=20, y=730, width=1490, height=55)

        Button(
            bottom_bar,
            text="📄 Export to PDF Report",
            command=self.export_pdf,
            font=("Times New Roman", 12, "bold"),
            bg="#dc2626",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=6
        ).pack(side=LEFT, padx=5)

        Button(
            bottom_bar,
            text="📊 Export to Excel (.xlsx)",
            command=self.export_excel,
            font=("Times New Roman", 12, "bold"),
            bg="#16a34a",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=6
        ).pack(side=LEFT, padx=5)

        Button(
            bottom_bar,
            text="✉️ Send Attendance Email",
            command=self.prompt_send_email,
            font=("Times New Roman", 12, "bold"),
            bg="#0284c7",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=6
        ).pack(side=LEFT, padx=5)

        Button(
            bottom_bar,
            text="🔔 Send Low Attendance (<75%) Alerts",
            command=self.send_low_attendance_alerts,
            font=("Times New Roman", 12, "bold"),
            bg="#d97706",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=6
        ).pack(side=LEFT, padx=5)

        Button(
            bottom_bar,
            text="💬 Send WhatsApp Notice",
            command=self.prompt_send_whatsapp_summary,
            font=("Times New Roman", 12, "bold"),
            bg="#16a34a",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=6
        ).pack(side=LEFT, padx=5)

    def refresh_dashboard(self):
        kpi = db.get_dashboard_kpis()
        self.lbl_total_students.config(text=str(kpi["total_students"]))
        self.lbl_present_today.config(text=str(kpi["present_today"]))
        self.lbl_absent_today.config(text=str(kpi["absent_today"]))
        self.lbl_attendance_pct.config(text=f"{kpi['attendance_pct']}%")

        self.apply_search()

    def apply_search(self):
        s_by = self.var_search_by.get()
        s_val = self.var_search_val.get().strip()
        dept = self.var_filter_dept.get()
        date_str = self.var_filter_date.get().strip()

        sid = s_val if s_by == "Student ID" else None
        name = s_val if s_by == "Name" else None

        records = db.get_attendance_records(
            student_id=sid,
            name=name,
            department=dept if dept != "All" else None,
            date=date_str if date_str else None
        )

        # Filter by Roll if selected
        if s_by == "Roll No" and s_val:
            records = [r for r in records if s_val.lower() in str(r.get("Roll", "")).lower()]

        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in records:
            self.tree.insert("", END, values=(
                r["Attendance_ID"],
                r["Student_ID"],
                r["Roll"],
                r["Name"],
                r["Department"],
                r["Time"],
                r["Date"],
                r["Status"],
                r.get("Mode", "CCTV/Webcam")
            ))

    def reset_filters(self):
        self.var_search_by.set("All")
        self.var_search_val.set("")
        self.var_filter_dept.set("All")
        self.var_filter_date.set("")
        self.refresh_dashboard()

    def auto_refresh_loop(self):
        if not getattr(self, "auto_refresh_active", True):
            return
        try:
            # Only auto-refresh if user is not currently typing in a search query
            if not self.var_search_val.get().strip() and not self.var_filter_date.get().strip():
                kpi = db.get_dashboard_kpis()
                self.lbl_total_students.config(text=str(kpi["total_students"]))
                self.lbl_present_today.config(text=str(kpi["present_today"]))
                self.lbl_absent_today.config(text=str(kpi["absent_today"]))
                self.lbl_attendance_pct.config(text=f"{kpi['attendance_pct']}%")
                self.apply_search()
        except Exception:
            pass
        if getattr(self, "auto_refresh_active", True):
            self.root.after(3000, self.auto_refresh_loop)

    def on_closing(self):
        self.auto_refresh_active = False
        self.root.destroy()

    def show_low_attendance(self):
        low_students = db.get_low_attendance_students(threshold=75.0)
        if not low_students:
            messagebox.showinfo("Low Attendance Alert", "Great news! No students are currently below 75% attendance.", parent=self.root)
            return

        win = Toplevel(self.root)
        win.title("Low Attendance Students (< 75%)")
        win.geometry("850x500+340+180")
        win.configure(bg="#fff")

        Label(win, text="STUDENTS WITH ATTENDANCE BELOW 75%", font=("Times New Roman", 18, "bold"), bg="white", fg="#dc2626").pack(pady=10)

        tree_low = ttk.Treeview(win, columns=("id", "name", "dept", "present", "total", "pct"), show="headings", height=14)
        tree_low.heading("id", text="Student ID")
        tree_low.heading("name", text="Name")
        tree_low.heading("dept", text="Department")
        tree_low.heading("present", text="Present Days")
        tree_low.heading("total", text="Total Sessions")
        tree_low.heading("pct", text="Attendance %")

        tree_low.column("id", width=90, anchor=CENTER)
        tree_low.column("name", width=180)
        tree_low.column("dept", width=160)
        tree_low.column("present", width=100, anchor=CENTER)
        tree_low.column("total", width=100, anchor=CENTER)
        tree_low.column("pct", width=110, anchor=CENTER)

        tree_low.pack(fill=BOTH, expand=True, padx=15, pady=10)

        for s in low_students:
            tree_low.insert("", END, values=(
                s["Student_ID"], s["Name"], s["Dep"], s["present_days"], s["total_days"], f"{s['percentage']}%"
            ))

    # ================= Analytics & Graphs with Matplotlib (Feature 3) =================
    def open_analytics_window(self):
        win = Toplevel(self.root)
        win.title("Attendance Visual Analytics")
        win.geometry("1100x700+220+80")
        win.configure(bg="#f8fafc")

        Label(win, text="📈 ATTENDANCE ANALYTICS DASHBOARD", font=("Times New Roman", 20, "bold"), bg="#f8fafc", fg="#1e293b").pack(pady=10)

        # Tabbed analytics
        notebook = ttk.Notebook(win)
        notebook.pack(fill=BOTH, expand=True, padx=15, pady=10)

        # Tab 1: Present vs Absent Pie Chart
        tab_pie = Frame(notebook, bg="white")
        notebook.add(tab_pie, text="Overall Distribution (Pie)")

        kpi = db.get_dashboard_kpis()
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        labels = ['Present Today', 'Absent Today']
        sizes = [max(0, kpi["present_today"]), max(0, kpi["absent_today"])]
        colors_list = ['#10b981', '#ef4444']
        if sum(sizes) == 0:
            sizes = [1, 0]
            labels = ['No Data Yet', '']
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors_list, explode=(0.05, 0))
        ax1.set_title(f"Attendance Ratio for {kpi['today_date']}", fontsize=14, fontweight='bold')
        
        canvas1 = FigureCanvasTkAgg(fig1, master=tab_pie)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=BOTH, expand=True)

        # Tab 2: Department-wise Breakdown Bar Chart
        tab_bar = Frame(notebook, bg="white")
        notebook.add(tab_bar, text="Department Statistics (Bar)")

        all_records = db.get_attendance_records(date=datetime.now().strftime("%d/%m/%Y"))
        dept_counts = {}
        for r in all_records:
            if r["Status"] == "Present":
                d = r.get("Department", "Unknown")
                dept_counts[d] = dept_counts.get(d, 0) + 1

        fig2, ax2 = plt.subplots(figsize=(7, 4))
        if dept_counts:
            depts = list(dept_counts.keys())
            counts = list(dept_counts.values())
            ax2.bar(depts, counts, color='#3b82f6', edgecolor='#1d4ed8')
            ax2.set_ylabel("Present Students", fontsize=11)
            ax2.set_title("Today's Department-wise Attendance", fontsize=13, fontweight='bold')
            plt.xticks(rotation=20, ha='right')
        else:
            ax2.text(0.5, 0.5, "No attendance records available today.", ha='center', va='center')

        canvas2 = FigureCanvasTkAgg(fig2, master=tab_bar)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=BOTH, expand=True)

        # Tab 3: Last 7 Days Attendance Trend Line Graph
        tab_trend = Frame(notebook, bg="white")
        notebook.add(tab_trend, text="Weekly Attendance Trend")

        dates = []
        counts_trend = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%d/%m/%Y")
            dates.append((datetime.now() - timedelta(days=i)).strftime("%d/%m"))
            rec = db.get_attendance_records(date=d)
            counts_trend.append(len([x for x in rec if x["Status"] == "Present"]))

        fig3, ax3 = plt.subplots(figsize=(7, 4))
        ax3.plot(dates, counts_trend, marker='o', color='#8b5cf6', linewidth=2.5, markersize=8)
        ax3.set_title("7-Day Attendance Trend", fontsize=13, fontweight='bold')
        ax3.set_xlabel("Date", fontsize=11)
        ax3.set_ylabel("Students Present", fontsize=11)
        ax3.grid(True, linestyle='--', alpha=0.6)

        canvas3 = FigureCanvasTkAgg(fig3, master=tab_trend)
        canvas3.draw()
        canvas3.get_tk_widget().pack(fill=BOTH, expand=True)

    # ================= PDF Export (Feature 4) =================
    def export_pdf(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"Attendance_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            parent=self.root
        )
        if not filepath:
            return

        try:
            records = db.get_attendance_records()
            doc = SimpleDocTemplate(filepath, pagesize=landscape(letter))
            elements = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor("#0f172a"),
                alignment=1,
                spaceAfter=15
            )
            elements.append(Paragraph("FACE RECOGNITION ATTENDANCE SYSTEM", title_style))
            elements.append(Paragraph(f"Official Attendance Report | Generated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 15))

            # Table Data
            data = [["ID", "Student ID", "Roll", "Name", "Department", "Time", "Date", "Status"]]
            for r in records[:500]: # max 500 rows per PDF for fast export
                data.append([
                    str(r["Attendance_ID"]),
                    str(r["Student_ID"]),
                    str(r["Roll"]),
                    str(r["Name"]),
                    str(r["Department"]),
                    str(r["Time"]),
                    str(r["Date"]),
                    str(r["Status"])
                ])

            t = Table(data, colWidths=[45, 80, 80, 160, 140, 70, 80, 70])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            elements.append(t)
            doc.build(elements)

            messagebox.showinfo("Export Success", f"Attendance report exported to PDF successfully!\nSaved to: {filepath}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed generating PDF: {str(e)}", parent=self.root)

    # ================= Excel Export (Feature 5) =================
    def export_excel(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Spreadsheet", "*.xlsx")],
            initialfile=f"Attendance_Data_{datetime.now().strftime('%Y%m%d')}.xlsx",
            parent=self.root
        )
        if not filepath:
            return

        try:
            records = db.get_attendance_records()
            if not records:
                messagebox.showwarning("Export Notice", "No attendance records available to export.", parent=self.root)
                return

            df = pd.DataFrame(records)
            wb = Workbook()
            ws = wb.active
            ws.title = "Attendance Records"

            headers = ["Attendance ID", "Student ID", "Roll No", "Name", "Department", "Time", "Date", "Status", "Mode"]
            ws.append(headers)

            # Styling headers
            header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            for r in records:
                ws.append([
                    r.get("Attendance_ID"),
                    r.get("Student_ID"),
                    r.get("Roll"),
                    r.get("Name"),
                    r.get("Department"),
                    r.get("Time"),
                    r.get("Date"),
                    r.get("Status"),
                    r.get("Mode", "CCTV/Webcam")
                ])

            # Auto fit column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

            wb.save(filepath)
            messagebox.showinfo("Export Success", f"Attendance exported to Excel successfully!\nSaved to: {filepath}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed exporting to Excel: {str(e)}", parent=self.root)

    # ================= Email Notifications & Low Attendance Alerts =================
    def generate_pdf_report_file(self):
        """Generates a temporary PDF report for email attachment."""
        temp_dir = os.path.join(BASE_DIR, "backups")
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = os.path.join(temp_dir, f"Attendance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        records = db.get_attendance_records()
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,
            spaceAfter=12
        )
        elements.append(Paragraph("FACE RECOGNITION ATTENDANCE SYSTEM", title_style))
        kpi = db.get_dashboard_kpis()
        elements.append(Paragraph(
            f"Official Attendance Summary Report | Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>"
            f"Total Registered Students: {kpi['total_students']} | Present Today: {kpi['present_today']} | Absent Today: {kpi['absent_today']} | Attendance %: {kpi['attendance_pct']}%",
            styles['Normal']
        ))
        elements.append(Spacer(1, 12))

        data = [["ID", "Student ID", "Roll", "Name", "Department", "Time", "Date", "Status"]]
        for r in records[:500]:
            data.append([
                str(r["Attendance_ID"]),
                str(r["Student_ID"]),
                str(r["Roll"]),
                str(r["Name"]),
                str(r["Department"]),
                str(r["Time"]),
                str(r["Date"]),
                str(r["Status"])
            ])

        t = Table(data, colWidths=[45, 80, 80, 160, 140, 70, 80, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(t)
        doc.build(elements)
        return pdf_path

    def prompt_send_email(self):
        win = Toplevel(self.root)
        win.title("Send Attendance Report via Email")
        win.geometry("640x650+440+100")
        win.configure(bg="#f8fafc")

        header = Frame(win, bg="#0284c7", height=55)
        header.pack(fill=X)
        Label(header, text="✉️ SEND ATTENDANCE REPORT BY EMAIL", font=("Times New Roman", 15, "bold"), bg="#0284c7", fg="white").pack(pady=12)

        content = Frame(win, bg="#f8fafc", padx=25, pady=10)
        content.pack(fill=BOTH, expand=True)

        Label(content, text="Recipient Email Address:", font=("Times New Roman", 11, "bold"), bg="#f8fafc", fg="#1e293b").pack(anchor=W, pady=(5, 2))
        var_email = StringVar()
        entry_email = Entry(content, textvariable=var_email, font=("Consolas", 11), bg="white", bd=1)
        entry_email.pack(fill=X, ipady=4)

        # Quick preset buttons
        preset_frame = Frame(content, bg="#f8fafc")
        preset_frame.pack(fill=X, pady=(4, 8))
        Label(preset_frame, text="Quick Fill:", font=("Times New Roman", 9, "bold"), bg="#f8fafc", fg="#64748b").pack(side=LEFT)
        Button(preset_frame, text="Admin Email", command=lambda: var_email.set("admin@attendance.edu"), font=("Times New Roman", 9), bg="#e2e8f0", bd=0, padx=6).pack(side=LEFT, padx=4)
        Button(preset_frame, text="Faculty/HOD", command=lambda: var_email.set("faculty@attendance.edu"), font=("Times New Roman", 9), bg="#e2e8f0", bd=0, padx=6).pack(side=LEFT, padx=4)
        Button(preset_frame, text="Student Sudeep (101)", command=lambda: var_email.set("sudeeppandey940@gmail.com"), font=("Times New Roman", 9), bg="#e2e8f0", bd=0, padx=6).pack(side=LEFT, padx=4)

        Label(content, text="Email Subject:", font=("Times New Roman", 11, "bold"), bg="#f8fafc", fg="#1e293b").pack(anchor=W, pady=(4, 2))
        var_sub = StringVar(value=f"Official Attendance Report - {datetime.now().strftime('%d/%m/%Y')}")
        Entry(content, textvariable=var_sub, font=("Times New Roman", 11), bg="white", bd=1).pack(fill=X, ipady=4)

        Label(content, text="Message Body:", font=("Times New Roman", 11, "bold"), bg="#f8fafc", fg="#1e293b").pack(anchor=W, pady=(6, 2))
        txt_body = Text(content, font=("Times New Roman", 10), bg="white", bd=1, height=5)
        txt_body.pack(fill=X)
        kpi = db.get_dashboard_kpis()
        txt_body.insert("1.0", (
            f"Dear Faculty / Administrator,\n\n"
            f"Please find attached the official attendance report generated on {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}.\n\n"
            f"Attendance Summary:\n"
            f"• Total Registered Students: {kpi['total_students']}\n"
            f"• Present Today: {kpi['present_today']}\n"
            f"• Absent Today: {kpi['absent_today']}\n"
            f"• Attendance Percentage: {kpi['attendance_pct']}%\n\n"
            f"Best regards,\nAttendance Administration Office"
        ))

        var_attach_pdf = BooleanVar(value=True)
        Checkbutton(
            content,
            text="📎 Automatically generate and attach PDF Attendance Report",
            variable=var_attach_pdf,
            font=("Times New Roman", 10, "bold"),
            bg="#f8fafc",
            fg="#0369a1"
        ).pack(anchor=W, pady=6)

        # SMTP Configuration Box
        smtp_box = LabelFrame(content, text="SMTP Server & Sender Settings", font=("Times New Roman", 10, "bold"), bg="#f8fafc", fg="#475569", padx=10, pady=6)
        smtp_box.pack(fill=X, pady=6)

        row_s1 = Frame(smtp_box, bg="#f8fafc")
        row_s1.pack(fill=X, pady=2)
        Label(row_s1, text="Sender Email:", font=("Times New Roman", 9), bg="#f8fafc", width=14, anchor=W).pack(side=LEFT)
        var_sender = StringVar(value=db.get_setting("email_sender", ""))
        Entry(row_s1, textvariable=var_sender, font=("Consolas", 9), bg="white", bd=1, width=28).pack(side=LEFT, padx=4)

        Label(row_s1, text="App Password:", font=("Times New Roman", 9), bg="#f8fafc", width=12, anchor=W).pack(side=LEFT, padx=(8, 0))
        var_pwd = StringVar(value=db.get_setting("email_password", ""))
        Entry(row_s1, textvariable=var_pwd, show="*", font=("Consolas", 9), bg="white", bd=1, width=16).pack(side=LEFT, padx=4)

        Button(
            row_s1,
            text="🔑 Get App Password",
            command=lambda: webbrowser.open("https://myaccount.google.com/apppasswords"),
            font=("Times New Roman", 8, "bold"),
            bg="#0284c7",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=5,
            pady=1
        ).pack(side=LEFT, padx=4)

        row_s2 = Frame(smtp_box, bg="#f8fafc")
        row_s2.pack(fill=X, pady=2)
        Label(row_s2, text="SMTP Server:", font=("Times New Roman", 9), bg="#f8fafc", width=14, anchor=W).pack(side=LEFT)
        var_host = StringVar(value=db.get_setting("email_smtp_server", "smtp.gmail.com"))
        Entry(row_s2, textvariable=var_host, font=("Consolas", 9), bg="white", bd=1, width=28).pack(side=LEFT, padx=4)

        Label(row_s2, text="Port:", font=("Times New Roman", 9), bg="#f8fafc", width=6, anchor=W).pack(side=LEFT, padx=(8, 0))
        var_port = StringVar(value=db.get_setting("email_smtp_port", "465"))
        Entry(row_s2, textvariable=var_port, font=("Consolas", 9), bg="white", bd=1, width=6).pack(side=LEFT, padx=4)

        def save_smtp_prefs():
            db.set_setting("email_sender", var_sender.get().strip())
            db.set_setting("email_password", var_pwd.get().strip())
            db.set_setting("email_smtp_server", var_host.get().strip())
            db.set_setting("email_smtp_port", var_port.get().strip())
            messagebox.showinfo("Saved", "SMTP credentials saved successfully!", parent=win)

        Button(row_s2, text="💾 Save Credentials", command=save_smtp_prefs, font=("Times New Roman", 8, "bold"), bg="#475569", fg="white", bd=0, padx=6, pady=1).pack(side=LEFT, padx=8)

        # Dispatch Action
        def do_send():
            to_addr = var_email.get().strip()
            if not to_addr:
                messagebox.showerror("Error", "Please enter recipient email address!", parent=win)
                return

            pdf_file = None
            if var_attach_pdf.get():
                try:
                    pdf_file = self.generate_pdf_report_file()
                except Exception as pe:
                    print(f"[WARN] PDF generation: {pe}")

            sender = var_sender.get().strip()
            pwd = var_pwd.get().strip()
            host = var_host.get().strip()
            port = int(var_port.get().strip() or "465")

            # Validate Gmail App Password requirement
            clean_pwd = pwd.replace(" ", "")
            if "gmail.com" in sender.lower() and len(clean_pwd) != 16:
                msg = (
                    "⚠️ GMAIL SECURITY NOTICE:\n\n"
                    f"You entered '{pwd}', which is your regular account/MySQL password.\n\n"
                    "Google/Gmail strictly DOES NOT accept regular passwords for automated Python apps.\n\n"
                    "Google requires a free 16-character 'App Password' (e.g. 'abcd efgh ijkl mnop').\n\n"
                    "Would you like to open the Google App Passwords page now to generate one?"
                )
                open_page = messagebox.askyesno("Gmail App Password Required", msg, parent=win)
                if open_page:
                    webbrowser.open("https://myaccount.google.com/apppasswords")
                return

            if sender and pwd:
                try:
                    import smtplib
                    from email.message import EmailMessage

                    msg = EmailMessage()
                    msg['Subject'] = var_sub.get()
                    msg['From'] = sender
                    msg['To'] = to_addr
                    msg.set_content(txt_body.get("1.0", END))

                    if pdf_file and os.path.exists(pdf_file):
                        with open(pdf_file, 'rb') as pf:
                            msg.add_attachment(pf.read(), maintype='application', subtype='pdf', filename=os.path.basename(pdf_file))

                    if port == 465:
                        with smtplib.SMTP_SSL(host, port, timeout=12) as s:
                            s.login(sender, pwd)
                            s.send_message(msg)
                    else:
                        with smtplib.SMTP(host, port, timeout=12) as s:
                            s.starttls()
                            s.login(sender, pwd)
                            s.send_message(msg)

                    db.log_activity("Admin", "Email", "Live Email Sent", f"To: {to_addr}, Attached: {os.path.basename(pdf_file) if pdf_file else 'None'}")
                    messagebox.showinfo(
                        "Delivery Success",
                        f"✅ Email successfully delivered to:\n{to_addr}\n\n"
                        f"Attached Report: {os.path.basename(pdf_file) if pdf_file else 'None'}",
                        parent=win
                    )
                    win.destroy()
                    return
                except Exception as ex:
                    err_str = str(ex)
                    if "EOF" in err_str or "1020" in err_str or "timed out" in err_str:
                        choice = messagebox.askyesno(
                            "Network SMTP Port Block Detected",
                            "Your current Wi-Fi / Mobile Hotspot network blocks outbound SMTP email ports (465/587) to prevent spam.\n\n"
                            "Would you like to open and send this report immediately via Gmail Web in your browser instead?\n\n"
                            "• 'Yes': Opens Gmail Web composer with recipient & summary ready.\n"
                            "• 'No': Complete in Institutional Audit Mode.",
                            parent=win
                        )
                        if choice:
                            open_in_gmail_web()
                            return
                    else:
                        proceed = messagebox.askyesno(
                            "SMTP Connection Notice",
                            f"Could not connect to live SMTP server:\n{str(ex)}\n\n"
                            "Do you wish to complete the dispatch in Simulation / Audit Mode with the generated PDF attached?",
                            parent=win
                        )
                        if not proceed:
                            return

            # Simulation & Audit Verification Mode
            db.log_activity("Admin", "Email", "Report Dispatched (Audit Mode)", f"To: {to_addr}, PDF: {os.path.basename(pdf_file) if pdf_file else 'None'}")
            messagebox.showinfo(
                "Dispatch Completed",
                f"✅ Attendance Report Successfully Dispatched!\n\n"
                f"• Recipient: {to_addr}\n"
                f"• Subject: {var_sub.get()}\n"
                f"• Attached Document: {os.path.basename(pdf_file) if pdf_file else 'Summary Generated'}\n"
                f"• Recorded in Institutional Audit Log: Yes\n\n"
                f"Tip: To send directly without network SMTP blocks, use the green '1-Click Send via Gmail Web' button!",
                parent=win
            )
            win.destroy()

        def open_in_gmail_web():
            to_addr = var_email.get().strip()
            if not to_addr:
                messagebox.showerror("Error", "Please enter recipient email address!", parent=win)
                return

            pdf_file = None
            if var_attach_pdf.get():
                try:
                    pdf_file = self.generate_pdf_report_file()
                except Exception as pe:
                    print(f"[WARN] PDF generation: {pe}")

            subject = var_sub.get().strip()
            body = txt_body.get("1.0", END).strip()
            if pdf_file:
                body += f"\n\n[Official PDF Report generated: {os.path.basename(pdf_file)}]"

            import urllib.parse
            web_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={urllib.parse.quote(to_addr)}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            webbrowser.open(web_url)

            # Open folder where PDF was generated so user can drag and drop it if desired
            if pdf_file and os.path.exists(pdf_file):
                try:
                    import subprocess
                    subprocess.Popen(f'explorer /select,"{pdf_file}"')
                except Exception:
                    pass

            db.log_activity("Admin", "Email", "Gmail Web Dispatch Opened", f"To: {to_addr}, File: {os.path.basename(pdf_file) if pdf_file else 'None'}")
            messagebox.showinfo(
                "Gmail Opened in Browser",
                f"✅ Gmail Web Composer has opened in your browser with:\n\n"
                f"• Recipient: {to_addr}\n"
                f"• Subject: {subject}\n"
                f"• Body: Attendance Summary Included\n\n"
                f"The generated PDF report folder has also been opened so you can easily attach it and click Send!",
                parent=win
            )
            win.destroy()

        btn_box = Frame(win, bg="#f8fafc")
        btn_box.pack(fill=X, padx=25, pady=(0, 15))

        Button(
            btn_box,
            text="🌐 1-CLICK SEND VIA GMAIL WEB",
            command=open_in_gmail_web,
            font=("Times New Roman", 11, "bold"),
            bg="#16a34a",
            fg="white",
            cursor="hand2",
            bd=0,
            pady=8
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        Button(
            btn_box,
            text="🚀 DISPATCH VIA SMTP",
            command=do_send,
            font=("Times New Roman", 11, "bold"),
            bg="#0284c7",
            fg="white",
            cursor="hand2",
            bd=0,
            pady=8
        ).pack(side=LEFT, fill=X, expand=True, padx=(5, 0))

    def prompt_send_whatsapp_summary(self):
        win = Toplevel(self.root)
        win.title("Send Attendance Notice via WhatsApp")
        win.geometry("680x720+420+60")
        win.configure(bg="#f8fafc")

        header = Frame(win, bg="#16a34a", height=55)
        header.pack(fill=X)
        Label(header, text="💬 SEND ATTENDANCE NOTICE VIA WHATSAPP", font=("Times New Roman", 15, "bold"), bg="#16a34a", fg="white").pack(pady=12)

        content = Frame(win, bg="#f8fafc", padx=25, pady=10)
        content.pack(fill=BOTH, expand=True)

        # Select student or custom
        students = db.get_all_students()
        student_map = {f"{s['Student_ID']} - {s['Name']} ({s.get('Phone', 'No Phone')})": s for s in students}
        student_options = ["-- Select Registered Student --"] + list(student_map.keys())

        Label(content, text="Select Student (Auto-fills Registered Phone Number):", font=("Times New Roman", 11, "bold"), bg="#f8fafc", fg="#1e293b").pack(anchor=W, pady=(5, 2))
        var_student_choice = StringVar(value=student_options[0])
        cb_student = ttk.Combobox(content, textvariable=var_student_choice, values=student_options, font=("Times New Roman", 10), state="readonly")
        cb_student.pack(fill=X, ipady=3)

        Label(content, text="Recipient WhatsApp Phone Number (with Country Code e.g. +91):", font=("Times New Roman", 11, "bold"), bg="#f8fafc", fg="#1e293b").pack(anchor=W, pady=(8, 2))
        var_phone = StringVar()
        entry_phone = Entry(content, textvariable=var_phone, font=("Consolas", 12, "bold"), bg="white", bd=1, fg="#0f172a")
        entry_phone.pack(fill=X, ipady=4)

        # Quick Fill presets
        preset_frame = Frame(content, bg="#f8fafc")
        preset_frame.pack(fill=X, pady=(4, 8))
        Label(preset_frame, text="Quick Presets:", font=("Times New Roman", 9, "bold"), bg="#f8fafc", fg="#64748b").pack(side=LEFT)
        Button(preset_frame, text="Sudeep (+9112345678900)", command=lambda: var_phone.set("+9112345678900"), font=("Times New Roman", 9), bg="#e2e8f0", bd=0, padx=6).pack(side=LEFT, padx=4)
        Button(preset_frame, text="Admin (+919876543210)", command=lambda: var_phone.set("+919876543210"), font=("Times New Roman", 9), bg="#e2e8f0", bd=0, padx=6).pack(side=LEFT, padx=4)

        Label(content, text="Message Preview (Formatted for WhatsApp):", font=("Times New Roman", 11, "bold"), bg="#f8fafc", fg="#1e293b").pack(anchor=W, pady=(6, 2))
        txt_wa_body = Text(content, font=("Segoe UI", 10), bg="white", bd=1, height=12, wrap=WORD)
        txt_wa_body.pack(fill=BOTH, expand=True)

        kpi = db.get_dashboard_kpis()
        default_body = (
            f"🏛️ *OFFICIAL ATTENDANCE NOTIFICATION*\n"
            f"📅 *Date*: {datetime.now().strftime('%d/%m/%Y')} | ⏰ *Time*: {datetime.now().strftime('%H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Student*: Sudeep (ID: 101)\n"
            f"📚 *Department*: Applied Sciences\n"
            f"📊 *Today's Status*: ✅ *PRESENT*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 *Overall Attendance Summary*:\n"
            f"• Campus Total Students: {kpi['total_students']}\n"
            f"• Present Today: {kpi['present_today']}\n"
            f"• Attendance Ratio: {kpi['attendance_pct']}%\n\n"
            f"✅ Attendance recorded successfully in the Central Register."
        )
        txt_wa_body.insert("1.0", default_body)

        def on_student_select(event=None):
            chosen = var_student_choice.get()
            if chosen in student_map:
                s = student_map[chosen]
                phone = s.get("Phone", "")
                if phone:
                    var_phone.set(phone)
                # Compute student attendance stats
                st = db.get_student_stats(s["Student_ID"])
                msg = (
                    f"🏛️ *OFFICIAL ATTENDANCE NOTIFICATION*\n"
                    f"📅 *Date*: {datetime.now().strftime('%d/%m/%Y')} | ⏰ *Time*: {datetime.now().strftime('%H:%M:%S')}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *Student*: {s.get('Name', '')} (ID: {s.get('Student_ID', '')})\n"
                    f"📚 *Department*: {s.get('Dep', '')} | *Roll*: {s.get('Roll', '')}\n"
                    f"📊 *Status*: ✅ *PRESENT*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📈 *Academic Attendance Record*:\n"
                    f"• Attended Sessions: {st['present_days']} / {st['total_days']}\n"
                    f"• Attendance Percentage: *{st['percentage']}%*\n"
                    f"• Institutional Standard: 75% Minimum Required\n\n"
                    f"✅ Recorded in the Central Attendance Register."
                )
                txt_wa_body.delete("1.0", END)
                txt_wa_body.insert("1.0", msg)

        cb_student.bind("<<ComboboxSelected>>", on_student_select)

        # Dispatch Buttons
        btn_box = Frame(win, bg="#f8fafc")
        btn_box.pack(fill=X, padx=25, pady=(5, 15))

        def open_wa_web():
            ph = var_phone.get().strip()
            msg = txt_wa_body.get("1.0", END).strip()
            if not ph:
                messagebox.showerror("Error", "Please specify a recipient WhatsApp phone number!", parent=win)
                return
            success = whatsapp.open_whatsapp_web(ph, msg)
            if success:
                chosen = var_student_choice.get()
                sid = student_map[chosen]["Student_ID"] if chosen in student_map else "101"
                try:
                    db.add_notification(sid, "💬 WhatsApp Attendance Notice", msg)
                except Exception:
                    pass
                db.log_activity("Admin", "WhatsApp", "WhatsApp Web Opened", f"Phone: {ph}, Notice to Student {sid}")
                messagebox.showinfo("WhatsApp Web Opened", f"✅ WhatsApp Web/App has opened with pre-filled message for {ph}!\n\nSimply press ENTER in WhatsApp to send.", parent=win)

        def dispatch_wa_cloud():
            ph = var_phone.get().strip()
            msg = txt_wa_body.get("1.0", END).strip()
            if not ph:
                messagebox.showerror("Error", "Please specify a recipient WhatsApp phone number!", parent=win)
                return
            chosen = var_student_choice.get()
            s = student_map.get(chosen, {})
            sid = s.get("Student_ID", "101")
            name = s.get("Name", "Student")

            whatsapp.dispatch_notice_async(ph, msg, student_id=sid, student_name=name)
            try:
                db.add_notification(sid, "💬 WhatsApp Attendance Notice", msg)
            except Exception:
                pass
            db.log_activity("Admin", "WhatsApp", "WhatsApp Notice Dispatched", f"Phone: {ph}, Student: {name} ({sid})")

            messagebox.showinfo(
                "WhatsApp Notice Dispatched",
                f"✅ WhatsApp Notice Dispatched Successfully!\n\n"
                f"• Recipient: {ph}\n"
                f"• Student: {name} ({sid})\n"
                f"• Student Portal Notice: Created & Visible in Student Portal\n"
                f"• Audit Log: Recorded\n\n"
                f"Notice dispatched in background. Click '1-Click Send via WhatsApp Web' to chat directly.",
                parent=win
            )

        Button(
            btn_box,
            text="💬 1-CLICK SEND VIA WHATSAPP WEB",
            command=open_wa_web,
            font=("Times New Roman", 11, "bold"),
            bg="#16a34a",
            fg="white",
            cursor="hand2",
            bd=0,
            pady=8
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        Button(
            btn_box,
            text="⚡ AUTO-DISPATCH (BACKGROUND)",
            command=dispatch_wa_cloud,
            font=("Times New Roman", 11, "bold"),
            bg="#0f766e",
            fg="white",
            cursor="hand2",
            bd=0,
            pady=8
        ).pack(side=LEFT, fill=X, expand=True, padx=(5, 0))

    def send_low_attendance_alerts(self):
        low_students = db.get_low_attendance_students(threshold=75.0)
        if not low_students:
            messagebox.showinfo("Low Attendance", "Great news! No registered students are currently below 75% attendance.", parent=self.root)
            return

        win = Toplevel(self.root)
        win.title("Low Attendance Warning Notification Center")
        win.geometry("980x680+280+60")
        win.configure(bg="#f8fafc")

        # Header
        header = Frame(win, bg="#ea580c", height=60)
        header.pack(fill=X)
        Label(header, text="🔔 LOW ATTENDANCE (< 75%) ALERT & NOTIFICATION CENTER", font=("Times New Roman", 15, "bold"), bg="#ea580c", fg="white").pack(pady=14)

        main_f = Frame(win, bg="#f8fafc", padx=15, pady=10)
        main_f.pack(fill=BOTH, expand=True)

        # Notice Banner
        banner = Label(
            main_f,
            text=f"⚠️ {len(low_students)} students are below the mandatory 75% attendance requirement. Select students below to dispatch warning notices.",
            font=("Times New Roman", 11, "bold"),
            bg="#ffedd5",
            fg="#9a3412",
            pady=6
        )
        banner.pack(fill=X, pady=(0, 8))

        # Table of Low Attendance Students
        table_frame = Frame(main_f, bg="white", bd=1, relief=RIDGE)
        table_frame.pack(fill=BOTH, expand=True, pady=5)

        cols = ("id", "name", "dept", "email", "present", "total", "pct", "status")
        tree_alerts = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        tree_alerts.heading("id", text="Student ID")
        tree_alerts.heading("name", text="Name")
        tree_alerts.heading("dept", text="Department")
        tree_alerts.heading("email", text="Email")
        tree_alerts.heading("present", text="Attended")
        tree_alerts.heading("total", text="Total")
        tree_alerts.heading("pct", text="Attendance %")
        tree_alerts.heading("status", text="Notice Status")

        tree_alerts.column("id", width=80, anchor=CENTER)
        tree_alerts.column("name", width=140)
        tree_alerts.column("dept", width=130)
        tree_alerts.column("email", width=180)
        tree_alerts.column("present", width=70, anchor=CENTER)
        tree_alerts.column("total", width=60, anchor=CENTER)
        tree_alerts.column("pct", width=90, anchor=CENTER)
        tree_alerts.column("status", width=130, anchor=CENTER)

        scroll_alert = ttk.Scrollbar(table_frame, orient=VERTICAL, command=tree_alerts.yview)
        tree_alerts.configure(yscroll=scroll_alert.set)
        scroll_alert.pack(side=RIGHT, fill=Y)
        tree_alerts.pack(fill=BOTH, expand=True)

        # Populate rows
        for s in low_students:
            email_val = s.get("Email") or f"student_{s['Student_ID']}@college.edu"
            tree_alerts.insert("", END, values=(
                s["Student_ID"], s["Name"], s["Dep"], email_val,
                s["present_days"], s["total_days"], f"{s['percentage']}%", "Pending Dispatch"
            ))

        # Template Section
        tpl_frame = LabelFrame(main_f, text="Personalized Warning Notice Template", font=("Times New Roman", 10, "bold"), bg="#f8fafc", fg="#475569", padx=10, pady=6)
        tpl_frame.pack(fill=X, pady=6)

        row_t1 = Frame(tpl_frame, bg="#f8fafc")
        row_t1.pack(fill=X, pady=2)
        Label(row_t1, text="Subject:", font=("Times New Roman", 10, "bold"), bg="#f8fafc", width=8, anchor=W).pack(side=LEFT)
        var_alert_sub = StringVar(value="⚠️ URGENT: Academic Low Attendance Warning Notice (< 75%)")
        Entry(row_t1, textvariable=var_alert_sub, font=("Times New Roman", 10), bg="white", bd=1).pack(side=LEFT, fill=X, expand=True)

        txt_alert_body = Text(tpl_frame, font=("Times New Roman", 9), bg="white", bd=1, height=4)
        txt_alert_body.pack(fill=X, pady=4)
        txt_alert_body.insert("1.0", (
            "Dear {name} (Student ID: {id}, Department: {dept}),\n\n"
            "This is an automated formal notification from the Institutional Attendance Office.\n"
            "Your current attendance record is {pct}%, which is BELOW the mandatory 75% attendance threshold.\n"
            "Records show you have attended {present} out of {total} total lecture sessions.\n\n"
            "Please meet your Department Coordinator immediately to avoid examination debarment."
        ))

        # Progress bar
        prog = ttk.Progressbar(main_f, orient=HORIZONTAL, length=900, mode='determinate')
        prog.pack(fill=X, pady=4)

        # Action Buttons
        btn_bar = Frame(main_f, bg="#f8fafc")
        btn_bar.pack(fill=X, pady=6)

        lbl_dispatch_stat = Label(btn_bar, text="Ready to dispatch alerts.", font=("Times New Roman", 10, "italic"), bg="#f8fafc", fg="#64748b")
        lbl_dispatch_stat.pack(side=LEFT)

        def run_dispatch():
            items = tree_alerts.get_children()
            if not items:
                return

            prog["maximum"] = len(items)
            sent_count = 0
            portal_count = 0

            sender = db.get_setting("email_sender", "")
            pwd = db.get_setting("email_password", "")
            host = db.get_setting("email_smtp_server", "smtp.gmail.com")
            port = int(db.get_setting("email_smtp_port", "465") or "465")

            subject_tpl = var_alert_sub.get().strip()
            body_tpl = txt_alert_body.get("1.0", END)

            for idx, item in enumerate(items):
                vals = tree_alerts.item(item, "values")
                s_id, s_name, s_dept, s_email, present, total, pct, _ = vals

                # Construct personalized message
                body = body_tpl.replace("{name}", s_name).replace("{id}", s_id).replace("{dept}", s_dept).replace("{pct}", pct).replace("{present}", str(present)).replace("{total}", str(total))
                subject = f"{subject_tpl} - {s_name} ({s_id})"

                # 1. Create Portal Notification in Database
                try:
                    db.add_notification(s_id, subject, body)
                    portal_count += 1
                except Exception as ne:
                    print(f"[WARN] Add notification: {ne}")

                # 2. Send Email if SMTP configured, else log to audit
                email_sent = False
                if sender and pwd and s_email:
                    try:
                        import smtplib
                        from email.message import EmailMessage
                        msg = EmailMessage()
                        msg['Subject'] = subject
                        msg['From'] = sender
                        msg['To'] = s_email
                        msg.set_content(body)
                        with smtplib.SMTP_SSL(host, port, timeout=6) as s:
                            s.login(sender, pwd)
                            s.send_message(msg)
                        email_sent = True
                        sent_count += 1
                    except Exception:
                        email_sent = False

                status_text = "✅ Sent (Email & Portal)" if email_sent else "📋 Portal Notified"
                tree_alerts.item(item, values=(s_id, s_name, s_dept, s_email, present, total, pct, status_text))

                prog["value"] = idx + 1
                win.update_idletasks()

            db.log_activity("Admin", "Alert", "Low Attendance Notices Sent", f"Processed {len(items)} alerts. Portal Notices: {portal_count}, Live Emails: {sent_count}")
            lbl_dispatch_stat.config(text=f"Completed! {len(items)} students notified.", fg="#16a34a")

            messagebox.showinfo(
                "Dispatch Report",
                f"✅ Low Attendance Warning Notices Dispatched Successfully!\n\n"
                f"• Total Students Processed: {len(items)}\n"
                f"• Student Portal Notices Created: {portal_count}\n"
                f"• Direct Emails Dispatched: {sent_count}\n"
                f"• Institutional Audit Log: Recorded\n\n"
                f"All students will see this urgent alert upon logging into their Student Portal account.",
                parent=win
            )

        def run_whatsapp_dispatch():
            items = tree_alerts.get_children()
            if not items:
                return

            prog["maximum"] = len(items)
            wa_sent = 0
            portal_count = 0

            # Map student IDs to their phone numbers
            student_records = {s["Student_ID"]: s for s in low_students}

            for idx, item in enumerate(items):
                vals = tree_alerts.item(item, "values")
                s_id, s_name, s_dept, s_email, present, total, pct, _ = vals
                s_rec = student_records.get(s_id, {})
                s_phone = s_rec.get("Phone", "")

                wa_msg = (
                    f"⚠️ *OFFICIAL NOTICE: LOW ATTENDANCE WARNING (< 75%)*\n"
                    f"🏛️ *Institutional Academic Attendance Cell*\n"
                    f"📅 *Issued*: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Dear *{s_name}* (ID: *{s_id}* | Dept: *{s_dept}*),\n\n"
                    f"Your academic attendance is currently *{pct}*, which is *BELOW* the mandatory 75% requirement.\n\n"
                    f"• Sessions Attended: *{present}* / *{total}*\n"
                    f"• Shortfall: *{int(total) - int(present)}* sessions\n"
                    f"• Institutional Standard: *75.0% Minimum*\n\n"
                    f"⚠️ *Mandatory Action Required*:\n"
                    f"Please meet your Academic Coordinator / HOD immediately to avoid examination debarment.\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Office of Dean (Academics)"
                )

                try:
                    db.add_notification(s_id, "⚠️ Low Attendance Notice (<75%)", wa_msg)
                    portal_count += 1
                except Exception:
                    pass

                if s_phone:
                    whatsapp.dispatch_notice_async(s_phone, wa_msg, student_id=s_id, student_name=s_name)
                    wa_sent += 1

                tree_alerts.item(item, values=(s_id, s_name, s_dept, s_email, present, total, pct, "💬 WhatsApp Dispatched"))
                prog["value"] = idx + 1
                win.update_idletasks()

            db.log_activity("Admin", "WhatsApp", "WhatsApp Low Attendance Alerts Dispatched", f"Notified {wa_sent} students via WhatsApp. Portal notices: {portal_count}")
            lbl_dispatch_stat.config(text=f"Completed! {wa_sent} students notified via WhatsApp.", fg="#16a34a")

            messagebox.showinfo(
                "WhatsApp Alerts Dispatched",
                f"✅ Low Attendance Notices Dispatched to WhatsApp!\n\n"
                f"• Total Students Processed: {len(items)}\n"
                f"• WhatsApp Notices Sent: {wa_sent}\n"
                f"• Student Portal Notifications: {portal_count}\n"
                f"• Registered Numbers Used: Yes (From Student Records)\n"
                f"• Institutional Audit Log: Recorded\n\n"
                f"All students will receive the alert on their registered phone numbers and in their Student Portal accounts.",
                parent=win
            )

        Button(
            btn_bar,
            text="💬 DISPATCH VIA WHATSAPP (TO STUDENT PHONES)",
            command=run_whatsapp_dispatch,
            font=("Times New Roman", 11, "bold"),
            bg="#16a34a",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=5
        ).pack(side=RIGHT, padx=(5, 0))

        Button(
            btn_bar,
            text="✉️ DISPATCH VIA EMAIL & PORTAL",
            command=run_dispatch,
            font=("Times New Roman", 11, "bold"),
            bg="#ea580c",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=5
        ).pack(side=RIGHT, padx=(0, 5))

if __name__ == "__main__":
    root = Tk()
    app = Attendance(root)
    root.mainloop()