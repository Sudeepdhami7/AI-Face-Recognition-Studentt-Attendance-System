import os
from datetime import datetime
from tkinter import *
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from db_manager import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class StudentPortal:
    def __init__(self, root, student_id="101"):
        self.root = root
        self.student_id = str(student_id).strip()
        self.root.geometry("1200x720+160+70")
        self.root.title(f"Student Attendance Portal - ID: {self.student_id}")
        self.root.configure(bg="#f8fafc")

        self.student_data = db.get_student_by_id(self.student_id)
        if not self.student_data:
            # Fallback mock if student record isn't in student table
            self.student_data = {
                "Student_ID": self.student_id,
                "Name": self.student_id,
                "Dep": "General",
                "Course": "Degree",
                "Roll": "N/A"
            }

        self.build_ui()
        self.load_attendance_data()

    def build_ui(self):
        # Header
        header = Frame(self.root, bg="#1e293b", height=70)
        header.place(x=0, y=0, width=1200, height=70)

        Label(
            header,
            text=f"🎓 STUDENT ATTENDANCE PORTAL | {self.student_data.get('Name', 'Student').upper()}",
            font=("Times New Roman", 20, "bold"),
            bg="#1e293b",
            fg="#38bdf8"
        ).place(x=25, y=18)

        Button(
            header,
            text="🚪 Logout",
            command=self.logout,
            font=("Times New Roman", 10, "bold"),
            bg="#dc2626",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=12,
            pady=4
        ).place(x=1090, y=18)

        # Profile Card & KPIs
        top_container = Frame(self.root, bg="#f8fafc")
        top_container.place(x=25, y=85, width=1150, height=120)

        # Student Details Card
        profile_card = Frame(top_container, bg="white", bd=1, relief=RIDGE)
        profile_card.place(x=0, y=0, width=420, height=120)

        Label(profile_card, text=f"Name: {self.student_data.get('Name')}", font=("Times New Roman", 12, "bold"), bg="white", fg="#0f172a").place(x=15, y=12)
        Label(profile_card, text=f"Student ID: {self.student_data.get('Student_ID')}", font=("Times New Roman", 11), bg="white", fg="#475569").place(x=15, y=38)
        Label(profile_card, text=f"Department: {self.student_data.get('Dep')}", font=("Times New Roman", 11), bg="white", fg="#475569").place(x=15, y=62)
        Label(profile_card, text=f"Roll No: {self.student_data.get('Roll', 'N/A')}", font=("Times New Roman", 11), bg="white", fg="#475569").place(x=15, y=86)

        # KPI Stats Cards
        stats = db.get_student_stats(self.student_id)

        def make_stat(x, title, val, bg_c, fg_c):
            f = Frame(top_container, bg=bg_c, bd=1, relief=FLAT)
            f.place(x=x, y=0, width=165, height=120)
            Label(f, text=title, font=("Times New Roman", 10, "bold"), bg=bg_c, fg="#e2e8f0").pack(pady=(20, 5))
            Label(f, text=str(val), font=("Times New Roman", 22, "bold"), bg=bg_c, fg=fg_c).pack()

        make_stat(440, "TOTAL SESSIONS", stats["total_days"], "#0f172a", "#38bdf8")
        make_stat(620, "PRESENT DAYS", stats["present_days"], "#065f46", "#34d399")
        make_stat(800, "ABSENT DAYS", stats["absent_days"], "#991b1b", "#f87171")
        make_stat(980, "ATTENDANCE %", f"{stats['percentage']}%", "#1e3a8a", "#60a5fa")

        # Low Attendance Alert Banner if < 75%
        if stats["total_days"] > 0 and stats["percentage"] < 75.0:
            alert_bar = Frame(self.root, bg="#fee2e2", bd=1, relief=SOLID)
            alert_bar.place(x=25, y=215, width=1150, height=35)
            Label(
                alert_bar,
                text=f"⚠️ LOW ATTENDANCE WARNING: Your attendance is currently {stats['percentage']}% (below required 75%). Please attend upcoming sessions regularly.",
                font=("Times New Roman", 11, "bold"),
                bg="#fee2e2",
                fg="#b91c1c"
            ).pack(pady=6)
            table_y = 260
            table_h = 390
        else:
            table_y = 220
            table_h = 430

        # Attendance Records Table
        table_frame = Frame(self.root, bg="white", bd=1, relief=RIDGE)
        table_frame.place(x=25, y=table_y, width=1150, height=table_h)

        cols = ("date", "time", "status", "mode")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree.heading("date", text="Date")
        self.tree.heading("time", text="Time Recorded")
        self.tree.heading("status", text="Status")
        self.tree.heading("mode", text="Verification Mode")

        self.tree.column("date", width=180, anchor=CENTER)
        self.tree.column("time", width=180, anchor=CENTER)
        self.tree.column("status", width=160, anchor=CENTER)
        self.tree.column("mode", width=220, anchor=CENTER)

        scroll = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        scroll.pack(side=RIGHT, fill=Y)
        self.tree.pack(fill=BOTH, expand=True)

        # Bottom Actions Bar
        b_bar = Frame(self.root, bg="#f8fafc")
        b_bar.place(x=25, y=660, width=1150, height=45)

        Button(
            b_bar,
            text="📥 Download Personal PDF Report",
            command=self.download_pdf,
            font=("Times New Roman", 11, "bold"),
            bg="#dc2626",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=5
        ).pack(side=LEFT, padx=5)

        Button(
            b_bar,
            text="📊 Download Personal Excel Sheet",
            command=self.download_excel,
            font=("Times New Roman", 11, "bold"),
            bg="#16a34a",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=5
        ).pack(side=LEFT, padx=5)

        Button(
            b_bar,
            text="🔔 View Official Notices",
            command=self.view_notices,
            font=("Times New Roman", 11, "bold"),
            bg="#d97706",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=5
        ).pack(side=RIGHT, padx=5)

    def view_notices(self):
        notices = db.get_student_notifications(self.student_id)
        win = Toplevel(self.root)
        win.title("Official Attendance Notices")
        win.geometry("700x450+380+180")
        win.configure(bg="#f8fafc")

        header = Frame(win, bg="#d97706", height=50)
        header.pack(fill=X)
        Label(header, text="🔔 OFFICIAL ATTENDANCE & WARNING NOTICES", font=("Times New Roman", 14, "bold"), bg="#d97706", fg="white").pack(pady=12)

        if not notices:
            Label(win, text="No formal warning notices on file for your account.", font=("Times New Roman", 12), bg="#f8fafc", fg="#64748b").pack(pady=50)
            return

        body_frame = Frame(win, bg="#f8fafc", padx=15, pady=10)
        body_frame.pack(fill=BOTH, expand=True)

        for n in notices[:5]:
            box = LabelFrame(body_frame, text=f"Notice: {n['Title']} | Date: {n['Date']}", font=("Times New Roman", 10, "bold"), bg="white", fg="#b45309", padx=10, pady=8)
            box.pack(fill=X, pady=6)
            Label(box, text=n["Message"], font=("Consolas", 9), bg="white", justify=LEFT, wraplength=640).pack(anchor=W)

    def load_attendance_data(self):
        records = db.get_attendance_records(student_id=self.student_id)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in records:
            self.tree.insert("", END, values=(
                r["Date"], r["Time"], r["Status"], r.get("Mode", "CCTV/Webcam")
            ))

    def download_pdf(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF File", "*.pdf")],
            initialfile=f"Attendance_Report_{self.student_id}.pdf",
            parent=self.root
        )
        if not filepath:
            return

        try:
            records = db.get_attendance_records(student_id=self.student_id)
            stats = db.get_student_stats(self.student_id)
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            elements.append(Paragraph("STUDENT ATTENDANCE REPORT", styles['Title']))
            elements.append(Paragraph(f"Student: {self.student_data.get('Name')} | ID: {self.student_id} | Dept: {self.student_data.get('Dep')}", styles['Normal']))
            elements.append(Paragraph(f"Attendance: {stats['percentage']}% | Present: {stats['present_days']}/{stats['total_days']} Sessions", styles['Normal']))
            elements.append(Spacer(1, 15))

            data = [["Date", "Time", "Status", "Mode"]]
            for r in records:
                data.append([r["Date"], r["Time"], r["Status"], r.get("Mode", "CCTV/Webcam")])

            t = Table(data, colWidths=[120, 120, 100, 150])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(t)
            doc.build(elements)
            messagebox.showinfo("Success", f"Personal PDF report generated!\nSaved: {filepath}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Could not export PDF: {str(e)}", parent=self.root)

    def download_excel(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel File", "*.xlsx")],
            initialfile=f"Attendance_{self.student_id}.xlsx",
            parent=self.root
        )
        if not filepath:
            return

        try:
            records = db.get_attendance_records(student_id=self.student_id)
            wb = Workbook()
            ws = wb.active
            ws.title = "My Attendance"
            ws.append(["Date", "Time", "Status", "Verification Mode"])
            for r in records:
                ws.append([r["Date"], r["Time"], r["Status"], r.get("Mode", "CCTV/Webcam")])
            wb.save(filepath)
            messagebox.showinfo("Success", f"Excel sheet exported!\nSaved: {filepath}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Could not export Excel: {str(e)}", parent=self.root)

    def logout(self):
        self.root.destroy()
        from login import LoginWindow
        root = Tk()
        app = LoginWindow(root)
        root.mainloop()

if __name__ == "__main__":
    root = Tk()
    app = StudentPortal(root, "101")
    root.mainloop()
