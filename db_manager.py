import os
import sqlite3
import csv
import json
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "student.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
UNKNOWN_DIR = os.path.join(BASE_DIR, "unknown_faces")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(UNKNOWN_DIR, exist_ok=True)

class DatabaseManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    def __init__(self):
        self.db_path = DB_FILE
        self.init_database()
        self.migrate_legacy_data()
        self.cleanup_orphaned_records()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        conn.row_factory = sqlite3.Row
        return conn

    def get_mysql_connection(self):
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="2333438",
                database="face_recognizer",
                connect_timeout=3
            )
            return conn
        except Exception:
            return None

    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Student Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS student (
                Dep TEXT,
                Course TEXT,
                Year TEXT,
                Semester TEXT,
                Student_ID TEXT PRIMARY KEY,
                Name TEXT,
                Division TEXT,
                Roll TEXT,
                Gender TEXT,
                DOB TEXT,
                Email TEXT,
                Phone TEXT,
                Address TEXT,
                Teacher TEXT,
                PhotoSample TEXT DEFAULT 'No'
            )
            """)

            # 2. Attendance Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                Attendance_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Student_ID TEXT,
                Roll TEXT,
                Name TEXT,
                Department TEXT,
                Time TEXT,
                Date TEXT,
                Status TEXT,
                Mode TEXT DEFAULT 'Webcam/CCTV'
            )
            """)

            # 3. Users Table (Role-based: Admin, Faculty, Student)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                Username TEXT PRIMARY KEY,
                Password TEXT NOT NULL,
                Role TEXT NOT NULL DEFAULT 'Admin',
                Fname TEXT,
                Lname TEXT,
                Contact TEXT,
                Email TEXT,
                Security_Q TEXT,
                Security_A TEXT,
                Created_At TEXT
            )
            """)

            # 4. Activity Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                Log_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp TEXT,
                User TEXT,
                Role TEXT,
                Action TEXT,
                Details TEXT
            )
            """)

            # 5. Attendance Schedules Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                Schedule_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Title TEXT,
                Type TEXT,
                Start_Time TEXT,
                End_Time TEXT,
                Days TEXT,
                Is_Active INTEGER DEFAULT 1
            )
            """)

            # 6. System Settings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                Key TEXT PRIMARY KEY,
                Value TEXT
            )
            """)

            # 7. Student Notifications Table (For Alerts & Warnings)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                Notification_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Student_ID TEXT,
                Title TEXT,
                Message TEXT,
                Date TEXT,
                Status TEXT DEFAULT 'Unread'
            )
            """)

            # Default Admin User
            cursor.execute("SELECT COUNT(*) FROM users WHERE Username = 'Admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO users (Username, Password, Role, Fname, Lname, Contact, Email, Security_Q, Security_A, Created_At)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "Admin", "12345", "Admin", "System", "Admin", 
                    "9800000000", "admin@attendance.edu", 
                    "Your Birth Place", "AdminCity", 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            # Default Faculty User
            cursor.execute("SELECT COUNT(*) FROM users WHERE Username = 'faculty'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO users (Username, Password, Role, Fname, Lname, Contact, Email, Security_Q, Security_A, Created_At)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "faculty", "12345", "Faculty", "Faculty", "Member", 
                    "9811111111", "faculty@attendance.edu", 
                    "Your Primary School", "Central High", 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            # Default Schedules if none exist
            cursor.execute("SELECT COUNT(*) FROM schedules")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO schedules (Title, Type, Start_Time, End_Time, Days, Is_Active)
                VALUES (?, ?, ?, ?, ?, ?)
                """, ("Morning Lecture Session", "Lecture", "08:00", "13:00", "Mon,Tue,Wed,Thu,Fri,Sat", 1))
                cursor.execute("""
                INSERT INTO schedules (Title, Type, Start_Time, End_Time, Days, Is_Active)
                VALUES (?, ?, ?, ?, ?, ?)
                """, ("Afternoon Lab Session", "Lab", "13:30", "17:30", "Mon,Tue,Wed,Thu,Fri,Sat", 1))

            # Default Settings
            default_settings = {
                "require_liveness": "1",
                "mask_policy": "allow",  # 'allow', 'deny', 'require'
                "low_attendance_threshold": "75",
                "default_cctv_url": "0",
                "auto_close_enabled": "0",
                "auto_close_time": "18:00",
                "email_smtp_server": "smtp.gmail.com",
                "email_smtp_port": "465",
                "email_sender": "",
                "email_password": ""
            }
            for k, v in default_settings.items():
                cursor.execute("INSERT OR IGNORE INTO settings (Key, Value) VALUES (?, ?)", (k, v))

            conn.commit()

    def migrate_legacy_data(self):
        """Migrates existing users.csv and attendance.csv if present into SQLite."""
        try:
            # Migrate users.csv
            users_csv = os.path.join(BASE_DIR, "users.csv")
            if os.path.exists(users_csv):
                with open(users_csv, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if header:
                        with self.get_connection() as conn:
                            cursor = conn.cursor()
                            for row in reader:
                                if len(row) >= 7 and row[0].strip():
                                    fname, lname, contact, email, sec_q, sec_a, pwd = [x.strip() for x in row[:7]]
                                    uname = email if email else fname
                                    cursor.execute("SELECT COUNT(*) FROM users WHERE Username = ? OR Email = ?", (uname, email))
                                    if cursor.fetchone()[0] == 0:
                                        cursor.execute("""
                                        INSERT INTO users (Username, Password, Role, Fname, Lname, Contact, Email, Security_Q, Security_A, Created_At)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (uname, pwd, "Admin", fname, lname, contact, email, sec_q, sec_a, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit()

            # Migrate attendance.csv
            atten_csv = os.path.join(BASE_DIR, "attendance.csv")
            if os.path.exists(atten_csv):
                with open(atten_csv, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if header:
                        with self.get_connection() as conn:
                            cursor = conn.cursor()
                            for row in reader:
                                if len(row) >= 7 and row[0].strip() and row[6].strip() in ["Present", "Absent"]:
                                    s_id, roll, name, dept, time_str, date_str, status = [x.strip() for x in row[:7]]
                                    cursor.execute("""
                                    SELECT COUNT(*) FROM attendance WHERE Student_ID = ? AND Date = ? AND Time = ?
                                    """, (s_id, date_str, time_str))
                                    if cursor.fetchone()[0] == 0:
                                        cursor.execute("""
                                        INSERT INTO attendance (Student_ID, Roll, Name, Department, Time, Date, Status, Mode)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (s_id, roll, name, dept, time_str, date_str, status, "CSV Import"))
                            conn.commit()

            # Make sure students with an account exist in users table as Student role
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Student_ID, Name, Email, DOB FROM student")
                for s in cursor.fetchall():
                    s_id, s_name, s_email, s_dob = s
                    uname = s_id
                    pwd = s_dob if s_dob else "student123"
                    cursor.execute("SELECT COUNT(*) FROM users WHERE Username = ?", (uname,))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                        INSERT INTO users (Username, Password, Role, Fname, Lname, Contact, Email, Security_Q, Security_A, Created_At)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (uname, pwd, "Student", s_name, "", "", s_email or "", "Your Birth Place", s_dob or "Unknown", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
        except Exception as e:
            print(f"[WARN] Data migration notice: {e}")

    # ================= LOGGING =================
    def log_activity(self, user, role, action, details=""):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO activity_logs (Timestamp, User, Role, Action, Details)
                VALUES (?, ?, ?, ?, ?)
                """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, role, action, details))
                conn.commit()
        except Exception as e:
            print(f"[ERROR] Failed to write activity log: {e}")

    def get_activity_logs(self, limit=500, search=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if search:
                cursor.execute("""
                SELECT * FROM activity_logs 
                WHERE User LIKE ? OR Action LIKE ? OR Details LIKE ? 
                ORDER BY Log_ID DESC LIMIT ?
                """, (f"%{search}%", f"%{search}%", f"%{search}%", limit))
            else:
                cursor.execute("SELECT * FROM activity_logs ORDER BY Log_ID DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ================= ATTENDANCE METHODS =================
    def mark_attendance(self, student_id, roll, name, department, status="Present", mode="CCTV/Webcam"):
        today_str = datetime.now().strftime("%d/%m/%Y")
        time_str = datetime.now().strftime("%H:%M:%S")
        s_id_str = str(student_id).strip()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check duplicate attendance for today
            cursor.execute("""
            SELECT Attendance_ID FROM attendance 
            WHERE Student_ID = ? AND Date = ?
            """, (s_id_str, today_str))
            existing = cursor.fetchone()
            if existing:
                return False, f"Attendance already marked for {name} today."

            cursor.execute("""
            INSERT INTO attendance (Student_ID, Roll, Name, Department, Time, Date, Status, Mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (s_id_str, roll, name, department, time_str, today_str, status, mode))
            conn.commit()

        # Mirror to MySQL face_recognizer if available
        try:
            m_conn = self.get_mysql_connection()
            if m_conn:
                m_cur = m_conn.cursor()
                m_cur.execute("""
                INSERT INTO attendance (Student_ID, Roll, Name, Department, Time, Date, Status, Mode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (s_id_str, roll, name, department, time_str, today_str, status, mode))
                m_conn.commit()
                m_conn.close()
        except Exception as me:
            print(f"[WARN] MySQL mirror notice: {me}")

        # Mirror to attendance.csv for legacy file compatibility
        try:
            csv_path = os.path.join(BASE_DIR, "attendance.csv")
            write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(["Student_ID", "Roll", "Name", "Department", "Time", "Date", "Status"])
                writer.writerow([s_id_str, roll, name, department, time_str, today_str, status])
        except Exception as e:
            print(f"[WARN] Failed mirroring to CSV: {e}")

        self.log_activity("System", "AI Engine", "Attendance Marked", f"ID: {s_id_str}, Name: {name}, Status: {status}")
        return True, f"Attendance marked: {name} ({s_id_str})"

    def get_attendance_records(self, student_id=None, date=None, department=None, name=None):
        query = "SELECT * FROM attendance WHERE 1=1"
        params = []
        if student_id:
            query += " AND Student_ID LIKE ?"
            params.append(f"%{student_id}%")
        if date:
            query += " AND Date LIKE ?"
            params.append(f"%{date}%")
        if department and department != "All" and department != "Select Department":
            query += " AND Department LIKE ?"
            params.append(f"%{department}%")
        if name:
            query += " AND Name LIKE ?"
            params.append(f"%{name}%")
        query += " ORDER BY Attendance_ID DESC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_students(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM student ORDER BY Student_ID ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_student_by_id(self, student_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM student WHERE Student_ID = ?", (str(student_id).strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_student(self, s_dict):
        """Adds student to both SQLite and MySQL safely."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO student (
                Dep, Course, Year, Semester, Student_ID, Name, Division, 
                Roll, Gender, DOB, Email, Phone, Address, Teacher, PhotoSample
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                s_dict["Dep"], s_dict["Course"], s_dict["Year"], s_dict["Semester"],
                s_dict["Student_ID"], s_dict["Name"], s_dict["Division"], s_dict["Roll"],
                s_dict["Gender"], s_dict["DOB"], s_dict["Email"], s_dict["Phone"],
                s_dict["Address"], s_dict["Teacher"], s_dict.get("PhotoSample", "No")
            ))
            pwd = s_dict["DOB"] if s_dict.get("DOB") else "student123"
            cursor.execute("SELECT COUNT(*) FROM users WHERE Username = ?", (s_dict["Student_ID"],))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO users (Username, Password, Role, Fname, Lname, Contact, Email, Security_Q, Security_A, Created_At)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (s_dict["Student_ID"], pwd, "Student", s_dict["Name"], "", s_dict.get("Phone", ""), s_dict.get("Email", ""), "Your Birth Place", s_dict.get("DOB", ""), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

        try:
            m_conn = self.get_mysql_connection()
            if m_conn:
                m_cur = m_conn.cursor()
                m_cur.execute("""
                INSERT INTO student 
                (Dep, Course, Year, Semester, Student_ID, Name, Division, Roll, Gender, DOB, Email, Phone, Address, Teacher, PhotoSample)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    s_dict["Dep"], s_dict["Course"], s_dict["Year"], s_dict["Semester"],
                    s_dict["Student_ID"], s_dict["Name"], s_dict["Division"], s_dict["Roll"],
                    s_dict["Gender"], s_dict["DOB"], s_dict["Email"], s_dict["Phone"],
                    s_dict["Address"], s_dict["Teacher"], s_dict.get("PhotoSample", "No")
                ))
                m_conn.commit()
                m_conn.close()
        except Exception as me:
            print(f"[WARN] MySQL add_student mirror: {me}")

        self.log_activity("Admin", "Student", "Add Student", f"ID: {s_dict['Student_ID']}, Name: {s_dict['Name']}")
        return True

    def update_student(self, s_dict):
        """Updates student in both SQLite and MySQL safely without locking issues."""
        sid = str(s_dict["Student_ID"]).strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM student WHERE Student_ID = ?", (sid,))
            if cursor.fetchone()[0] == 0:
                return False, f"Student ID '{sid}' not found in database. Please click a student in the table on the right."

            cursor.execute("""
            UPDATE student SET 
                Dep = ?, Course = ?, Year = ?, Semester = ?, Name = ?, 
                Division = ?, Roll = ?, Gender = ?, DOB = ?, Email = ?, 
                Phone = ?, Address = ?, Teacher = ?, PhotoSample = ?
            WHERE Student_ID = ?
            """, (
                s_dict["Dep"], s_dict["Course"], s_dict["Year"], s_dict["Semester"],
                s_dict["Name"], s_dict["Division"], s_dict["Roll"], s_dict["Gender"],
                s_dict["DOB"], s_dict["Email"], s_dict["Phone"], s_dict["Address"],
                s_dict["Teacher"], s_dict.get("PhotoSample", "No"), sid
            ))
            cursor.execute("UPDATE users SET Fname = ?, Email = ?, Contact = ? WHERE Username = ?", (s_dict["Name"], s_dict.get("Email", ""), s_dict.get("Phone", ""), sid))
            cursor.execute("UPDATE attendance SET Name = ?, Department = ?, Roll = ? WHERE Student_ID = ?", (s_dict["Name"], s_dict["Dep"], s_dict["Roll"], sid))
            conn.commit()

        try:
            m_conn = self.get_mysql_connection()
            if m_conn:
                m_cur = m_conn.cursor()
                m_cur.execute("""
                UPDATE student SET 
                    Dep = %s, Course = %s, Year = %s, Semester = %s, Name = %s, 
                    Division = %s, Roll = %s, Gender = %s, DOB = %s, Email = %s, 
                    Phone = %s, Address = %s, Teacher = %s, PhotoSample = %s
                WHERE Student_ID = %s
                """, (
                    s_dict["Dep"], s_dict["Course"], s_dict["Year"], s_dict["Semester"],
                    s_dict["Name"], s_dict["Division"], s_dict["Roll"], s_dict["Gender"],
                    s_dict["DOB"], s_dict["Email"], s_dict["Phone"], s_dict["Address"],
                    s_dict["Teacher"], s_dict.get("PhotoSample", "No"), sid
                ))
                m_cur.execute("UPDATE attendance SET Name = %s, Department = %s, Roll = %s WHERE Student_ID = %s", (s_dict["Name"], s_dict["Dep"], s_dict["Roll"], sid))
                m_conn.commit()
                m_conn.close()
        except Exception as me:
            print(f"[WARN] MySQL update_student mirror: {me}")

        self.log_activity("Admin", "Student", "Update Student", f"ID: {sid}, Name: {s_dict['Name']}")
        return True, "Record updated successfully across SQLite & MySQL!"

    # ================= STATS & DASHBOARD =================
    def get_dashboard_kpis(self):
        today_str = datetime.now().strftime("%d/%m/%Y")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM student")
            total_students = cursor.fetchone()[0]

            cursor.execute("""
            SELECT COUNT(DISTINCT Student_ID) FROM attendance 
            WHERE Date = ? AND Status = 'Present'
            """, (today_str,))
            present_today = cursor.fetchone()[0]

            absent_today = max(0, total_students - present_today)
            pct = round((present_today / total_students * 100), 1) if total_students > 0 else 0.0

            return {
                "total_students": total_students,
                "present_today": present_today,
                "absent_today": absent_today,
                "attendance_pct": pct,
                "today_date": today_str
            }

    def get_student_stats(self, student_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT Date) FROM attendance")
            total_sessions = cursor.fetchone()[0]

            cursor.execute("""
            SELECT COUNT(*) FROM attendance 
            WHERE Student_ID = ? AND Status = 'Present'
            """, (str(student_id).strip(),))
            present_days = cursor.fetchone()[0]

            cursor.execute("""
            SELECT COUNT(*) FROM attendance 
            WHERE Student_ID = ? AND Status = 'Absent'
            """, (str(student_id).strip(),))
            explicit_absent = cursor.fetchone()[0]

            absent_days = max(explicit_absent, total_sessions - present_days)
            total_days = max(total_sessions, present_days + absent_days)
            pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0.0

            return {
                "total_days": total_days,
                "present_days": present_days,
                "absent_days": absent_days,
                "percentage": pct
            }

    def get_low_attendance_students(self, threshold=75.0):
        students = self.get_all_students()
        low_list = []
        for s in students:
            stats = self.get_student_stats(s["Student_ID"])
            if stats["percentage"] < threshold:
                low_list.append({**s, **stats})
        return low_list

    # ================= NOTIFICATIONS =================
    def add_notification(self, student_id, title, message):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO notifications (Student_ID, Title, Message, Date, Status)
            VALUES (?, ?, ?, ?, 'Unread')
            """, (str(student_id).strip(), title, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

    def get_student_notifications(self, student_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM notifications 
            WHERE Student_ID = ? 
            ORDER BY Notification_ID DESC
            """, (str(student_id).strip(),))
            return [dict(row) for row in cursor.fetchall()]

    # ================= SETTINGS & SCHEDULES =================
    def get_setting(self, key, default=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Value FROM settings WHERE Key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (Key, Value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    def get_active_schedules(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schedules WHERE Is_Active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def is_attendance_allowed_now(self):
        """Checks if current time is within active schedules."""
        schedules = self.get_active_schedules()
        if not schedules:
            return True, "No schedule restrictions active."

        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        current_day = now.strftime("%a")

        for sch in schedules:
            days = [d.strip() for d in sch["Days"].split(",")]
            if current_day in days:
                if sch["Start_Time"] <= current_time_str <= sch["End_Time"]:
                    return True, f"Active: {sch['Title']} ({sch['Start_Time']} - {sch['End_Time']})"

        return False, f"Attendance Closed: Current time ({current_time_str}) is outside lecture/lab hours."

    # ================= BACKUP & RESTORE =================
    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_face_rec_{timestamp}.db"
        dest_path = os.path.join(BACKUP_DIR, backup_filename)
        shutil.copy2(self.db_path, dest_path)
        self.log_activity("Admin", "System", "Database Backup", f"Saved to {backup_filename}")
        return dest_path

    def restore_backup(self, backup_file_path):
        if not os.path.exists(backup_file_path):
            return False, "Selected backup file does not exist."
        # Create pre-restore backup first
        self.create_backup()
        shutil.copy2(backup_file_path, self.db_path)
        self.log_activity("Admin", "System", "Database Restored", f"Restored from {os.path.basename(backup_file_path)}")
    def delete_student_cascade(self, student_id):
        """
        Permanently deletes a student across the entire ecosystem:
        1. Deletes student from SQLite `student` table.
        2. Deletes all attendance records from SQLite `attendance` table.
        3. Deletes user login from SQLite `users` table (Username = student_id).
        4. Deletes notifications from SQLite `notifications` table.
        5. Deletes from MySQL `student`, `attendance`, and `users` tables (if available).
        6. Deletes all face photo samples from `data/` directory (user.<student_id>.*).
        7. Removes student from `id_map.json` (both id_to_int and int_to_id).
        8. Retrains the LBPH model (`classifier.xml`) on remaining images so CCTV stops recognizing them.
        9. Removes student records from `attendance.csv` (if present).
        10. Records an institutional audit log.
        """
        sid = str(student_id).strip()
        summary = {
            "student_id": sid,
            "student_deleted": False,
            "attendance_deleted": 0,
            "photos_deleted": 0,
            "user_deleted": False,
            "notifications_deleted": 0,
            "csv_rows_removed": 0,
            "model_retrained": False
        }

        # 1. SQLite Deletions
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count attendance records to be deleted
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE Student_ID = ?", (sid,))
            att_row = cursor.fetchone()
            summary["attendance_deleted"] = att_row[0] if att_row else 0
            
            # Delete attendance
            cursor.execute("DELETE FROM attendance WHERE Student_ID = ?", (sid,))
            
            # Delete student
            cursor.execute("DELETE FROM student WHERE Student_ID = ?", (sid,))
            summary["student_deleted"] = cursor.rowcount > 0
            
            # Delete user portal login
            cursor.execute("DELETE FROM users WHERE Username = ?", (sid,))
            summary["user_deleted"] = cursor.rowcount > 0
            
            # Delete notifications
            try:
                cursor.execute("DELETE FROM notifications WHERE student_id = ?", (sid,))
                summary["notifications_deleted"] = cursor.rowcount
            except Exception:
                pass
                
            conn.commit()

        # 2. MySQL Deletions (if MySQL is running)
        try:
            m_conn = self.get_mysql_connection()
            if m_conn:
                m_cursor = m_conn.cursor()
                m_cursor.execute("DELETE FROM attendance WHERE Student_ID = %s", (sid,))
                m_cursor.execute("DELETE FROM student WHERE Student_ID = %s", (sid,))
                try:
                    m_cursor.execute("DELETE FROM users WHERE Username = %s", (sid,))
                except Exception:
                    pass
                m_conn.commit()
                m_conn.close()
        except Exception as me:
            print(f"[WARN] MySQL cascade delete error: {me}")

        # 3. Delete Face Image Samples from data/
        data_dir = os.path.join(BASE_DIR, "data")
        if os.path.exists(data_dir):
            for fname in os.listdir(data_dir):
                parts = fname.split('.')
                if len(parts) >= 3 and parts[0] == "user" and parts[1].strip() == sid:
                    try:
                        os.remove(os.path.join(data_dir, fname))
                        summary["photos_deleted"] += 1
                    except Exception as fe:
                        print(f"[WARN] Failed to delete photo {fname}: {fe}")

        # 4. Remove from id_map.json
        id_map_file = os.path.join(BASE_DIR, "id_map.json")
        if os.path.exists(id_map_file):
            try:
                with open(id_map_file, "r", encoding="utf-8") as mf:
                    id_map = json.load(mf)
                
                id_to_int = id_map.get("id_to_int", {})
                int_to_id = id_map.get("int_to_id", {})
                
                if sid in id_to_int:
                    int_label = str(id_to_int[sid])
                    del id_to_int[sid]
                    if int_label in int_to_id:
                        del int_to_id[int_label]
                
                keys_to_del = [k for k, v in int_to_id.items() if v == sid]
                for k in keys_to_del:
                    del int_to_id[k]
                    
                with open(id_map_file, "w", encoding="utf-8") as mf:
                    json.dump({"id_to_int": id_to_int, "int_to_id": int_to_id}, mf, indent=2)
            except Exception as ie:
                print(f"[WARN] Failed to update id_map.json: {ie}")

        # 5. Retrain or reset AI LBPH Model (classifier.xml)
        model_file = os.path.join(BASE_DIR, "classifier.xml")
        try:
            import cv2
            import numpy as np
            from PIL import Image

            valid_files = []
            if os.path.exists(data_dir):
                valid_files = [f for f in os.listdir(data_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

            if valid_files:
                faces = []
                labels = []
                updated_id_to_int = {}
                if os.path.exists(id_map_file):
                    with open(id_map_file, "r", encoding="utf-8") as f:
                        updated_id_to_int = json.load(f).get("id_to_int", {})

                for filename in valid_files:
                    parts = filename.split('.')
                    if len(parts) >= 3 and parts[0] == 'user':
                        other_sid = parts[1].strip()
                        label_num = updated_id_to_int.get(other_sid, int(other_sid) if other_sid.isdigit() else None)
                        if label_num is not None:
                            img_path = os.path.join(data_dir, filename)
                            img = Image.open(img_path).convert('L')
                            faces.append(np.array(img, 'uint8'))
                            labels.append(label_num)

                if faces and labels:
                    clf = cv2.face.LBPHFaceRecognizer_create()
                    clf.train(faces, np.array(labels, dtype=np.int32))
                    clf.write(model_file)
                    summary["model_retrained"] = True
            else:
                if os.path.exists(model_file):
                    os.remove(model_file)
                summary["model_retrained"] = True
        except Exception as te:
            print(f"[WARN] Failed to retrain model after deletion: {te}")

        # 6. Clean attendance.csv if present
        csv_file = os.path.join(BASE_DIR, "attendance.csv")
        if os.path.exists(csv_file):
            try:
                kept_rows = []
                removed = 0
                with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if header:
                        kept_rows.append(header)
                    for row in reader:
                        if row and len(row) > 0 and row[0].strip() == sid:
                            removed += 1
                        elif row:
                            kept_rows.append(row)
                if removed > 0:
                    with open(csv_file, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerows(kept_rows)
                    summary["csv_rows_removed"] = removed
            except Exception as ce:
                print(f"[WARN] Failed to clean attendance.csv: {ce}")

        # 7. Audit log
        self.log_activity(
            "Admin", "Student", "Cascade Delete Student",
            f"Permanently purged Student ID: {sid}. Removed {summary['attendance_deleted']} attendance records, {summary['photos_deleted']} photos. Retrained model: {summary['model_retrained']}."
        )

        return summary

    def cleanup_orphaned_records(self):
        """Removes attendance and mapping records for students that no longer exist in student table."""
        purged = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance WHERE Student_ID NOT IN (SELECT Student_ID FROM student)")
            purged = cursor.rowcount
            conn.commit()

        # MySQL cleanup
        try:
            m_conn = self.get_mysql_connection()
            if m_conn:
                m_cursor = m_conn.cursor()
                m_cursor.execute("DELETE FROM attendance WHERE Student_ID NOT IN (SELECT Student_ID FROM student)")
                m_conn.commit()
                m_conn.close()
        except Exception:
            pass

        # id_map.json cleanup
        id_map_file = os.path.join(BASE_DIR, "id_map.json")
        if os.path.exists(id_map_file):
            try:
                all_sids = set(s["Student_ID"] for s in self.get_all_students())
                with open(id_map_file, "r", encoding="utf-8") as mf:
                    id_map = json.load(mf)
                id_to_int = {k: v for k, v in id_map.get("id_to_int", {}).items() if k in all_sids}
                int_to_id = {k: v for k, v in id_map.get("int_to_id", {}).items() if v in all_sids}
                with open(id_map_file, "w", encoding="utf-8") as mf:
                    json.dump({"id_to_int": id_to_int, "int_to_id": int_to_id}, mf, indent=2)
            except Exception:
                pass

        # Clean attendance.csv
        csv_file = os.path.join(BASE_DIR, "attendance.csv")
        if os.path.exists(csv_file):
            try:
                all_sids = set(s["Student_ID"] for s in self.get_all_students())
                kept_rows = []
                with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if header:
                        kept_rows.append(header)
                    for row in reader:
                        if row and len(row) > 0 and row[0].strip() in all_sids:
                            kept_rows.append(row)
                with open(csv_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(kept_rows)
            except Exception:
                pass

        return purged

db = DatabaseManager.get_instance()
