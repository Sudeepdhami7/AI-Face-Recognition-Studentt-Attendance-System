import csv
import os
from datetime import datetime
from tkinter import *
from tkinter import filedialog, messagebox, ttk
import numpy as np
from PIL import Image, ImageTk


class Attendance:

    def __init__(self, root):
        self.root = root
        self.root.geometry("1530x790+0+0")
        self.root.title("Face Recognition System - Attendance Management")

        # Variables
        self.var_atten_id = StringVar()
        self.var_atten_roll = StringVar()
        self.var_atten_name = StringVar()
        self.var_atten_dep = StringVar()
        self.var_atten_time = StringVar()
        self.var_atten_date = StringVar()
        self.var_atten_status = StringVar()

        # ================= Top Banner Images =================
        try:
            img_left = Image.open(
                r"C:\Users\sudee\OneDrive\Desktop\DATA SCIENCE\face recognition\face_recognition\photo7.jpg"
            )
            img_left = img_left.resize((800, 200), Image.Resampling.LANCZOS)
            self.photoimg_left = ImageTk.PhotoImage(img_left)
            f_lbl_left = Label(self.root, image=self.photoimg_left)
            f_lbl_left.place(x=0, y=0, width=800, height=200)
        except Exception:
            f_lbl_left = Label(
                self.root,
                text="ATTENDANCE BANNER LEFT",
                bg="lightblue",
                font=("Times New Roman", 18, "bold"),
            )
            f_lbl_left.place(x=0, y=0, width=800, height=200)

        try:
            img_right = Image.open(
                r"C:\Users\sudee\OneDrive\Desktop\DATA SCIENCE\face recognition\face_recognition\photo6.jpg"
            )
            img_right = img_right.resize((730, 200), Image.Resampling.LANCZOS)
            self.photoimg_right = ImageTk.PhotoImage(img_right)
            f_lbl_right = Label(self.root, image=self.photoimg_right)
            f_lbl_right.place(x=800, y=0, width=730, height=200)
        except Exception:
            f_lbl_right = Label(
                self.root,
                text="ATTENDANCE BANNER RIGHT",
                bg="lightgreen",
                font=("Times New Roman", 18, "bold"),
            )
            f_lbl_right.place(x=800, y=0, width=730, height=200)

        # Title Label
        title_lbl = Label(
            self.root,
            text="ATTENDANCE MANAGEMENT SYSTEM",
            font=("times new roman", 30, "bold"),
            bg="darkgreen",
            fg="white",
        )
        title_lbl.place(x=0, y=200, width=1530, height=45)

        # Main Container Frame
        main_frame = Frame(self.root, bd=2, bg="white")
        main_frame.place(x=10, y=250, width=1510, height=530)

        # ================= Left Frame (Form Controls) =================
        Left_frame = LabelFrame(
            main_frame,
            bd=2,
            bg="white",
            relief=RIDGE,
            text="Student Attendance Details",
            font=("times new roman", 12, "bold"),
        )
        Left_frame.place(x=10, y=10, width=730, height=500)

        left_inside_frame = Frame(Left_frame, bd=2, relief=RIDGE, bg="white")
        left_inside_frame.place(x=10, y=15, width=705, height=380)

        # Form Field Inputs
        lbl_id = Label(
            left_inside_frame,
            text="Attendance ID:",
            font=("times new roman", 12, "bold"),
            bg="white",
        )
        lbl_id.grid(row=0, column=0, padx=10, pady=10, sticky=W)
        entry_id = ttk.Entry(
            left_inside_frame,
            textvariable=self.var_atten_id,
            width=20,
            font=("times new roman", 12),
        )
        entry_id.grid(row=0, column=1, padx=10, pady=10, sticky=W)

        lbl_roll = Label(
            left_inside_frame,
            text="Roll No:",
            font=("times new roman", 12, "bold"),
            bg="white",
        )
        lbl_roll.grid(row=0, column=2, padx=10, pady=10, sticky=W)
        entry_roll = ttk.Entry(
            left_inside_frame,
            textvariable=self.var_atten_roll,
            width=20,
            font=("times new roman", 12),
        )
        entry_roll.grid(row=0, column=3, padx=10, pady=10, sticky=W)

        lbl_name = Label(
            left_inside_frame,
            text="Name:",
            font=("times new roman", 12, "bold"),
            bg="white",
        )
        lbl_name.grid(row=1, column=0, padx=10, pady=10, sticky=W)
        entry_name = ttk.Entry(
            left_inside_frame,
            textvariable=self.var_atten_name,
            width=20,
            font=("times new roman", 12),
        )
        entry_name.grid(row=1, column=1, padx=10, pady=10, sticky=W)

        lbl_dep = Label(
            left_inside_frame,
            text="Department:",
            font=("times new roman", 12, "bold"),
            bg="white",
        )
        lbl_dep.grid(row=1, column=2, padx=10, pady=10, sticky=W)
        entry_dep = ttk.Entry(
            left_inside_frame,
            textvariable=self.var_atten_dep,
            width=20,
            font=("times new roman", 12),
        )
        entry_dep.grid(row=1, column=3, padx=10, pady=10, sticky=W)

        lbl_time = Label(
            left_inside_frame,
            text="Time:",
            font=("times new roman", 12, "bold"),
            bg="white",
        )
        lbl_time.grid(row=2, column=0, padx=10, pady=10, sticky=W)
        entry_time = ttk.Entry(
            left_inside_frame,
            textvariable=self.var_atten_time,
            width=20,
            font=("times new roman", 12),
        )
        entry_time.grid(row=2, column=1, padx=10, pady=10, sticky=W)

        lbl_date = Label(
            left_inside_frame,
            text="Date:",
            font=("times new roman", 12, "bold"),
            bg="white",
        )
        lbl_date.grid(row=2, column=2, padx=10, pady=10, sticky=W)
        entry_date = ttk.Entry(
            left_inside_frame,
            textvariable=self.var_atten_date,
            width=20,
            font=("times new roman", 12),
        )
        entry_date.grid(row=2, column=3, padx=10, pady=10, sticky=W)

        lbl_status = Label(
            left_inside_frame,
            text="Attendance Status:",
            font=("times new roman", 12, "bold"),
            bg="white",
        )
        lbl_status.grid(row=3, column=0, padx=10, pady=10, sticky=W)
        combo_status = ttk.Combobox(
            left_inside_frame,
            textvariable=self.var_atten_status,
            font=("times new roman", 12),
            state="readonly",
            width=18,
        )
        combo_status["values"] = ("Status", "Present", "Absent")
        combo_status.current(0)
        combo_status.grid(row=3, column=1, padx=10, pady=10, sticky=W)

        # Buttons Frame
        btn_frame = Frame(Left_frame, bd=2, relief=RIDGE, bg="white")
        btn_frame.place(x=10, y=410, width=705, height=50)

        btn_import = Button(
            btn_frame,
            text="Import CSV",
            command=self.import_csv,
            width=16,
            font=("times new roman", 12, "bold"),
            bg="blue",
            fg="white",
        )
        btn_import.grid(row=0, column=0, padx=5, pady=8)

        btn_export = Button(
            btn_frame,
            text="Export CSV",
            command=self.export_csv,
            width=16,
            font=("times new roman", 12, "bold"),
            bg="blue",
            fg="white",
        )
        btn_export.grid(row=0, column=1, padx=5, pady=8)

        btn_update = Button(
            btn_frame,
            text="Update",
            command=self.update_data,
            width=16,
            font=("times new roman", 12, "bold"),
            bg="blue",
            fg="white",
        )
        btn_update.grid(row=0, column=2, padx=5, pady=8)

        btn_reset = Button(
            btn_frame,
            text="Reset",
            command=self.reset_data,
            width=16,
            font=("times new roman", 12, "bold"),
            bg="blue",
            fg="white",
        )
        btn_reset.grid(row=0, column=3, padx=5, pady=8)

        # ================= Right Frame (Treeview Table) =================
        Right_frame = LabelFrame(
            main_frame,
            bd=2,
            bg="white",
            relief=RIDGE,
            text="Attendance Records",
            font=("times new roman", 12, "bold"),
        )
        Right_frame.place(x=750, y=10, width=745, height=500)

        table_frame = Frame(Right_frame, bd=2, relief=RIDGE, bg="white")
        table_frame.place(x=5, y=5, width=730, height=465)

        # Scrollbars
        scroll_x = ttk.Scrollbar(table_frame, orient=HORIZONTAL)
        scroll_y = ttk.Scrollbar(table_frame, orient=VERTICAL)

        self.AttendanceReportTable = ttk.Treeview(
            table_frame,
            column=("id", "roll", "name", "department", "time", "date", "status"),
            xscrollcommand=scroll_x.set,
            yscrollcommand=scroll_y.set,
        )

        scroll_x.pack(side=BOTTOM, fill=X)
        scroll_y.pack(side=RIGHT, fill=Y)

        scroll_x.config(command=self.AttendanceReportTable.xview)
        scroll_y.config(command=self.AttendanceReportTable.yview)

        self.AttendanceReportTable.heading("id", text="Student ID")
        self.AttendanceReportTable.heading("roll", text="Roll")
        self.AttendanceReportTable.heading("name", text="Name")
        self.AttendanceReportTable.heading("department", text="Department")
        self.AttendanceReportTable.heading("time", text="Time")
        self.AttendanceReportTable.heading("date", text="Date")
        self.AttendanceReportTable.heading("status", text="Status")

        self.AttendanceReportTable["show"] = "headings"

        self.AttendanceReportTable.column("id", width=100)
        self.AttendanceReportTable.column("roll", width=100)
        self.AttendanceReportTable.column("name", width=120)
        self.AttendanceReportTable.column("department", width=120)
        self.AttendanceReportTable.column("time", width=100)
        self.AttendanceReportTable.column("date", width=100)
        self.AttendanceReportTable.column("status", width=100)

        self.AttendanceReportTable.pack(fill=BOTH, expand=1)
        self.AttendanceReportTable.bind("<ButtonRelease-1>", self.get_cursor)

        # Load default attendance file automatically if present
        self.auto_load_default_csv()

    # ================= Helper Methods =================
    def auto_load_default_csv(self):
        filename = "sudeep.csv"
        if not os.path.exists(filename):
            filename = "attendance.csv"

        if os.path.exists(filename):
            self.fetch_data_from_file(filename)

    def fetch_data_from_file(self, file_path):
        self.AttendanceReportTable.delete(*self.AttendanceReportTable.get_children())
        try:
            with open(file_path, "r", newline="", encoding="utf-8") as f:
                csv_reader = csv.reader(f)
                header = next(csv_reader, None)  # Skip header row
                for row in csv_reader:
                    if row:
                        self.AttendanceReportTable.insert("", END, values=row)
        except Exception as es:
            messagebox.showerror("Error", f"Failed to load file: {es}", parent=self.root)

    def import_csv(self):
        try:
            file_path = filedialog.askopenfilename(
                initialdir=os.getcwd(),
                title="Open CSV File",
                filetypes=(("CSV File", "*.csv"), ("All Files", "*.*")),
                parent=self.root,
            )

            if not file_path:
                return

            self.fetch_data_from_file(file_path)
            messagebox.showinfo(
                "Success",
                f"Successfully imported {os.path.basename(file_path)}",
                parent=self.root,
            )
        except Exception as es:
            messagebox.showerror(
                "Error", f"Could not import CSV file: {es}", parent=self.root
            )

    def export_csv(self):
        try:
            if len(self.AttendanceReportTable.get_children()) < 1:
                messagebox.showwarning("No Data", "No attendance data available to export!", parent=self.root)
                return

            file_path = filedialog.asksaveasfilename(
                initialdir=os.getcwd(),
                title="Save CSV File",
                defaultextension=".csv",
                filetypes=(("CSV File", "*.csv"), ("All Files", "*.*")),
                parent=self.root,
            )
            if file_path:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    csv_writer = csv.writer(f)
                    csv_writer.writerow(["Student_ID", "Roll", "Name", "Department", "Time", "Date", "Status"])
                    for row_id in self.AttendanceReportTable.get_children():
                        row_vals = self.AttendanceReportTable.item(row_id)["values"]
                        csv_writer.writerow(row_vals)
                messagebox.showinfo("Export Successful", f"Data exported to {os.path.basename(file_path)}", parent=self.root)
        except Exception as es:
            messagebox.showerror("Error", f"Could not export file: {es}", parent=self.root)

    def get_cursor(self, event=""):
        cursor_row = self.AttendanceReportTable.focus()
        content = self.AttendanceReportTable.item(cursor_row)
        rows = content["values"]

        if rows:
            self.var_atten_id.set(rows[0])
            self.var_atten_roll.set(rows[1])
            self.var_atten_name.set(rows[2])
            self.var_atten_dep.set(rows[3])
            self.var_atten_time.set(rows[4])
            self.var_atten_date.set(rows[5])
            self.var_atten_status.set(rows[6])

    def update_data(self):
        selected = self.AttendanceReportTable.focus()
        if not selected:
            messagebox.showerror("Error", "Please select a record from the table to update!", parent=self.root)
            return

        self.AttendanceReportTable.item(
            selected,
            values=(
                self.var_atten_id.get(),
                self.var_atten_roll.get(),
                self.var_atten_name.get(),
                self.var_atten_dep.get(),
                self.var_atten_time.get(),
                self.var_atten_date.get(),
                self.var_atten_status.get(),
            ),
        )
        messagebox.showinfo("Success", "Attendance record updated in view!", parent=self.root)

    def reset_data(self):
        self.var_atten_id.set("")
        self.var_atten_roll.set("")
        self.var_atten_name.set("")
        self.var_atten_dep.set("")
        self.var_atten_time.set("")
        self.var_atten_date.set("")
        self.var_atten_status.set("Status")


if __name__ == "__main__":
    root = Tk()
    app = Attendance(root)
    root.mainloop()