import os
import json
import time
from datetime import datetime
from tkinter import *
from tkinter import messagebox, simpledialog, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

from db_manager import db
from ai_vision import AIVisionEngine
from cctv_engine import ThreadedCamera, normalize_camera_source
from whatsapp_engine import whatsapp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "classifier.xml")
ID_MAP_FILE = os.path.join(BASE_DIR, "id_map.json")
CASCADE_FILE = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
IMG_DIR = os.path.join(BASE_DIR, "face_recognition")

class Face_Recognition:
    def __init__(self, root, auto_start=False):
        self.root = root
        self.auto_start = auto_start
        self.root.geometry("1530x820+0+0")
        self.root.title("CCTV & AI Face Recognition Attendance System")
        self.root.configure(bg="#121824")

        self.vision = AIVisionEngine(CASCADE_FILE)
        self.camera_client = None
        self.is_streaming = False
        self.recognizer = None
        self.int_to_id = {}
        self.id_to_int = {}
        self.students_cache = {}
        self.session_marked = set()
        self.unknown_alert_count = 0
        self.unknown_face_counters = {}  # Persistence counter for unknown faces

        # Feature settings (pulled from DB)
        self.var_liveness = BooleanVar(value=bool(int(db.get_setting("require_liveness", "0"))))
        self.var_unknown_mode = StringVar(value=db.get_setting("unknown_mode", "Show Unknown Face"))
        self.var_primary_face_only = BooleanVar(value=bool(int(db.get_setting("primary_face_only", "0"))))
        initial_min_conf = db.get_setting("min_confidence", "60")
        if not initial_min_conf or int(initial_min_conf) < 50:
            initial_min_conf = "60"
            db.set_setting("min_confidence", "60")
        self.var_min_confidence = StringVar(value=initial_min_conf)
        self.var_mask_policy = StringVar(value=db.get_setting("mask_policy", "allow")) # 'allow', 'deny', 'require'
        self.var_camera_source = StringVar(value=db.get_setting("default_cctv_url", "http://10.241.76.161:8080/video"))
        self.var_whatsapp_notify = BooleanVar(value=bool(int(db.get_setting("auto_whatsapp_notify", "1"))))
        self.var_status_msg = StringVar(value="Ready to start recognition.")

        self.load_ai_model()
        self.load_student_cache()
        self.build_ui()

        if self.auto_start:
            self.root.after(350, lambda: self.start_stream(bypass_schedule=True))

    def load_student_cache(self):
        students = db.get_all_students()
        self.students_cache = {s["Student_ID"]: s for s in students}

    def load_ai_model(self):
        if os.path.exists(MODEL_FILE):
            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(MODEL_FILE)
            except Exception as e:
                print(f"[ERROR] Could not load LBPH classifier: {e}")
                self.recognizer = None

        if os.path.exists(ID_MAP_FILE):
            try:
                with open(ID_MAP_FILE, "r", encoding="utf-8") as f:
                    map_data = json.load(f)
                    self.int_to_id = map_data.get("int_to_id", {})
                    self.id_to_int = map_data.get("id_to_int", {})
            except Exception as e:
                print(f"[WARN] Error reading ID map: {e}")

    def build_ui(self):
        # ================= Header Bar =================
        header = Frame(self.root, bg="#1e293b", height=65)
        header.place(x=0, y=0, width=1530, height=65)

        title = Label(
            header,
            text="🎥 CCTV & AI MULTI-FACE RECOGNITION AUTO ATTENDANCE",
            font=("Times New Roman", 22, "bold"),
            bg="#1e293b",
            fg="#38bdf8"
        )
        title.place(x=20, y=14)

        # Real-time clock in header
        self.lbl_clock = Label(header, font=("Consolas", 14, "bold"), bg="#1e293b", fg="#4ade80")
        self.lbl_clock.place(x=1300, y=18)
        self.update_clock()

        # ================= Main Container =================
        main_content = Frame(self.root, bg="#121824")
        main_content.place(x=10, y=75, width=1510, height=730)

        # ---------------- Left: Live Video Feed Display ----------------
        video_frame = Frame(main_content, bg="#0f172a", bd=2, relief=RIDGE)
        video_frame.place(x=10, y=10, width=950, height=640)

        self.video_display = Label(
            video_frame,
            text="CAMERA FEED OFFLINE\n\nClick 'START CAMERA STREAM' or select a camera preset below.",
            font=("Times New Roman", 18, "bold"),
            bg="#020617",
            fg="#94a3b8"
        )
        self.video_display.place(x=0, y=0, width=946, height=636)

        # Video Controls Bar under display
        ctrl_bar = Frame(main_content, bg="#1e293b", bd=1, relief=GROOVE)
        ctrl_bar.place(x=10, y=660, width=950, height=60)

        Label(ctrl_bar, text="Camera Source:", font=("Times New Roman", 11, "bold"), bg="#1e293b", fg="white").place(x=10, y=16)

        self.source_entry = Entry(ctrl_bar, textvariable=self.var_camera_source, font=("Consolas", 10), bg="#0f172a", fg="#38bdf8", bd=1)
        self.source_entry.place(x=120, y=14, width=310, height=32)

        # Quick preset buttons
        btn_cam0 = Button(ctrl_bar, text="💻 Laptop (0)", command=lambda: self.switch_source("0"), font=("Times New Roman", 9, "bold"), bg="#334155", fg="white", cursor="hand2", bd=0)
        btn_cam0.place(x=440, y=14, width=85, height=32)

        btn_cam1 = Button(ctrl_bar, text="🔌 USB (1)", command=lambda: self.switch_source("1"), font=("Times New Roman", 9, "bold"), bg="#334155", fg="white", cursor="hand2", bd=0)
        btn_cam1.place(x=530, y=14, width=75, height=32)

        btn_ip = Button(ctrl_bar, text="📱 IP Cam", command=self.prompt_ip_webcam, font=("Times New Roman", 9, "bold"), bg="#0284c7", fg="white", cursor="hand2", bd=0)
        btn_ip.place(x=610, y=14, width=75, height=32)

        btn_my_ip = Button(ctrl_bar, text="🎯 10.241.76.161", command=lambda: self.switch_source("http://10.241.76.161:8080/video"), font=("Times New Roman", 9, "bold"), bg="#0369a1", fg="white", cursor="hand2", bd=0)
        btn_my_ip.place(x=690, y=14, width=125, height=32)

        self.btn_toggle_stream = Button(
            ctrl_bar,
            text="▶ START STREAM",
            command=self.toggle_stream,
            font=("Times New Roman", 10, "bold"),
            bg="#16a34a",
            fg="white",
            cursor="hand2",
            bd=0
        )
        self.btn_toggle_stream.place(x=825, y=14, width=115, height=32)

        # ---------------- Right: Settings & Live Attendance Log ----------------
        right_panel = Frame(main_content, bg="#1e293b", bd=2, relief=RIDGE)
        right_panel.place(x=970, y=10, width=530, height=710)

        # Panel Title
        Label(
            right_panel,
            text="AI RECOGNITION & ATTENDANCE LOG",
            font=("Times New Roman", 15, "bold"),
            bg="#1e293b",
            fg="#f8fafc"
        ).pack(fill=X, pady=8)

        # Status Banner
        self.banner_lbl = Label(
            right_panel,
            textvariable=self.var_status_msg,
            font=("Times New Roman", 10, "bold"),
            bg="#0f172a",
            fg="#38bdf8",
            wraplength=500,
            pady=5
        )
        self.banner_lbl.pack(fill=X, padx=15, pady=3)

        # ================= Detection & Unknown Face Controls =================
        settings_box = LabelFrame(right_panel, text="Detection & Unknown Face Management", font=("Times New Roman", 11, "bold"), bg="#1e293b", fg="#94a3b8", padx=10, pady=6)
        settings_box.pack(fill=X, padx=15, pady=4)

        # 1. UNKNOWN FACE ACTION MODE (Complete Management of Unknown Faces)
        unk_frame = Frame(settings_box, bg="#1e293b")
        unk_frame.pack(fill=X, pady=3)
        Label(unk_frame, text="Unknown Face Action:", font=("Times New Roman", 10, "bold"), bg="#1e293b", fg="#fca5a5").pack(side=LEFT)
        unk_combo = ttk.Combobox(
            unk_frame,
            textvariable=self.var_unknown_mode,
            values=["Show Unknown Face", "Alert & Snapshot", "Ignore Unknown"],
            state="readonly",
            width=18
        )
        unk_combo.pack(side=LEFT, padx=8)
        unk_combo.bind("<<ComboboxSelected>>", self.on_unknown_mode_change)

        # 2. Laptop Camera: Single Face Focus Mode
        Checkbutton(
            settings_box,
            text="Focus Main/Nearest Face (Suppress Background Glitches)",
            variable=self.var_primary_face_only,
            command=self.save_primary_face_setting,
            font=("Times New Roman", 10),
            bg="#1e293b",
            fg="#e2e8f0",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="white"
        ).pack(anchor=W, pady=2)

        # 3. Recognition Confidence Threshold
        conf_frame = Frame(settings_box, bg="#1e293b")
        conf_frame.pack(fill=X, pady=3)
        Label(conf_frame, text="Recognition Min Confidence:", font=("Times New Roman", 10), bg="#1e293b", fg="white").pack(side=LEFT)
        conf_combo = ttk.Combobox(conf_frame, textvariable=self.var_min_confidence, values=["50", "55", "60", "65", "70", "75", "80"], state="readonly", width=6)
        conf_combo.pack(side=LEFT, padx=8)
        conf_combo.bind("<<ComboboxSelected>>", lambda e: db.set_setting("min_confidence", self.var_min_confidence.get()))
        Label(conf_frame, text="%(65% recommended - Rejects unknown faces)", font=("Times New Roman", 9, "italic"), bg="#1e293b", fg="#94a3b8").pack(side=LEFT)

        # 4. Liveness Check
        Checkbutton(
            settings_box,
            text="Require Anti-Spoof Liveness (Blink/Motion)",
            variable=self.var_liveness,
            command=self.save_liveness_setting,
            font=("Times New Roman", 10),
            bg="#1e293b",
            fg="white",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="white"
        ).pack(anchor=W, pady=2)

        # 5. Mask Policy
        mask_frame = Frame(settings_box, bg="#1e293b")
        mask_frame.pack(fill=X, pady=2)
        Label(mask_frame, text="Mask Attendance Policy:", font=("Times New Roman", 10), bg="#1e293b", fg="white").pack(side=LEFT)
        mask_combo = ttk.Combobox(mask_frame, textvariable=self.var_mask_policy, values=["allow", "deny", "require"], state="readonly", width=8)
        mask_combo.pack(side=LEFT, padx=8)
        mask_combo.bind("<<ComboboxSelected>>", lambda e: db.set_setting("mask_policy", self.var_mask_policy.get()))

        # 6. Auto WhatsApp Notification Toggle
        Checkbutton(
            settings_box,
            text="💬 Auto WhatsApp Notice on Marked Attendance",
            variable=self.var_whatsapp_notify,
            command=lambda: db.set_setting("auto_whatsapp_notify", "1" if self.var_whatsapp_notify.get() else "0"),
            font=("Times New Roman", 10, "bold"),
            bg="#1e293b",
            fg="#34d399",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="white"
        ).pack(anchor=W, pady=2)

        # Live Recognized Students Feed
        log_box = LabelFrame(right_panel, text="Today's Live Recognized Faces", font=("Times New Roman", 11, "bold"), bg="#1e293b", fg="#94a3b8", padx=5, pady=5)
        log_box.pack(fill=BOTH, expand=True, padx=15, pady=8)

        columns = ("id", "name", "dept", "time", "status")
        self.tree_live = ttk.Treeview(log_box, columns=columns, show="headings", height=13)
        self.tree_live.heading("id", text="Student ID")
        self.tree_live.heading("name", text="Name")
        self.tree_live.heading("dept", text="Department")
        self.tree_live.heading("time", text="Time")
        self.tree_live.heading("status", text="Status")

        self.tree_live.column("id", width=80, anchor=CENTER)
        self.tree_live.column("name", width=120)
        self.tree_live.column("dept", width=110)
        self.tree_live.column("time", width=80, anchor=CENTER)
        self.tree_live.column("status", width=70, anchor=CENTER)

        scrollbar = ttk.Scrollbar(log_box, orient=VERTICAL, command=self.tree_live.yview)
        self.tree_live.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree_live.pack(fill=BOTH, expand=True)

        self.load_today_attendance_history()

    def update_clock(self):
        self.lbl_clock.config(text=datetime.now().strftime("%I:%M:%S %p"))
        self.root.after(1000, self.update_clock)

    def on_unknown_mode_change(self, event=None):
        mode = self.var_unknown_mode.get()
        db.set_setting("unknown_mode", mode)
        if mode == "Ignore Unknown":
            self.var_status_msg.set("Unknown faces will be ignored (Only registered students shown).")
        elif mode == "Alert & Snapshot":
            self.var_status_msg.set("Security alert & snapshot mode enabled for unregistered faces.")
        else:
            self.var_status_msg.set("Unknown faces will be clearly displayed with 'UNKNOWN FACE' banner.")

    def save_primary_face_setting(self):
        db.set_setting("primary_face_only", "1" if self.var_primary_face_only.get() else "0")

    def save_liveness_setting(self):
        db.set_setting("require_liveness", "1" if self.var_liveness.get() else "0")

    def switch_source(self, src):
        norm = normalize_camera_source(src)
        self.var_camera_source.set(norm)
        db.set_setting("default_cctv_url", norm)
        if self.is_streaming:
            self.stop_stream()
        self.start_stream(bypass_schedule=True)

    def prompt_ip_webcam(self):
        url = simpledialog.askstring(
            "Android IP Webcam",
            "Enter IP Webcam streaming URL:\n(e.g., http://172.16.113.232:8080/video)",
            initialvalue="http://172.16.113.232:8080/video",
            parent=self.root
        )
        if url and url.strip():
            self.switch_source(url.strip())

    def prompt_rtsp_dialog(self):
        url = simpledialog.askstring(
            "CCTV RTSP Stream URL",
            "Enter RTSP Stream URL:\n(e.g., rtsp://admin:password@192.168.1.50:554/stream1)",
            initialvalue=self.var_camera_source.get(),
            parent=self.root
        )
        if url and url.strip():
            self.switch_source(url.strip())

    def load_today_attendance_history(self):
        for item in self.tree_live.get_children():
            self.tree_live.delete(item)
        today_records = db.get_attendance_records(date=datetime.now().strftime("%d/%m/%Y"))
        for rec in today_records:
            self.session_marked.add(str(rec["Student_ID"]).strip())
            self.tree_live.insert("", 0, values=(rec["Student_ID"], rec["Name"], rec["Department"], rec["Time"], rec["Status"]))

    def toggle_stream(self):
        if self.is_streaming:
            self.stop_stream()
        else:
            self.start_stream()

    def start_stream(self, bypass_schedule=False):
        # Reload latest AI model, sample photo gallery, and student cache in case new students were just added
        self.load_ai_model()
        self.load_student_cache()
        self.vision.load_sample_gallery()
        self.load_today_attendance_history()

        # 1. Check schedule restrictions
        if not bypass_schedule:
            allowed, msg = db.is_attendance_allowed_now()
            if not allowed:
                proceed = messagebox.askyesno(
                    "Schedule Notice",
                    f"{msg}\n\nDo you wish to bypass schedule and proceed with attendance anyway?",
                    parent=self.root
                )
                if not proceed:
                    return

        # 2. Check classifier model
        if not self.recognizer or not os.path.exists(MODEL_FILE):
            messagebox.showerror(
                "Model Not Trained",
                "Face recognizer model ('classifier.xml') is missing.\nPlease click 'Train Data' first!",
                parent=self.root
            )
            return

        source = normalize_camera_source(self.var_camera_source.get().strip())
        self.var_status_msg.set(f"Connecting to: {source}...")
        self.root.update_idletasks()

        self.camera_client = ThreadedCamera(source)
        if not self.camera_client.is_opened():
            # If an IP/CCTV stream failed (e.g. phone IP camera offline), auto-switch to laptop webcam (0)
            if source != 0:
                if self.auto_start:
                    self.var_status_msg.set(f"CCTV offline. Auto-switched to Laptop Webcam (0)...")
                    self.switch_source("0")
                    return

                fallback = messagebox.askyesno(
                    "CCTV Stream Offline",
                    f"Could not connect to CCTV stream at:\n{source}\n\n"
                    "Would you like to automatically switch to the local Laptop Webcam (0) to mark attendance now?",
                    parent=self.root
                )
                if fallback:
                    self.switch_source("0")
                    return

            messagebox.showerror(
                "Connection Failed",
                f"Could not open camera stream at:\n{source}\n\n"
                "• For IP Webcam: Ensure the app is open on your phone and on the same Wi-Fi network.\n"
                "• For Laptop Webcam: Select '💻 Laptop (0)'.",
                parent=self.root
            )
            self.var_status_msg.set("Camera connection failed.")
            self.camera_client = None
            return

        self.is_streaming = True
        self.btn_toggle_stream.config(text="⏹ STOP STREAM", bg="#dc2626")
        self.var_status_msg.set(f"Live: {source} | Mode: {self.var_unknown_mode.get()}")
        self.process_video_loop()

    def stop_stream(self):
        self.is_streaming = False
        if self.camera_client:
            self.camera_client.release()
            self.camera_client = None
        self.btn_toggle_stream.config(text="▶ START STREAM", bg="#16a34a")
        self.var_status_msg.set("Stream stopped.")
        self.video_display.config(image="", text="CAMERA FEED OFFLINE\n\nClick 'START CAMERA STREAM' to reconnect.")

    def process_video_loop(self):
        if not self.is_streaming or not self.camera_client:
            return

        # Auto attendance closing check if configured
        if db.get_setting("auto_close_enabled", "0") == "1":
            close_time = db.get_setting("auto_close_time", "18:00")
            if datetime.now().strftime("%H:%M") >= close_time:
                self.var_status_msg.set(f"Auto-closing attendance time reached ({close_time}).")
                self.stop_stream()
                messagebox.showinfo("Attendance Closed", f"Attendance closed automatically at {close_time}.", parent=self.root)
                return

        grabbed, frame = self.camera_client.read()
        if grabbed and frame is not None:
            gray, faces = self.vision.detect_faces(frame)

            # Optional: Single prominent face focus (laptop mode)
            if self.var_primary_face_only.get() and len(faces) > 1:
                faces = [faces[0]]

            min_threshold = int(self.var_min_confidence.get())
            unknown_mode = self.var_unknown_mode.get()

            recognized_records = []
            unrecognized_candidates = []

            # ================= PASS 1: RECOGNITION EVALUATION =================
            for (x, y, w, h) in faces:
                face_crop_gray = gray[y:y+h, x:x+w]
                face_crop_bgr = frame[y:y+h, x:x+w]

                # 1. Consistent Centroid Multi-Face Tracking across frames
                track_id, track = self.vision.get_or_create_track((x, y, w, h))

                student_id = None
                distance = 999.0
                confidence = 0
                is_match = False

                if self.recognizer:
                    try:
                        face_prepared = self.vision.prepare_face_for_recognition(face_crop_gray, (450, 450))
                        predicted_label, distance = self.recognizer.predict(face_prepared)
                        candidate_id = self.int_to_id.get(str(predicted_label), str(predicted_label))

                        # Strict validation: candidate must exist in registered students cache
                        if candidate_id in self.students_cache:
                            is_match, confidence = self.vision.evaluate_lbph_prediction(
                                distance, min_threshold=min_threshold, max_distance=68.0
                            )
                            if is_match:
                                # Dual-Analysis: Validate live face against student's registered sample photos in data/
                                sample_ok, sample_score, _ = self.vision.verify_against_sample_photos(
                                    face_crop_gray, candidate_id, lbph_dist=distance, max_distance=68.0
                                )
                                if sample_ok:
                                    student_id = candidate_id
                                    confidence = max(confidence, sample_score)
                                else:
                                    # Rejected impostor / unknown face misclassified by LBPH
                                    student_id = None
                                    is_match = False
                                    confidence = sample_score
                    except Exception:
                        student_id = None
                        is_match = False
                        confidence = 0

                # 2. Record this frame's vote into the temporal stability buffer
                self.vision.record_track_prediction(track_id, student_id, confidence, is_match)

                # 3. Multi-frame temporal consensus (requires at least 2 consistent matching frames)
                confirmed_id, confirmed_conf, is_confirmed = self.vision.get_track_confirmed_identity(
                    track_id, min_matching_frames=2
                )

                if is_confirmed and confirmed_id and confirmed_id in self.students_cache:
                    student = self.students_cache[confirmed_id]
                    recognized_records.append({
                        "box": (x, y, w, h),
                        "student": student,
                        "student_id": confirmed_id,
                        "confidence": confirmed_conf,
                        "crop_gray": face_crop_gray,
                        "crop_bgr": face_crop_bgr,
                        "track_id": track_id
                    })
                else:
                    unrecognized_candidates.append({
                        "box": (x, y, w, h),
                        "crop_gray": face_crop_gray,
                        "crop_bgr": face_crop_bgr,
                        "track_id": track_id,
                        "confidence": confidence,
                        "distance": distance
                    })

            # ================= RENDER RECOGNIZED STUDENTS =================
            recognized_boxes = [r["box"] for r in recognized_records]
            for rec in recognized_records:
                x, y, w, h = rec["box"]
                student = rec["student"]
                student_id = rec["student_id"]
                confidence = rec["confidence"]
                face_crop_gray = rec["crop_gray"]
                face_crop_bgr = rec["crop_bgr"]
                track_id = rec["track_id"]

                # 1. Mask Detection
                has_mask, mask_conf, mask_label = self.vision.detect_mask(face_crop_bgr)

                # 2. Liveness Check (Blink / Motion)
                is_live, live_reason = self.vision.verify_liveness(face_crop_gray, track_id, (x, y, w, h))

                name = student["Name"]
                roll = student["Roll"]
                dept = student["Dep"]
                box_color = (0, 255, 0)  # Green

                # Check Mask Policy
                policy = self.var_mask_policy.get()
                mask_allowed = True
                if policy == "deny" and has_mask:
                    mask_allowed = False
                elif policy == "require" and not has_mask:
                    mask_allowed = False

                # Check Liveness Requirement
                liveness_ok = True
                if self.var_liveness.get() and not is_live:
                    liveness_ok = False

                # Draw Clean HUD
                cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
                cv2.putText(frame, f"{name} ({confidence}%)", (x, y - 28), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {student_id} | {dept}", (x, y - 8), cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1)

                badge = f"{mask_label} | {live_reason}"
                cv2.putText(frame, badge, (x, y + h + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

                # Auto Mark Attendance if policy & liveness pass
                if mask_allowed and liveness_ok:
                    if student_id not in self.session_marked:
                        success, ret_msg = db.mark_attendance(student_id, roll, name, dept, status="Present", mode="CCTV/AI")
                        if success:
                            self.session_marked.add(student_id)
                            cur_time = datetime.now().strftime("%H:%M:%S")
                            self.tree_live.insert("", 0, values=(student_id, name, dept, cur_time, "Present"))
                            self.var_status_msg.set(f"✅ Attendance Marked: {name} ({student_id})")

                            # Automatic WhatsApp Notification to Student's Registered Phone Number
                            if self.var_whatsapp_notify.get():
                                phone = student.get("Phone")
                                if phone and str(phone).strip():
                                    msg = whatsapp.format_attendance_message(name, student_id, dept, cur_time, mode="CCTV/AI")
                                    whatsapp.dispatch_notice_async(phone, msg, student_id, name, title="Attendance Confirmed")
                        else:
                            # If already marked in database earlier today
                            self.session_marked.add(student_id)
                            self.var_status_msg.set(f"✅ Attendance Already Recorded Today: {name} ({student_id})")
                    else:
                        self.var_status_msg.set(f"✅ Attendance Already Recorded Today: {name} ({student_id})")

                    cv2.putText(frame, "ATTENDANCE: PRESENT", (x, y + h + 36), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1)
                else:
                    if not mask_allowed:
                        cv2.putText(frame, "POLICY: MASK VIOLATION", (x, y + h + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
                    elif not liveness_ok:
                        cv2.putText(frame, "VERIFYING LIVENESS...", (x, y + h + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)

            # ================= PASS 2: HANDLE UNRECOGNIZED CANDIDATES =================
            for unrec in unrecognized_candidates:
                x, y, w, h = unrec["box"]
                track_id = unrec["track_id"]

                # CRITICAL OVERLAP FILTER:
                # If this candidate box touches, overlaps, or is near ANY recognized student's box,
                # it is an artifact of the student's face/neck/clothing. DISCARD IT COMPLETELY!
                if any(self.vision.is_overlapping((x, y, w, h), r_box, threshold=0.15) for r_box in recognized_boxes):
                    continue

                # MODE 1: Ignore Unknown (Completely hidden, NO boxes, NO alerts, NO wrong names)
                if unknown_mode == "Ignore Unknown":
                    continue

                # MODE 2: Alert & Snapshot (Security Mode)
                elif unknown_mode == "Alert & Snapshot":
                    track = self.vision.tracks.get(track_id, {})
                    unk_frames = track.get("unknown_persistence", 1)

                    if unk_frames >= 8:
                        box_color = (0, 0, 255)  # Red
                        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
                        cv2.putText(frame, "UNKNOWN PERSON", (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 0, 255), 2)
                        cv2.putText(frame, "Not Registered / No Match", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)

                        saved_path = self.vision.save_unknown_snapshot(unrec["crop_bgr"])
                        if saved_path:
                            self.unknown_alert_count += 1
                            db.log_activity("AI Engine", "Alert", "Unknown Person Detected", f"Snapshot: {os.path.basename(saved_path)}")
                            self.var_status_msg.set(f"⚠️ Alert: Unknown face captured ({os.path.basename(saved_path)})")
                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 165, 255), 1)
                        cv2.putText(frame, "Verifying Face...", (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)

                # MODE 3 / DEFAULT: Show Unknown Face
                else:
                    track = self.vision.tracks.get(track_id, {})
                    unk_frames = track.get("unknown_persistence", 1)
                    if unk_frames >= 2:
                        # Prominent RED box clearly labeled UNKNOWN FACE
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.putText(frame, "UNKNOWN FACE", (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 0, 255), 2)
                        cv2.putText(frame, "Not Registered / No Match", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 165, 255), 1)
                        cv2.putText(frame, "Verifying Face...", (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)

            # Convert frame to PhotoImage and render
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((946, 636), Image.Resampling.BILINEAR)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_display.imgtk = imgtk
            self.video_display.configure(image=imgtk)

        self.root.after(15, self.process_video_loop)

    def on_closing(self):
        self.stop_stream()
        self.root.destroy()

if __name__ == "__main__":
    root = Tk()
    app = Face_Recognition(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()