import csv
import os
from datetime import datetime
from tkinter import *
from tkinter import filedialog, messagebox, ttk
import numpy as np
from PIL import Image, ImageTk


class Help:

    def __init__(self, root):
        self.root = root
        self.root.geometry("1530x790+0+0")
        self.root.title("Face Recognition System - Attendance Management")

        # ================= Header Title =================
        title_lbl = Label(
            self.root,
            text="HELP DESK",
            font=("times new roman", 35, "bold"),
            bg="white",
            fg="blue",
        )
        title_lbl.place(x=0, y=0, width=1530, height=60)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(base_dir, "face_recognition", "help1.jpg")

        try:
            img_top = Image.open(img_path)
            img_top = img_top.resize((1530, 730), Image.Resampling.LANCZOS)
            self.photoimg_top = ImageTk.PhotoImage(img_top)

            self.bg_lbl = Label(self.root, image=self.photoimg_top)
            self.bg_lbl.place(x=0, y=60, width=1530, height=730)
        except Exception:
            self.bg_lbl = Label(
                self.root,
                text="BACKGROUND IMAGE NOT FOUND",
                bg="lightgrey",
                font=("times new roman", 20, "bold"),
            )
            self.bg_lbl.place(x=0, y=60, width=1530, height=730)

        # ================= Email Overlay Label =================
        dev_label = Label(
            self.bg_lbl,
            text="Email:sudeepdhami9@gmail.com",
            font=("times new roman", 20, "bold"),
            bg="white",
            fg="blue",
        )
        # Positioned right in the middle over the laptop display area
        dev_label.place(x=550, y=260)


if __name__ == "__main__":
    root = Tk()
    app = Help(root)
    root.mainloop()