import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle

BASE_DIR = r"c:\Users\sudee\OneDrive\Desktop\DATA SCIENCE\data\face recognition"
OUT_DIR = os.path.join(BASE_DIR, "diagrams")
os.makedirs(OUT_DIR, exist_ok=True)

# Set high DPI and aesthetic styles
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

# ==============================================================================
# DIAGRAM 1: END-TO-END SYSTEM ARCHITECTURE WORKFLOW
# ==============================================================================
def generate_diagram_1():
    fig, ax = plt.subplots(figsize=(16, 11), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    # Title Header
    ax.text(8, 10.5, "END-TO-END SYSTEM ARCHITECTURE & WORKFLOW", 
            fontsize=18, fontweight='bold', ha='center', va='center', color='#0f172a')
    ax.text(8, 10.15, "AI Face Recognition & CCTV Automated Attendance System", 
            fontsize=12, style='italic', ha='center', va='center', color='#475569')

    # Helper function for drawing styled boxes
    def draw_box(x, y, w, h, text, subtitle="", title_color='#1e293b', bg_color='#f8fafc', border_color='#cbd5e1', is_cylinder=False):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.15",
                             facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(box)
        if subtitle:
            ax.text(x + w/2, y + h/2 + 0.15, text, fontsize=9.5, fontweight='bold', ha='center', va='center', color=title_color)
            ax.text(x + w/2, y + h/2 - 0.2, subtitle, fontsize=7.5, ha='center', va='center', color='#64748b')
        else:
            ax.text(x + w/2, y + h/2, text, fontsize=9.5, fontweight='bold', ha='center', va='center', color=title_color)

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#334155", lw=1.6, mutation_scale=14))
        if label:
            ax.text((x1 + x2)/2, (y1 + y2)/2 + 0.12, label, fontsize=8, ha='center', va='center', 
                    backgroundcolor='#ffffff', color='#2563eb', fontweight='bold')

    # 1. User Authentication Layer (Top Left)
    draw_box(0.6, 8.6, 3.2, 0.9, "1. USER AUTHENTICATION", "Admin | Faculty | Student", "#1e3a8a", "#eff6ff", "#93c5fd")
    
    # Branching from Auth
    draw_arrow(2.2, 8.6, 2.2, 7.8, "Role Routed")
    
    # 2. Main Executive Dashboard & Student Portal
    draw_box(0.6, 6.8, 3.2, 1.0, "EXECUTIVE DASHBOARD", "KPIs, Schedule & Module Hub", "#0f172a", "#f1f5f9", "#94a3b8")
    draw_box(4.5, 8.6, 2.8, 0.9, "STUDENT PORTAL", "Self-Service & % Alerts", "#065f46", "#ecfdf5", "#6ee7b7")
    draw_arrow(3.8, 9.05, 4.5, 9.05, "Student")

    # Connect to Subsystems
    draw_arrow(2.2, 6.8, 2.2, 5.8)
    draw_arrow(3.8, 7.3, 5.2, 7.3)

    # 3. Student Registration & Dataset Collection Layer
    draw_box(0.6, 4.8, 3.2, 1.0, "STUDENT ENROLLMENT", "Form Input & Data Validation", "#1e3a8a", "#f8fafc", "#bfdbfe")
    draw_arrow(2.2, 4.8, 2.2, 3.8)
    draw_box(0.6, 2.8, 3.2, 1.0, "PHOTO DATASET CAPTURE", "100 Face Crops in data/", "#b45309", "#fffbeb", "#fde68a")
    draw_arrow(2.2, 2.8, 2.2, 1.8)
    draw_box(0.6, 0.8, 3.2, 1.0, "MODEL TRAINING ENGINE", "LBPH -> classifier.xml", "#b91c1c", "#fef2f2", "#fca5a5")

    # Connect Training to Recognition Engine
    draw_arrow(3.8, 1.3, 5.2, 1.3, "Load Model")

    # 4. Input Feed Layer (Middle-Top)
    draw_box(5.2, 6.8, 4.5, 1.0, "MULTI-CAMERA STREAM INGESTION", "Laptop (0) | USB Cam (1) | IP Webcam | RTSP CCTV", "#0f172a", "#f8fafc", "#cbd5e1")
    draw_arrow(7.45, 6.8, 7.45, 5.8, "Live Video Stream")

    # 5. Core AI Computer Vision Pipeline (Center Column)
    box_ai = FancyBboxPatch((5.0, 0.6), 4.9, 5.2, boxstyle="round,pad=0.2,rounding_size=0.2",
                            facecolor='#f8fafc', edgecolor='#64748b', linewidth=1.5, linestyle='--')
    ax.add_patch(box_ai)
    ax.text(7.45, 5.5, "CORE AI VISION PIPELINE", fontsize=11, fontweight='bold', ha='center', color='#1e293b')

    draw_box(5.3, 4.3, 4.3, 0.8, "HAAR CASCADE FACE DETECTION", "Multiscale Sliding Window (haarcascade)", "#0f172a", "#ffffff", "#cbd5e1")
    draw_arrow(7.45, 4.3, 7.45, 3.8)
    draw_box(5.3, 3.0, 4.3, 0.8, "LIVENESS ANTI-SPOOFING", "Blink Frequency & Centroid Micro-Jitter", "#0369a1", "#f0f9ff", "#7dd3fc")
    draw_arrow(7.45, 3.0, 7.45, 2.5)
    draw_box(5.3, 1.7, 4.3, 0.8, "FACE MASK DETECTION", "HSV Lower-Face Skin Ratio (< 32%)", "#047857", "#f0fdf4", "#86efac")
    draw_arrow(7.45, 1.7, 7.45, 1.2)
    draw_box(5.3, 0.4, 4.3, 0.8, "LBPH FACIAL RECOGNITION", "Chi-Square Distance -> Confidence %", "#7c2d12", "#fff7ed", "#fdba74")

    # Decision: Recognized vs Unknown
    draw_arrow(9.6, 0.8, 11.2, 0.8, "Match")
    draw_arrow(9.6, 2.1, 11.2, 2.1, "Unknown")

    # 6. Output & Security Decisions (Right Column)
    draw_box(11.2, 1.6, 4.2, 1.0, "UNKNOWN PERSON ALERT", "Audio Siren, Red HUD & Snapshot Save", "#991b1b", "#fef2f2", "#f87171")
    draw_box(11.2, 0.3, 4.2, 1.0, "AUTO ATTENDANCE RECORDING", "Duplicate Prevention & Timestamping", "#15803d", "#f0fdf4", "#86efac")

    # 7. Database Persistence Layer (Right Middle)
    draw_box(11.2, 3.7, 4.2, 1.5, "CENTRAL DUAL DATABASE", "SQLite (student.db)  <===>  MySQL Workbench\nTables: student, attendance, users, logs", "#1e3a8a", "#eff6ff", "#93c5fd")
    draw_arrow(13.3, 1.3, 13.3, 3.7, "Store Record")
    draw_arrow(13.3, 2.6, 13.3, 3.7, "Log Alert")

    # 8. Analytics & Report Generation Layer (Right Top)
    draw_box(11.2, 6.2, 4.2, 1.3, "ATTENDANCE ANALYTICS & REPORTS", "Matplotlib Charts | PDF Export | Excel .xlsx", "#6d28d9", "#f5f3ff", "#c4b5fd")
    draw_arrow(13.3, 5.2, 13.3, 6.2, "Query Data")

    draw_box(11.2, 8.3, 4.2, 1.0, "NOTIFICATION & ALERTS", "SMTP Email Reports & <75% Low Alerts", "#b45309", "#fffbeb", "#fde68a")
    draw_arrow(13.3, 7.5, 13.3, 8.3, "Trigger")

    plt.tight_layout()
    file_path = os.path.join(OUT_DIR, "diagram_1_end_to_end_architecture.png")
    fig.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Generated: {file_path}")

# ==============================================================================
# DIAGRAM 2: DETAILED MODULE-BY-MODULE WORKFLOW
# ==============================================================================
def generate_diagram_2():
    fig, ax = plt.subplots(figsize=(15, 12), dpi=300)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 12)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    # Title Header
    ax.text(7.5, 11.5, "DETAILED MODULE-BY-MODULE SYSTEM WORKFLOW", 
            fontsize=18, fontweight='bold', ha='center', va='center', color='#0f172a')
    ax.text(7.5, 11.15, "Sequential Execution Flow Across System Lifecycle Stages", 
            fontsize=11.5, style='italic', ha='center', va='center', color='#475569')

    stages = [
        ("STAGE 1: AUTHENTICATION & ACCESS CONTROL", 9.6, "#1e3a8a", "#eff6ff", "#bfdbfe", [
            ("Launch main.py", "Initialize Tkinter & DB"),
            ("Role Selection", "Admin, Faculty, or Student"),
            ("Credentials Check", "Password / OTP Verification"),
            ("Session Routing", "Main Dashboard or Student Portal")
        ]),
        ("STAGE 2: STUDENT REGISTRATION & ENROLLMENT", 7.1, "#065f46", "#ecfdf5", "#a7f3d0", [
            ("Student Details Entry", "ID, Roll, Name, Dept, Year"),
            ("Form Validation", "Verify Unique Student ID"),
            ("Automated Photo Capture", "100 Samples via Haar Cascade"),
            ("Dataset Indexing", "Saved into data/ Directory")
        ]),
        ("STAGE 3: MODEL TRAINING & FEATURE EXTRACTION", 4.6, "#b45309", "#fffbeb", "#fde68a", [
            ("Read Image Samples", "Load grayscale matrices"),
            ("ID Mapping Engine", "Alphanumeric IDs in id_map.json"),
            ("LBPH Feature Extraction", "Calculate 8x8 Spatial Histograms"),
            ("Model Export", "Serialize weights to classifier.xml")
        ]),
        ("STAGE 4: REAL-TIME RECOGNITION & ATTENDANCE PIPELINE", 2.1, "#b91c1c", "#fef2f2", "#fca5a5", [
            ("CCTV / Webcam Ingestion", "RTSP / USB / Laptop 0"),
            ("Liveness & Mask Check", "Blink detection & HSV skin ratio"),
            ("LBPH Face Matching", "Confidence >= 70% threshold"),
            ("Dual DB Recording", "SQLite + MySQL Workbench Mirror")
        ])
    ]

    for stage_title, y_pos, title_c, bg_c, border_c, steps in stages:
        # Stage Banner
        banner = FancyBboxPatch((0.5, y_pos), 14.0, 1.9, boxstyle="round,pad=0.1,rounding_size=0.15",
                                facecolor=bg_c, edgecolor=border_c, linewidth=1.5)
        ax.add_patch(banner)
        ax.text(0.8, y_pos + 1.6, stage_title, fontsize=10.5, fontweight='bold', color=title_c)

        # 4 Sub-steps horizontally
        box_w = 3.0
        gap = 0.35
        start_x = 0.8
        for i, (step_title, step_desc) in enumerate(steps):
            bx = start_x + i * (box_w + gap)
            by = y_pos + 0.25
            s_box = FancyBboxPatch((bx, by), box_w, 1.1, boxstyle="round,pad=0.1,rounding_size=0.1",
                                   facecolor='#ffffff', edgecolor='#cbd5e1', linewidth=1.2)
            ax.add_patch(s_box)
            ax.text(bx + 0.2, by + 0.75, f"Step {i+1}:", fontsize=8, fontweight='bold', color='#64748b')
            ax.text(bx + box_w/2, by + 0.5, step_title, fontsize=8.5, fontweight='bold', ha='center', color='#1e293b')
            ax.text(bx + box_w/2, by + 0.22, step_desc, fontsize=7, ha='center', color='#64748b')

            # Arrow to next step
            if i < 3:
                ax.annotate('', xy=(bx + box_w + gap - 0.05, by + 0.55), xytext=(bx + box_w + 0.05, by + 0.55),
                            arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.3, mutation_scale=10))

    # Downward connection arrows between stages
    ax.annotate('', xy=(7.5, 9.55), xytext=(7.5, 9.6), arrowprops=dict(arrowstyle="-|>", color="#1e3a8a", lw=2, mutation_scale=14))
    ax.annotate('', xy=(7.5, 7.05), xytext=(7.5, 7.1), arrowprops=dict(arrowstyle="-|>", color="#065f46", lw=2, mutation_scale=14))
    ax.annotate('', xy=(7.5, 4.55), xytext=(7.5, 4.6), arrowprops=dict(arrowstyle="-|>", color="#b45309", lw=2, mutation_scale=14))

    # Stage 5: Reporting footer box
    rep_box = FancyBboxPatch((0.5, 0.3), 14.0, 1.2, boxstyle="round,pad=0.1,rounding_size=0.15",
                             facecolor='#f8fafc', edgecolor='#6d28d9', linewidth=1.5)
    ax.add_patch(rep_box)
    ax.text(0.8, 1.15, "STAGE 5: ANALYTICS, EXPORT & AUTOMATED NOTIFICATIONS", fontsize=10.5, fontweight='bold', color='#6d28d9')
    ax.text(7.5, 0.7, "Matplotlib Interactive Analytics (Pie/Bar/Trend)  |  Print-Ready PDF Reports (ReportLab)\nExcel .xlsx Workbooks (openpyxl)  |  Automated Low Attendance (<75%) SMTP Email Dispatch",
            fontsize=8.5, ha='center', color='#334155')

    plt.tight_layout()
    file_path = os.path.join(OUT_DIR, "diagram_2_module_workflow.png")
    fig.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Generated: {file_path}")

# ==============================================================================
# DIAGRAM 3: CCTV / RTSP REAL-TIME RECOGNITION & ATTENDANCE PIPELINE
# ==============================================================================
def generate_diagram_3():
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    # Title Header
    ax.text(8, 9.5, "CCTV / RTSP REAL-TIME RECOGNITION & ATTENDANCE PIPELINE", 
            fontsize=17, fontweight='bold', ha='center', va='center', color='#0f172a')
    ax.text(8, 9.15, "Multi-Camera Streaming, Anti-Spoofing, Mask Verification & Dual Database Synchronization", 
            fontsize=11, style='italic', ha='center', va='center', color='#475569')

    def draw_box(x, y, w, h, text, sub="", color='#1e293b', bg='#ffffff', border='#cbd5e1'):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12,rounding_size=0.12",
                             facecolor=bg, edgecolor=border, linewidth=1.4)
        ax.add_patch(box)
        if sub:
            ax.text(x + w/2, y + h/2 + 0.15, text, fontsize=9, fontweight='bold', ha='center', va='center', color=color)
            ax.text(x + w/2, y + h/2 - 0.2, sub, fontsize=7.2, ha='center', va='center', color='#64748b')
        else:
            ax.text(x + w/2, y + h/2, text, fontsize=9, fontweight='bold', ha='center', va='center', color=color)

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#334155", lw=1.5, mutation_scale=12))
        if label:
            ax.text((x1 + x2)/2, (y1 + y2)/2 + 0.1, label, fontsize=7.5, ha='center', va='center', 
                    backgroundcolor='#ffffff', color='#2563eb', fontweight='bold')

    # 1. Video Ingestion (Far Left)
    draw_box(0.5, 6.8, 3.2, 1.6, "CAMERA SOURCES", "• Built-in Laptop Webcam (0)\n• External USB Camera (1)\n• Android IP Webcam (HTTP)\n• CCTV RTSP Stream (Port 554)", "#0f172a", "#f8fafc", "#94a3b8")
    draw_arrow(3.7, 7.6, 4.5, 7.6, "RTSP / DirectShow")

    # 2. Threaded Buffer-Free Frame Ingestion
    draw_box(4.5, 6.9, 3.0, 1.4, "THREADED STREAM CLIENT", "cctv_engine.py\nBuffer = 1 frame (Zero Lag)\nBackground Daemon Thread", "#0369a1", "#f0f9ff", "#7dd3fc")
    draw_arrow(7.5, 7.6, 8.3, 7.6, "Fresh Frame")

    # 3. Pre-processing & Detection
    draw_box(8.3, 6.9, 3.2, 1.4, "HAAR CASCADE DETECTOR", "Grayscale Conversion\nFrontal Face Classifier\nExtract Bounding Boxes", "#047857", "#f0fdf4", "#86efac")
    draw_arrow(11.5, 7.6, 12.3, 7.6, "Detected Faces")

    # 4. Multi-Face Processing Dispatcher
    draw_box(12.3, 6.9, 3.2, 1.4, "MULTI-FACE DISPATCHER", "Iterates all faces in frame\nSimultaneous verification\nTrack ID centroid tagging", "#6d28d9", "#f5f3ff", "#c4b5fd")
    
    # Downward arrow to verification pipeline
    draw_arrow(13.9, 6.9, 13.9, 5.8)

    # 5. Parallel AI Inspection Box (Middle Row)
    ai_box = FancyBboxPatch((1.5, 3.2), 13.0, 2.4, boxstyle="round,pad=0.15,rounding_size=0.15",
                            facecolor='#f8fafc', edgecolor='#64748b', linewidth=1.5, linestyle='--')
    ax.add_patch(ai_box)
    ax.text(8.0, 5.3, "THREE-STAGE PARALLEL AI INSPECTION PIPELINE", fontsize=11, fontweight='bold', ha='center', color='#1e293b')

    # Stage A: Liveness
    draw_box(2.2, 3.5, 3.6, 1.5, "A. LIVENESS VERIFICATION", "Anti-Spoofing Filter:\n• Eye Blink Variance Dips\n• Centroid Natural Motion\n• Blocks 2D Photos & Phones", "#0369a1", "#ffffff", "#bae6fd")
    
    # Stage B: Mask Check
    draw_box(6.2, 3.5, 3.6, 1.5, "B. FACE MASK DETECTION", "HSV Lower-Face Analysis:\n• Skin Pixel Ratio (< 32%)\n• Allow / Deny / Require Policy\n• Dynamic Badge HUD", "#047857", "#ffffff", "#a7f3d0")

    # Stage C: Recognition
    draw_box(10.2, 3.5, 3.6, 1.5, "C. LBPH RECOGNITION", "Texture Pattern Matching:\n• 8x8 Spatial Histograms\n• Chi-Square Distance Metric\n• Confidence Threshold: 70%", "#b45309", "#ffffff", "#fde68a")

    # Connect from Dispatcher to AI Box
    draw_arrow(13.9, 5.8, 12.0, 5.0)

    # Decision Split below Stage C
    draw_arrow(12.0, 3.5, 12.0, 2.4)
    
    # Decision Diamond
    decision = patches.RegularPolygon((12.0, 1.8), numVertices=4, radius=0.7, 
                                      orientation=0, facecolor='#f1f5f9', edgecolor='#475569', lw=1.5)
    ax.add_patch(decision)
    ax.text(12.0, 1.8, "Conf\n>=70%?", fontsize=8.5, fontweight='bold', ha='center', va='center', color='#0f172a')

    # Path 1: Unknown Person Alert
    draw_arrow(11.3, 1.8, 8.5, 1.8, "No / Unknown")
    draw_box(4.5, 1.1, 4.0, 1.4, "UNKNOWN PERSON ALERT", "• Red Bounding Box on HUD\n• Trigger Audio Warning\n• Save Snapshot to unknown_faces/\n• Record Event in Activity Logs", "#991b1b", "#fef2f2", "#fca5a5")

    # Path 2: Verified Student Attendance
    draw_arrow(12.7, 1.8, 13.5, 1.8, "Yes / Verified")
    draw_box(13.5, 0.4, 2.2, 2.4, "VERIFIED STUDENT\nATTENDANCE", "• Green HUD Box\n• Check Date Duplicate\n• Save Attendance:\n  - SQLite (student.db)\n  - MySQL (Workbench)\n• Update Real-Time KPIs", "#15803d", "#f0fdf4", "#86efac")

    plt.tight_layout()
    file_path = os.path.join(OUT_DIR, "diagram_3_cctv_pipeline.png")
    fig.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Generated: {file_path}")

if __name__ == "__main__":
    generate_diagram_1()
    generate_diagram_2()
    generate_diagram_3()
    print("All 3 professional diagrams generated successfully!")
