import os
import random
import string
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

from db_manager import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "face_recognition")

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - AI Face Recognition Attendance System")
        self.root.geometry("1530x790+0+0")
        self.root.configure(bg="#0f172a")

        # Variables
        self.var_login_user = StringVar()
        self.var_login_password = StringVar()
        self.var_login_role = StringVar(value="Admin")

        self.build_ui()

    def build_ui(self):
        # Background image
        img_path = os.path.join(IMG_DIR, "login_bg.jpg")
        if not os.path.exists(img_path):
            img_path = os.path.join(IMG_DIR, "bg.jpg")

        if os.path.exists(img_path):
            try:
                bg_img = Image.open(img_path).resize((1530, 790), Image.Resampling.LANCZOS)
                self.photo_bg = ImageTk.PhotoImage(bg_img)
                bg_lbl = Label(self.root, image=self.photo_bg)
                bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception:
                pass

        # Login Card Frame
        card = Frame(self.root, bg="#ffffff", bd=2, relief=RIDGE)
        card.place(x=540, y=110, width=460, height=580)

        # Header Title
        Label(
            card,
            text="PORTAL LOGIN",
            font=("Times New Roman", 24, "bold"),
            bg="white",
            fg="#1e293b"
        ).pack(pady=(25, 5))

        Label(
            card,
            text="Face Recognition & Attendance System",
            font=("Times New Roman", 11),
            bg="white",
            fg="#64748b"
        ).pack(pady=(0, 20))

        # Role Selector
        Label(card, text="Select Role", font=("Times New Roman", 11, "bold"), bg="white", fg="#334155").place(x=55, y=105)
        role_combo = ttk.Combobox(card, textvariable=self.var_login_role, values=["Admin", "Faculty", "Student"], state="readonly", font=("Times New Roman", 11))
        role_combo.place(x=55, y=130, width=350, height=35)

        # Username / Email
        Label(card, text="Username / Student ID / Email", font=("Times New Roman", 11, "bold"), bg="white", fg="#334155").place(x=55, y=180)
        Entry(card, textvariable=self.var_login_user, font=("Times New Roman", 11), bg="#f8fafc", bd=1).place(x=55, y=205, width=350, height=35)

        # Password
        Label(card, text="Password", font=("Times New Roman", 11, "bold"), bg="white", fg="#334155").place(x=55, y=255)
        Entry(card, textvariable=self.var_login_password, show="*", font=("Times New Roman", 11), bg="#f8fafc", bd=1).place(x=55, y=280, width=350, height=35)

        # Action Buttons
        Button(
            card,
            text="🔐 SIGN IN",
            command=self.login_action,
            font=("Times New Roman", 13, "bold"),
            bg="#2563eb",
            fg="white",
            cursor="hand2",
            bd=0
        ).place(x=55, y=345, width=350, height=42)

        # Sub-actions
        sub_frame = Frame(card, bg="white")
        sub_frame.place(x=55, y=410, width=350, height=30)

        Button(
            sub_frame,
            text="Register New User",
            command=self.open_register_window,
            font=("Times New Roman", 10, "bold"),
            bg="white",
            fg="#16a34a",
            bd=0,
            cursor="hand2"
        ).pack(side=LEFT)

        Button(
            sub_frame,
            text="Forgot Password?",
            command=self.open_forgot_password_dialog,
            font=("Times New Roman", 10, "bold"),
            bg="white",
            fg="#dc2626",
            bd=0,
            cursor="hand2"
        ).pack(side=RIGHT)

        # Role Help Box
        info_lbl = Label(
            card,
            text="Default Credentials:\n• Admin: Admin / 12345\n• Faculty: faculty / 12345\n• Student: Student ID / DOB (or student123)",
            font=("Times New Roman", 9),
            bg="#f1f5f9",
            fg="#475569",
            justify=LEFT,
            padx=10,
            pady=6
        )
        info_lbl.place(x=55, y=460, width=350, height=85)

    def login_action(self):
        username = self.var_login_user.get().strip()
        password = self.var_login_password.get().strip()
        selected_role = self.var_login_role.get()

        if not username or not password:
            messagebox.showerror("Validation Error", "Please enter both Username and Password!", parent=self.root)
            return

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT Username, Password, Role, Fname FROM users 
            WHERE (Username = ? OR Email = ?) AND Password = ?
            """, (username, username, password))
            user = cursor.fetchone()

        if user:
            u_name, u_pwd, u_role, f_name = user["Username"], user["Password"], user["Role"], user["Fname"]
            
            # Allow Admin to log into any role view, or ensure matched role
            if selected_role != u_role and u_role != "Admin":
                messagebox.showerror("Role Mismatch", f"Account '{u_name}' is registered as a {u_role}, not {selected_role}.", parent=self.root)
                db.log_activity(username, selected_role, "Login Failed", "Role mismatch")
                return

            db.log_activity(u_name, selected_role, "Login Success", f"Logged in as {selected_role}")
            messagebox.showinfo("Login Successful", f"Welcome, {f_name or u_name}! Accessing as {selected_role}.", parent=self.root)
            
            self.root.destroy()
            self.route_user(selected_role, u_name)
        else:
            db.log_activity(username, selected_role, "Login Failed", "Invalid credentials")
            messagebox.showerror("Access Denied", "Invalid Username or Password!", parent=self.root)

    def route_user(self, role, username):
        if role == "Student":
            from student_portal import StudentPortal
            root = Tk()
            app = StudentPortal(root, student_id=username)
            root.mainloop()
        else:
            from main import FaceRecognitionSystem
            root = Tk()
            app = FaceRecognitionSystem(root, current_user=username, current_role=role)
            root.mainloop()

    # ================= Password Reset (Security Question & Email OTP) =================
    def open_forgot_password_dialog(self):
        win = Toplevel(self.root)
        win.title("Password Recovery")
        win.geometry("500x520+520+150")
        win.configure(bg="white")
        win.grab_set()

        Label(win, text="PASSWORD RESET PORTAL", font=("Times New Roman", 18, "bold"), bg="white", fg="#dc2626").pack(pady=15)

        tabs = ttk.Notebook(win)
        tabs.pack(fill=BOTH, expand=True, padx=15, pady=10)

        # Tab 1: Security Questions
        tab_sec = Frame(tabs, bg="white")
        tabs.add(tab_sec, text="1. Security Question")

        Label(tab_sec, text="Username / Email:", font=("Times New Roman", 10, "bold"), bg="white").place(x=30, y=20)
        var_sec_user = StringVar()
        Entry(tab_sec, textvariable=var_sec_user, font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=30, y=45, width=400, height=28)

        Label(tab_sec, text="Security Question:", font=("Times New Roman", 10, "bold"), bg="white").place(x=30, y=85)
        var_sec_q = StringVar()
        combo_q = ttk.Combobox(tab_sec, textvariable=var_sec_q, values=["Your Birth Place", "Your Pet Name", "Your Primary School"], state="readonly")
        combo_q.current(0)
        combo_q.place(x=30, y=110, width=400, height=28)

        Label(tab_sec, text="Your Answer:", font=("Times New Roman", 10, "bold"), bg="white").place(x=30, y=150)
        var_sec_a = StringVar()
        Entry(tab_sec, textvariable=var_sec_a, font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=30, y=175, width=400, height=28)

        Label(tab_sec, text="New Password:", font=("Times New Roman", 10, "bold"), bg="white").place(x=30, y=215)
        var_new_p1 = StringVar()
        Entry(tab_sec, textvariable=var_new_p1, show="*", font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=30, y=240, width=400, height=28)

        def reset_via_sec():
            u = var_sec_user.get().strip()
            q = var_sec_q.get()
            a = var_sec_a.get().strip()
            np = var_new_p1.get().strip()
            if not u or not a or not np:
                messagebox.showerror("Error", "All fields are required!", parent=win)
                return

            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE (Username = ? OR Email = ?) AND Security_Q = ? AND Security_A = ?", (u, u, q, a))
                user = cur.fetchone()
                if user:
                    cur.execute("UPDATE users SET Password = ? WHERE Username = ?", (np, user["Username"]))
                    conn.commit()
                    db.log_activity(user["Username"], user["Role"], "Password Reset", "Reset via security question")
                    messagebox.showinfo("Success", "Password reset successfully! You can now log in.", parent=win)
                    win.destroy()
                else:
                    messagebox.showerror("Error", "Security details do not match any registered account.", parent=win)

        Button(tab_sec, text="Reset Password", command=reset_via_sec, font=("Times New Roman", 11, "bold"), bg="#2563eb", fg="white", cursor="hand2", bd=0).place(x=140, y=290, width=180, height=35)

        # Tab 2: Email OTP
        tab_otp = Frame(tabs, bg="white")
        tabs.add(tab_otp, text="2. Email OTP")

        Label(tab_otp, text="Registered Email Address:", font=("Times New Roman", 10, "bold"), bg="white").place(x=30, y=20)
        var_otp_email = StringVar()
        Entry(tab_otp, textvariable=var_otp_email, font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=30, y=45, width=280, height=28)

        generated_otp = [""]

        def send_otp():
            em = var_otp_email.get().strip()
            if not em:
                messagebox.showerror("Error", "Please enter registered email!", parent=win)
                return
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT Username FROM users WHERE Email = ? OR Username = ?", (em, em))
                if not cur.fetchone():
                    messagebox.showerror("Error", "No user found with this email!", parent=win)
                    return

            otp = "".join(random.choices(string.digits, k=6))
            generated_otp[0] = otp
            messagebox.showinfo("OTP Dispatched", f"Verification Code Sent!\n\nYour 6-Digit OTP is: {otp}\n\n(Enter this OTP below to reset your password.)", parent=win)

        Button(tab_otp, text="Send OTP", command=send_otp, font=("Times New Roman", 10, "bold"), bg="#0284c7", fg="white", cursor="hand2", bd=0).place(x=320, y=45, width=110, height=28)

        Label(tab_otp, text="Enter 6-Digit OTP:", font=("Times New Roman", 10, "bold"), bg="white").place(x=30, y=100)
        var_entered_otp = StringVar()
        Entry(tab_otp, textvariable=var_entered_otp, font=("Times New Roman", 11, "bold"), bg="#f8fafc", bd=1).place(x=30, y=125, width=400, height=28)

        Label(tab_otp, text="New Password:", font=("Times New Roman", 10, "bold"), bg="white").place(x=30, y=175)
        var_new_p2 = StringVar()
        Entry(tab_otp, textvariable=var_new_p2, show="*", font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=30, y=200, width=400, height=28)

        def verify_otp_reset():
            if not generated_otp[0] or var_entered_otp.get().strip() != generated_otp[0]:
                messagebox.showerror("Error", "Invalid OTP code entered!", parent=win)
                return
            np = var_new_p2.get().strip()
            if not np:
                messagebox.showerror("Error", "Please enter new password!", parent=win)
                return
            em = var_otp_email.get().strip()
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE users SET Password = ? WHERE Email = ? OR Username = ?", (np, em, em))
                conn.commit()
                messagebox.showinfo("Success", "Password updated successfully! You can now log in.", parent=win)
                win.destroy()

        Button(tab_otp, text="Verify OTP & Reset", command=verify_otp_reset, font=("Times New Roman", 11, "bold"), bg="#16a34a", fg="white", cursor="hand2", bd=0).place(x=140, y=260, width=180, height=35)

    # ================= Registration Window =================
    def open_register_window(self):
        reg_win = Toplevel(self.root)
        reg_win.title("User Registration")
        reg_win.geometry("780x560+370+120")
        reg_win.configure(bg="white")
        reg_win.grab_set()

        Label(reg_win, text="NEW USER REGISTRATION", font=("Times New Roman", 20, "bold"), bg="white", fg="#1e293b").place(x=40, y=20)

        var_r_fname = StringVar()
        var_r_lname = StringVar()
        var_r_role = StringVar(value="Faculty")
        var_r_email = StringVar()
        var_r_contact = StringVar()
        var_r_q = StringVar(value="Your Birth Place")
        var_r_a = StringVar()
        var_r_pwd = StringVar()
        var_r_cpwd = StringVar()

        Label(reg_win, text="First Name", font=("Times New Roman", 10, "bold"), bg="white").place(x=40, y=80)
        Entry(reg_win, textvariable=var_r_fname, font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=40, y=105, width=320, height=28)

        Label(reg_win, text="Last Name", font=("Times New Roman", 10, "bold"), bg="white").place(x=400, y=80)
        Entry(reg_win, textvariable=var_r_lname, font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=400, y=105, width=320, height=28)

        Label(reg_win, text="Role", font=("Times New Roman", 10, "bold"), bg="white").place(x=40, y=145)
        role_cb = ttk.Combobox(reg_win, textvariable=var_r_role, values=["Faculty", "Student", "Admin"], state="readonly")
        role_cb.place(x=40, y=170, width=320, height=28)

        Label(reg_win, text="Contact No", font=("Times New Roman", 10, "bold"), bg="white").place(x=400, y=145)
        Entry(reg_win, textvariable=var_r_contact, font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=400, y=170, width=320, height=28)

        Label(reg_win, text="Email Address", font=("Times New Roman", 10, "bold"), bg="white").place(x=40, y=210)
        Entry(reg_win, textvariable=var_r_email, font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=40, y=235, width=320, height=28)

        Label(reg_win, text="Security Question", font=("Times New Roman", 10, "bold"), bg="white").place(x=400, y=210)
        combo_sec = ttk.Combobox(reg_win, textvariable=var_r_q, values=["Your Birth Place", "Your Pet Name", "Your Primary School"], state="readonly")
        combo_sec.place(x=400, y=235, width=320, height=28)

        Label(reg_win, text="Security Answer", font=("Times New Roman", 10, "bold"), bg="white").place(x=40, y=275)
        Entry(reg_win, textvariable=var_r_a, font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=40, y=300, width=320, height=28)

        Label(reg_win, text="Password", font=("Times New Roman", 10, "bold"), bg="white").place(x=400, y=275)
        Entry(reg_win, textvariable=var_r_pwd, show="*", font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=400, y=300, width=320, height=28)

        Label(reg_win, text="Confirm Password", font=("Times New Roman", 10, "bold"), bg="white").place(x=400, y=340)
        Entry(reg_win, textvariable=var_r_cpwd, show="*", font=("Times New Roman", 10), bg="#f8fafc", bd=1).place(x=400, y=365, width=320, height=28)

        def save_reg():
            fn = var_r_fname.get().strip()
            em = var_r_email.get().strip()
            pwd = var_r_pwd.get().strip()
            cpwd = var_r_cpwd.get().strip()
            if not fn or not em or not pwd:
                messagebox.showerror("Error", "Required fields are missing!", parent=reg_win)
                return
            if pwd != cpwd:
                messagebox.showerror("Error", "Passwords do not match!", parent=reg_win)
                return

            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM users WHERE Username = ? OR Email = ?", (em, em))
                if cur.fetchone()[0] > 0:
                    messagebox.showerror("Error", "Account with this email already exists!", parent=reg_win)
                    return

                cur.execute("""
                INSERT INTO users (Username, Password, Role, Fname, Lname, Contact, Email, Security_Q, Security_A, Created_At)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    em, pwd, var_r_role.get(), fn, var_r_lname.get(), var_r_contact.get(),
                    em, var_r_q.get(), var_r_a.get(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()

            messagebox.showinfo("Success", "Registration successful! You can now login.", parent=reg_win)
            reg_win.destroy()

        Button(reg_win, text="Complete Registration", command=save_reg, font=("Times New Roman", 12, "bold"), bg="#16a34a", fg="white", cursor="hand2", bd=0).place(x=280, y=450, width=220, height=40)

if __name__ == "__main__":
    root = Tk()
    app = LoginWindow(root)
    root.mainloop()