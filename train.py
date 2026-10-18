import os
import json
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from db_manager import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_FILE = os.path.join(BASE_DIR, "classifier.xml")
ID_MAP_FILE = os.path.join(BASE_DIR, "id_map.json")
IMG_DIR = os.path.join(BASE_DIR, "face_recognition")

class Train:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1530x790+0+0")
        self.root.title("Train Data - Face Recognition System")
        self.root.configure(bg="#f4f6f9")

        # ================= Main Title =================
        title_lbl = Label(
            self.root,
            text="AI FACE RECOGNITION MODEL TRAINING",
            font=("Times New Roman", 32, "bold"),
            bg="#1a252f",
            fg="white"
        )
        title_lbl.place(x=0, y=0, width=1530, height=55)

        # Helper for safe image loading
        def load_img(name, size):
            p = os.path.join(IMG_DIR, name)
            if os.path.exists(p):
                im = Image.open(p).resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(im)
            return None

        # ================= Top Banner Image =================
        self.photoimg_top = load_img("face2.jpg", (1530, 310))
        f_lbl_top = Label(self.root, image=self.photoimg_top, bg="#2c3e50")
        f_lbl_top.place(x=0, y=55, width=1530, height=310)

        # ================= Train Dataset Button =================
        self.btn_train = Button(
            self.root,
            text="⚡ START TRAINING MODEL",
            command=self.train_classifier,
            cursor="hand2",
            font=("Times New Roman", 22, "bold"),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            bd=0
        )
        self.btn_train.place(x=365, y=380, width=800, height=55)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient=HORIZONTAL, length=800, mode='determinate')
        self.progress.place(x=365, y=445, width=800, height=20)

        self.status_lbl = Label(self.root, text="Ready to train face dataset", font=("Times New Roman", 13), bg="#f4f6f9", fg="#555")
        self.status_lbl.place(x=365, y=475, width=800, height=25)

        # ================= Bottom Image =================
        self.photoimg_bottom = load_img("face3.jpg", (1530, 260))
        f_lbl_bottom = Label(self.root, image=self.photoimg_bottom, bg="#34495e")
        f_lbl_bottom.place(x=0, y=510, width=1530, height=260)

    # ================= Train Classifier Method =================
    def train_classifier(self):
        if not os.path.exists(DATA_DIR):
            messagebox.showerror(
                "Error",
                "No 'data' folder found in project directory!\nPlease capture student photo samples first.",
                parent=self.root
            )
            return

        valid_files = [
            f for f in os.listdir(DATA_DIR) 
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]

        if not valid_files:
            messagebox.showerror(
                "Error",
                "No face sample images found in 'data/' folder!",
                parent=self.root
            )
            return

        faces = []
        labels = []
        
        # Build ID mapping: map student string IDs (e.g. "CS2025001", "101") to integer labels
        id_to_int = {}
        int_to_id = {}
        next_label = 1

        # Check existing id_map
        if os.path.exists(ID_MAP_FILE):
            try:
                with open(ID_MAP_FILE, "r", encoding="utf-8") as mf:
                    saved_map = json.load(mf)
                    id_to_int = saved_map.get("id_to_int", {})
                    int_to_id = saved_map.get("int_to_id", {})
                    if int_to_id:
                        next_label = max([int(k) for k in int_to_id.keys()]) + 1
            except Exception:
                id_to_int = {}
                int_to_id = {}
                next_label = 1

        self.btn_train.config(state=DISABLED)
        total_files = len(valid_files)
        self.progress["maximum"] = total_files

        for idx, filename in enumerate(valid_files):
            img_path = os.path.join(DATA_DIR, filename)
            parts = filename.split('.')
            
            # Format: user.<StudentID>.<SampleNum>.jpg
            if len(parts) >= 3 and parts[0] == "user":
                student_id_str = parts[1].strip()
                
                # Assign unique integer label
                if student_id_str not in id_to_int:
                    # If it's already purely numeric and not taken, use it
                    if student_id_str.isdigit() and str(student_id_str) not in int_to_id:
                        assigned = int(student_id_str)
                    else:
                        assigned = next_label
                        next_label += 1
                    id_to_int[student_id_str] = assigned
                    int_to_id[str(assigned)] = student_id_str

                label_num = id_to_int[student_id_str]

                try:
                    img = Image.open(img_path).convert('L')
                    image_np = np.array(img, 'uint8')
                    faces.append(image_np)
                    labels.append(label_num)
                except Exception as e:
                    print(f"[WARN] Error reading {filename}: {e}")

            self.progress["value"] = idx + 1
            self.status_lbl.config(text=f"Processing {idx + 1}/{total_files} samples...")
            self.root.update_idletasks()

        if not faces:
            self.btn_train.config(state=NORMAL)
            messagebox.showerror(
                "Error",
                "No valid 'user.<ID>.<Num>.jpg' images could be parsed.",
                parent=self.root
            )
            return

        labels = np.array(labels, dtype=np.int32)

        # Train LBPH Recognizer
        try:
            clf = cv2.face.LBPHFaceRecognizer_create()
        except AttributeError:
            self.btn_train.config(state=NORMAL)
            messagebox.showerror(
                "OpenCV Error",
                "cv2.face module not found. Please install opencv-contrib-python.",
                parent=self.root
            )
            return

        self.status_lbl.config(text="Training classifier model. Please wait...")
        self.root.update_idletasks()

        clf.train(faces, labels)
        clf.write(MODEL_FILE)

        # Save ID map
        with open(ID_MAP_FILE, "w", encoding="utf-8") as mf:
            json.dump({"id_to_int": id_to_int, "int_to_id": int_to_id}, mf, indent=2)

        self.btn_train.config(state=NORMAL)
        self.status_lbl.config(text=f"Done! Trained {len(faces)} samples across {len(id_to_int)} students.")

        db.log_activity("Admin", "AI Engine", "Model Trained", f"{len(faces)} samples, {len(id_to_int)} students")

        messagebox.showinfo(
            "Success",
            f"Training completed successfully!\nTrained {len(faces)} face samples for {len(id_to_int)} unique students into '{os.path.basename(MODEL_FILE)}'.",
            parent=self.root
        )

def train_model_headless():
    """Utility function to retrain without launching GUI."""
    if not os.path.exists(DATA_DIR):
        return False, "Data directory not found."
    valid_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not valid_files:
        return False, "No face samples found."

    faces = []
    labels = []
    id_to_int = {}
    int_to_id = {}
    next_label = 1

    for filename in valid_files:
        parts = filename.split('.')
        if len(parts) >= 3 and parts[0] == "user":
            student_id_str = parts[1].strip()
            if student_id_str not in id_to_int:
                if student_id_str.isdigit() and str(student_id_str) not in int_to_id:
                    assigned = int(student_id_str)
                else:
                    assigned = next_label
                    next_label += 1
                id_to_int[student_id_str] = assigned
                int_to_id[str(assigned)] = student_id_str

            label_num = id_to_int[student_id_str]
            try:
                img = Image.open(os.path.join(DATA_DIR, filename)).convert('L')
                faces.append(np.array(img, 'uint8'))
                labels.append(label_num)
            except Exception:
                pass

    if not faces:
        return False, "No valid faces."

    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, np.array(labels, dtype=np.int32))
    clf.write(MODEL_FILE)
    with open(ID_MAP_FILE, "w", encoding="utf-8") as mf:
        json.dump({"id_to_int": id_to_int, "int_to_id": int_to_id}, mf, indent=2)

    return True, f"Trained {len(faces)} samples."

if __name__ == "__main__":
    root = Tk()
    app = Train(root)
    root.mainloop()