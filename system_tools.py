import os
from datetime import datetime
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from db_manager import db, BACKUP_DIR

class SystemToolsWindow:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1100x700+220+75")
        self.root.title("System Administration & Security Tools")
        self.root.configure(bg="#f8fafc")

        # Header
        header = Frame(self.root, bg="#0f172a", height=65)
        header.place(x=0, y=0, width=1100, height=65)

        Label(
            header,
            text="⚙️ SYSTEM TOOLS: ACTIVITY LOGS, SCHEDULING & BACKUP",
            font=("Times New Roman", 18, "bold"),
            bg="#0f172a",
            fg="#38bdf8"
        ).place(x=20, y=18)

        # Tabs
        tabs = ttk.Notebook(self.root)
        tabs.place(x=20, y=80, width=1060, height=590)

        # ---------------- Tab 1: Activity Logs (Feature 12) ----------------
        tab_logs = Frame(tabs, bg="white")
        tabs.add(tab_logs, text="📜 Activity & Audit Logs")

        log_ctrl = Frame(tab_logs, bg="white")
        log_ctrl.pack(fill=X, padx=15, pady=10)

        Label(log_ctrl, text="Search Logs:", font=("Times New Roman", 11, "bold"), bg="white").pack(side=LEFT, padx=5)
        self.var_log_search = StringVar()
        Entry(log_ctrl, textvariable=self.var_log_search, font=("Times New Roman", 11), bg="#f8fafc", bd=1, width=25).pack(side=LEFT, padx=5)
        Button(log_ctrl, text="Filter", command=self.load_logs, font=("Times New Roman", 10, "bold"), bg="#2563eb", fg="white", cursor="hand2", bd=0, padx=10, pady=2).pack(side=LEFT, padx=5)
        Button(log_ctrl, text="Refresh", command=lambda: (self.var_log_search.set(""), self.load_logs()), font=("Times New Roman", 10, "bold"), bg="#64748b", fg="white", cursor="hand2", bd=0, padx=10, pady=2).pack(side=LEFT, padx=5)

        cols = ("id", "time", "user", "role", "action", "details")
        self.tree_logs = ttk.Treeview(tab_logs, columns=cols, show="headings", height=18)
        self.tree_logs.heading("id", text="Log ID")
        self.tree_logs.heading("time", text="Timestamp")
        self.tree_logs.heading("user", text="User")
        self.tree_logs.heading("role", text="Role")
        self.tree_logs.heading("action", text="Action")
        self.tree_logs.heading("details", text="Details")

        self.tree_logs.column("id", width=60, anchor=CENTER)
        self.tree_logs.column("time", width=150, anchor=CENTER)
        self.tree_logs.column("user", width=120)
        self.tree_logs.column("role", width=100, anchor=CENTER)
        self.tree_logs.column("action", width=160)
        self.tree_logs.column("details", width=420)

        scroll_l = ttk.Scrollbar(tab_logs, orient=VERTICAL, command=self.tree_logs.yview)
        self.tree_logs.configure(yscroll=scroll_l.set)
        scroll_l.pack(side=RIGHT, fill=Y)
        self.tree_logs.pack(fill=BOTH, expand=True, padx=15, pady=(0, 15))

        # ---------------- Tab 2: Attendance Scheduling (Features 18 & 19) ----------------
        tab_sched = Frame(tabs, bg="white")
        tabs.add(tab_sched, text="⏰ Scheduling & Auto-Close")

        sched_box = LabelFrame(tab_sched, text="Active Attendance Time Windows", font=("Times New Roman", 12, "bold"), bg="white", padx=15, pady=15)
        sched_box.pack(fill=X, padx=20, pady=15)

        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM schedules")
            schedules = cur.fetchall()

        for idx, s in enumerate(schedules):
            row_f = Frame(sched_box, bg="white")
            row_f.pack(fill=X, pady=8)
            Label(row_f, text=f"• {s['Title']} ({s['Type']}):", font=("Times New Roman", 11, "bold"), bg="white", width=30, anchor=W).pack(side=LEFT)
            Label(row_f, text=f"Active Hours: {s['Start_Time']} to {s['End_Time']}", font=("Consolas", 11), bg="#f1f5f9", padx=8, pady=2).pack(side=LEFT, padx=10)
            Label(row_f, text=f"Days: {s['Days']}", font=("Times New Roman", 10), bg="white", fg="#64748b").pack(side=LEFT, padx=10)

        # Auto Close Settings
        close_box = LabelFrame(tab_sched, text="Auto Attendance Closing (Feature 19)", font=("Times New Roman", 12, "bold"), bg="white", padx=15, pady=15)
        close_box.pack(fill=X, padx=20, pady=15)

        self.var_auto_close_on = BooleanVar(value=db.get_setting("auto_close_enabled", "0") == "1")
        self.var_close_time = StringVar(value=db.get_setting("auto_close_time", "18:00"))

        Checkbutton(
            close_box,
            text="Enable Auto Attendance Closing",
            variable=self.var_auto_close_on,
            font=("Times New Roman", 11, "bold"),
            bg="white"
        ).pack(anchor=W, pady=5)

        row_c = Frame(close_box, bg="white")
        row_c.pack(fill=X, pady=5)
        Label(row_c, text="Auto Close Daily At (HH:MM):", font=("Times New Roman", 11), bg="white").pack(side=LEFT)
        Entry(row_c, textvariable=self.var_close_time, font=("Consolas", 11), width=10, bg="#f8fafc", bd=1).pack(side=LEFT, padx=10)

        def save_auto_close():
            db.set_setting("auto_close_enabled", "1" if self.var_auto_close_on.get() else "0")
            db.set_setting("auto_close_time", self.var_close_time.get().strip())
            messagebox.showinfo("Saved", "Auto attendance closing configuration saved!", parent=self.root)

        Button(close_box, text="Save Settings", command=save_auto_close, font=("Times New Roman", 10, "bold"), bg="#16a34a", fg="white", cursor="hand2", bd=0, padx=15, pady=4).pack(anchor=W, pady=10)

        # ---------------- Tab 3: Backup & Restore (Feature 21) ----------------
        tab_bak = Frame(tabs, bg="white")
        tabs.add(tab_bak, text="💾 Database Backup & Restore")

        bak_card = Frame(tab_bak, bg="#f8fafc", bd=1, relief=RIDGE)
        bak_card.place(x=30, y=30, width=480, height=350)

        Label(bak_card, text="CREATE DATABASE BACKUP", font=("Times New Roman", 14, "bold"), bg="#f8fafc", fg="#1e293b").pack(pady=(20, 10))
        Label(
            bak_card,
            text="Creates a complete, safe snapshot of student records,\nattendance history, activity logs, and settings.",
            font=("Times New Roman", 11),
            bg="#f8fafc",
            fg="#64748b",
            justify=CENTER
        ).pack(pady=5)

        self.lbl_bak_info = Label(bak_card, text=f"Backup Directory:\n{BACKUP_DIR}", font=("Consolas", 9), bg="#f1f5f9", fg="#334155", padx=10, pady=8)
        self.lbl_bak_info.pack(pady=20)

        def trigger_backup():
            path = db.create_backup()
            messagebox.showinfo("Backup Successful", f"Database successfully backed up!\n\nFile saved to:\n{path}", parent=self.root)
            self.refresh_backups_list()

        Button(bak_card, text="💾 Backup Database Now", command=trigger_backup, font=("Times New Roman", 12, "bold"), bg="#2563eb", fg="white", cursor="hand2", bd=0, padx=20, pady=8).pack(pady=10)

        # Restore Card
        rst_card = Frame(tab_bak, bg="#f8fafc", bd=1, relief=RIDGE)
        rst_card.place(x=540, y=30, width=480, height=350)

        Label(rst_card, text="RESTORE FROM BACKUP", font=("Times New Roman", 14, "bold"), bg="#f8fafc", fg="#dc2626").pack(pady=(20, 10))
        Label(
            rst_card,
            text="Restore database from a previously saved backup file.\nA pre-restore safety copy is automatically generated.",
            font=("Times New Roman", 11),
            bg="#f8fafc",
            fg="#64748b",
            justify=CENTER
        ).pack(pady=5)

        def trigger_restore():
            file = filedialog.askopenfilename(
                title="Select Backup File to Restore",
                initialdir=BACKUP_DIR,
                filetypes=[("SQLite DB Backup", "*.db"), ("All Files", "*.*")],
                parent=self.root
            )
            if not file:
                return

            confirm = messagebox.askyesno(
                "Confirm Restore",
                f"Are you sure you want to restore database from:\n{os.path.basename(file)}?\n\nCurrent data will be replaced by the backup version.",
                parent=self.root
            )
            if confirm:
                ok, msg = db.restore_backup(file)
                if ok:
                    messagebox.showinfo("Restore Success", msg, parent=self.root)
                else:
                    messagebox.showerror("Restore Failed", msg, parent=self.root)

        Button(rst_card, text="🔄 Select & Restore Backup", command=trigger_restore, font=("Times New Roman", 12, "bold"), bg="#dc2626", fg="white", cursor="hand2", bd=0, padx=20, pady=8).pack(pady=40)

        self.load_logs()

    def load_logs(self):
        s = self.var_log_search.get().strip()
        logs = db.get_activity_logs(limit=500, search=s)
        for item in self.tree_logs.get_children():
            self.tree_logs.delete(item)
        for l in logs:
            self.tree_logs.insert("", END, values=(
                l["Log_ID"], l["Timestamp"], l["User"], l["Role"], l["Action"], l["Details"]
            ))

    def refresh_backups_list(self):
        pass

if __name__ == "__main__":
    root = Tk()
    app = SystemToolsWindow(root)
    root.mainloop()
