import os
import platform
import subprocess
from datetime import datetime
from time import strftime
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk

from db_manager import db

# Module imports
try:
    from student import Student
except ImportError as e:
    Student = None
    print(f"[WARN] student.py import: {e}")

try:
    from face_rec import Face_Recognition
except ImportError as e:
    Face_Recognition = None
    print(f"[WARN] face_rec.py import: {e}")

try:
    from attendance import Attendance
except ImportError as e:
    Attendance = None
    print(f"[WARN] attendance.py import: {e}")

try:
    from train import Train
except ImportError as e:
    Train = None
    print(f"[WARN] train.py import: {e}")

try:
    from developer import Developer
except ImportError as e:
    Developer = None
    print(f"[WARN] developer.py import: {e}")

try:
    from help import Help
except ImportError as e:
    Help = None
    print(f"[WARN] help.py import: {e}")

try:
    from system_tools import SystemToolsWindow
except ImportError as e:
    SystemToolsWindow = None
    print(f"[WARN] system_tools.py import: {e}")

try:
    from student_portal import StudentPortal
except ImportError as e:
    StudentPortal = None
    print(f"[WARN] student_portal.py import: {e}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "face_recognition")

def load_image(filename, size):
    path = os.path.join(IMG_DIR, filename)
    if os.path.exists(path):
        img = Image.open(path)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    return None


class FaceRecognitionSystem:
    def __init__(self, root, current_user="Admin", current_role="Admin"):
        self.root = root
        self.current_user = current_user
        self.current_role = current_role

        self.root.geometry("1530x820+0+0")
        self.root.title(f"AI Face Recognition & CCTV Attendance System - [{self.current_role}: {self.current_user}]")
        self.root.configure(bg="#0f172a")

        self.var_cctv_quick_url = StringVar(value=db.get_setting("default_cctv_url", "http://172.16.113.232:8080/video"))

        self.build_ui()

    def build_ui(self):
        # ================= Top 3 Header Images =================
        self.photoimg = load_image("agc.jpg", (510, 110))
        f_lbl = Label(self.root, image=self.photoimg, bg="#1e293b")
        f_lbl.place(x=0, y=0, width=510, height=110)

        self.photoimg2 = load_image("images2.jpg", (510, 110))
        f_lbl2 = Label(self.root, image=self.photoimg2, bg="#1e293b")
        f_lbl2.place(x=510, y=0, width=510, height=110)

        self.photoimg3 = load_image("images11.jpg", (510, 110))
        f_lbl3 = Label(self.root, image=self.photoimg3, bg="#1e293b")
        f_lbl3.place(x=1020, y=0, width=510, height=110)

        # ================= Main Header Bar =================
        header_bar = Frame(self.root, bg="#1e293b", height=50)
        header_bar.place(x=0, y=110, width=1530, height=50)

        Label(
            header_bar,
            text="AI FACE RECOGNITION & CCTV ATTENDANCE SYSTEM SOFTWARE",
            font=("Times New Roman", 18, "bold"),
            bg="#1e293b",
            fg="#38bdf8"
        ).place(x=20, y=10)

        # User Role Badge
        Label(
            header_bar,
            text=f"👤 {self.current_user} ({self.current_role})",
            font=("Times New Roman", 11, "bold"),
            bg="#0f172a",
            fg="#4ade80",
            padx=12,
            pady=4
        ).place(x=1140, y=10)

        # Clock
        self.lbl_clock = Label(header_bar, font=("Consolas", 12, "bold"), bg="#1e293b", fg="#e2e8f0")
        self.lbl_clock.place(x=1380, y=12)
        self.update_clock()

        # ================= Quick CCTV Connection Bar (Feature 1) =================
        cctv_bar = Frame(self.root, bg="#0284c7", height=45)
        cctv_bar.place(x=0, y=160, width=1530, height=45)

        Label(
            cctv_bar,
            text="🎥 CCTV / RTSP Quick-Connect:",
            font=("Times New Roman", 12, "bold"),
            bg="#0284c7",
            fg="white"
        ).place(x=20, y=10)

        Entry(
            cctv_bar,
            textvariable=self.var_cctv_quick_url,
            font=("Consolas", 11),
            bg="#f8fafc",
            bd=1
        ).place(x=270, y=8, width=420, height=28)

        Button(
            cctv_bar,
            text="💻 Laptop (0)",
            command=lambda: self.set_quick_url("0"),
            font=("Times New Roman", 10, "bold"),
            bg="#0369a1",
            fg="white",
            cursor="hand2",
            bd=0
        ).place(x=705, y=8, width=90, height=28)

        Button(
            cctv_bar,
            text="🔌 USB Cam (1)",
            command=lambda: self.set_quick_url("1"),
            font=("Times New Roman", 10, "bold"),
            bg="#0369a1",
            fg="white",
            cursor="hand2",
            bd=0
        ).place(x=805, y=8, width=100, height=28)

        Button(
            cctv_bar,
            text="📱 IP Webcam",
            command=self.prompt_ip_webcam_quick,
            font=("Times New Roman", 10, "bold"),
            bg="#0369a1",
            fg="white",
            cursor="hand2",
            bd=0
        ).place(x=915, y=8, width=95, height=28)

        Button(
            cctv_bar,
            text="⚡ CONNECT & START CCTV ATTENDANCE",
            command=self.launch_cctv_direct,
            font=("Times New Roman", 11, "bold"),
            bg="#16a34a",
            fg="white",
            cursor="hand2",
            bd=0
        ).place(x=1025, y=8, width=320, height=28)

        # Active Schedule Indicator
        allowed, sched_msg = db.is_attendance_allowed_now()
        sched_color = "#22c55e" if allowed else "#f97316"
        Label(
            cctv_bar,
            text=f"● {sched_msg}",
            font=("Times New Roman", 9, "bold"),
            bg="#0284c7",
            fg=sched_color
        ).place(x=1360, y=12)

        # ================= Real-Time KPI Cards (Feature 2) =================
        kpi_container = Frame(self.root, bg="#0f172a", height=75)
        kpi_container.place(x=20, y=215, width=1490, height=75)

        kpis = db.get_dashboard_kpis()

        def make_kpi(x, title, val, bg_c, fg_c):
            f = Frame(kpi_container, bg=bg_c, bd=1, relief=FLAT)
            f.place(x=x, y=0, width=355, height=75)
            Label(f, text=title, font=("Times New Roman", 10, "bold"), bg=bg_c, fg="#cbd5e1").pack(pady=(8, 2))
            Label(f, text=str(val), font=("Times New Roman", 20, "bold"), bg=bg_c, fg=fg_c).pack()

        make_kpi(0, "TOTAL REGISTERED STUDENTS", kpis["total_students"], "#1e293b", "#38bdf8")
        make_kpi(375, "PRESENT TODAY", kpis["present_today"], "#065f46", "#34d399")
        make_kpi(750, "ABSENT TODAY", kpis["absent_today"], "#991b1b", "#f87171")
        make_kpi(1125, "ATTENDANCE PERCENTAGE", f"{kpis['attendance_pct']}%", "#1e3a8a", "#60a5fa")

        # ================= Main Feature Navigation Buttons Grid =================
        nav_frame = Frame(self.root, bg="#0f172a")
        nav_frame.place(x=20, y=305, width=1490, height=495)

        buttons_def = [
            # Row 1
            ("images10.jpg", "Student Details", self.student_details, "#1e3a8a", 100, 10),
            ("images3.jpg", "CCTV Face Recognizer", self.face_data, "#047857", 400, 10),
            ("attendance.jpg", "Attendance & Analytics", self.attendance_data, "#0284c7", 700, 10),
            ("train_data.jpg", "Train AI Model", self.train_data, "#b91c1c", 1000, 10),
            # Row 2
            ("photos.jpg", "Student Photos", self.open_img, "#475569", 100, 245),
            ("developers.jpg", "System Tools & Logs", self.system_tools_data, "#6d28d9", 400, 245),
            ("images8.jpg", "Student Portal", self.open_student_portal, "#0891b2", 700, 245),
            ("help_desk.jpg", "Developer & Help", self.developer_data, "#334155", 1000, 245),
        ]

        self.btn_images = []
        for img_name, label_text, cmd, color, x_pos, y_pos in buttons_def:
            p_img = load_image(img_name, (200, 155))
            self.btn_images.append(p_img)

            card_f = Frame(nav_frame, bg="#1e293b", bd=1, relief=RIDGE)
            card_f.place(x=x_pos, y=y_pos, width=220, height=215)

            btn_img = Button(card_f, image=p_img, command=cmd, cursor="hand2", bg="#1e293b", bd=0, activebackground="#1e293b")
            btn_img.place(x=10, y=10, width=200, height=155)

            btn_lbl = Button(card_f, text=label_text, command=cmd, cursor="hand2", font=("Times New Roman", 11, "bold"), bg=color, fg="white", bd=0)
            btn_lbl.place(x=10, y=170, width=200, height=35)

        # Logout / Exit Button on bottom right
        btn_logout = Button(
            nav_frame,
            text="🚪 Sign Out",
            command=self.logout_action,
            font=("Times New Roman", 11, "bold"),
            bg="#dc2626",
            fg="white",
            cursor="hand2",
            bd=0
        )
        btn_logout.place(x=1320, y=440, width=130, height=35)

    def update_clock(self):
        self.lbl_clock.config(text=strftime("%I:%M:%S %p"))
        self.root.after(1000, self.update_clock)

    def set_quick_url(self, val):
        from cctv_engine import normalize_camera_source
        norm = str(normalize_camera_source(val))
        self.var_cctv_quick_url.set(norm)
        db.set_setting("default_cctv_url", norm)

    def prompt_ip_webcam_quick(self):
        from cctv_engine import normalize_camera_source
        url = simpledialog.askstring(
            "Android IP Webcam",
            "Enter IP Webcam stream URL:\n(e.g., http://172.16.113.232:8080/video)",
            initialvalue="http://172.16.113.232:8080/video",
            parent=self.root
        )
        if url and url.strip():
            norm = str(normalize_camera_source(url.strip()))
            self.set_quick_url(norm)

    def launch_cctv_direct(self):
        from cctv_engine import normalize_camera_source
        url = self.var_cctv_quick_url.get().strip()
        norm = str(normalize_camera_source(url))
        self.var_cctv_quick_url.set(norm)
        db.set_setting("default_cctv_url", norm)
        self.face_data()

    # ================= Navigation Actions =================
    def student_details(self):
        if Student:
            win = Toplevel(self.root)
            self.student_app = Student(win)
        else:
            messagebox.showerror("Error", "Student module could not be loaded.", parent=self.root)

    def face_data(self):
        if Face_Recognition:
            win = Toplevel(self.root)
            self.face_app = Face_Recognition(win, auto_start=True)
        else:
            messagebox.showerror("Error", "Face Recognition module could not be loaded.", parent=self.root)

    def attendance_data(self):
        if Attendance:
            win = Toplevel(self.root)
            self.atten_app = Attendance(win)
        else:
            messagebox.showerror("Error", "Attendance module could not be loaded.", parent=self.root)

    def train_data(self):
        if self.current_role != "Admin":
            messagebox.showerror("Access Denied", "Model training is restricted to Admin role.", parent=self.root)
            return
        if Train:
            win = Toplevel(self.root)
            self.train_app = Train(win)
        else:
            messagebox.showerror("Error", "Train module could not be loaded.", parent=self.root)

    def system_tools_data(self):
        if self.current_role != "Admin":
            messagebox.showerror("Access Denied", "System tools & logs are restricted to Admin role.", parent=self.root)
            return
        if SystemToolsWindow:
            win = Toplevel(self.root)
            self.tools_app = SystemToolsWindow(win)
        else:
            messagebox.showerror("Error", "System Tools module could not be loaded.", parent=self.root)

    def open_student_portal(self):
        # Prompt for Student ID to preview
        sid = simpledialog.askstring(
            "Student Portal Access",
            "Enter Student ID to view personal attendance portal:",
            initialvalue="101",
            parent=self.root
        )
        if sid and sid.strip():
            if StudentPortal:
                win = Toplevel(self.root)
                self.portal_app = StudentPortal(win, student_id=sid.strip())
            else:
                messagebox.showerror("Error", "Student Portal module could not be loaded.", parent=self.root)

    def open_img(self):
        data_path = os.path.join(BASE_DIR, "data")
        os.makedirs(data_path, exist_ok=True)
        if platform.system() == "Windows":
            os.startfile(data_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", data_path])
        else:
            subprocess.Popen(["xdg-open", data_path])

    def developer_data(self):
        if Developer:
            win = Toplevel(self.root)
            self.dev_app = Developer(win)
        else:
            messagebox.showerror("Error", "Developer module could not be loaded.", parent=self.root)

    def help_desk(self):
        if Help:
            win = Toplevel(self.root)
            self.help_app = Help(win)
        else:
            messagebox.showerror("Error", "Help module could not be loaded.", parent=self.root)

    def logout_action(self):
        confirm = messagebox.askyesno("Sign Out", "Are you sure you want to sign out?", parent=self.root)
        if confirm:
            db.log_activity(self.current_user, self.current_role, "Logout", "User signed out")
            self.root.destroy()
            from login import LoginWindow
            new_root = Tk()
            LoginWindow(new_root)
            new_root.mainloop()


if __name__ == "__main__":
    from login import LoginWindow
    root = Tk()
    app = LoginWindow(root)
    root.mainloop()