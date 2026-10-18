import os
from tkinter import *
from PIL import Image, ImageTk


class Developer:

    def __init__(self, root):
        self.root = root
        
        # Responsive geometry based on screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.title("Face Recognition System - Attendance Management")

        # Header Title
        title_lbl = Label(
            self.root,
            text="DEVELOPER DETAILS",
            font=("times new roman", 30, "bold"),
            bg="darkblue",
            fg="white",
        )
        title_lbl.place(x=0, y=0, relwidth=1.0, height=55)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_dir = os.path.join(base_dir, "face_recognition")
        img_path = os.path.join(img_dir, "dev.jpg")

        try:
            img_top = Image.open(img_path)
            img_top = img_top.resize((screen_width, screen_height - 55), Image.Resampling.LANCZOS)
            self.photoimg_top = ImageTk.PhotoImage(img_top)

            self.f_lbl_top = Label(self.root, image=self.photoimg_top)
            self.f_lbl_top.place(x=0, y=55, relwidth=1.0, relheight=1.0)
        except Exception:
            # Fallback label in case the image file path is not found
            self.f_lbl_top = Label(
                self.root,
                text="DEVELOPER BACKGROUND\n(Image file not found)",
                bg="lightgrey",
                font=("Times New Roman", 18, "bold"),
            )
            self.f_lbl_top.place(x=0, y=55, relwidth=1.0, relheight=1.0)

        # Main Info Frame (Overlayed on top of the background label)
        main_frame = Frame(self.f_lbl_top, bd=2, bg="white", relief=RIDGE)
        # Position using relative placement so it scales better across monitors
        main_frame.place(relx=0.65, rely=0.08, width=480, height=580)

        # Developer Info Header Inside Frame
        dev_title = Label(
            main_frame,
            text="ABOUT THE DEVELOPER",
            font=("times new roman", 20, "bold"),
            bg="white",
            fg="darkblue",
        )
        dev_title.pack(side=TOP, fill=X, pady=(20, 10))

        # Profile Image inside Frame
        profile_path = os.path.join(img_dir, "sudeep.jpeg")
        try:
            img_prof = Image.open(profile_path)
            img_prof = img_prof.resize((160, 160), Image.Resampling.LANCZOS)
            self.photoimg_prof = ImageTk.PhotoImage(img_prof)

            prof_lbl = Label(main_frame, image=self.photoimg_prof, bg="white")
            prof_lbl.pack(pady=10)
        except Exception:
            prof_lbl = Label(
                main_frame,
                text="[ Profile Photo ]",
                bg="lightgray",
                font=("times new roman", 12),
                width=18,
                height=7,
            )
            prof_lbl.pack(pady=10)

        # Developer Information Details - FIX: Triple quotes for multiline text
        dev_info_text = (
            "Hello, I'm Sudeep!\n\n"
            "Passionate Data Scientist and Data Analyst "
            "transforming data into intelligent solutions through AI, "
            "Machine Learning, and analytics.\n\n"
            "Dedicated to innovation, continuous learning, "
            "and solving real-world problems.\n\n"
            "📧 Contact: sudeepdhami9@gmail.com"
        )

        info_label = Label(
            main_frame,
            text=dev_info_text,
            font=("times new roman", 13),
            bg="white",
            fg="#222222",
            justify=CENTER,
            wraplength=420,  # Prevents text overflow outside frame
        )
        info_label.pack(pady=15, padx=20)


if __name__ == "__main__":
    root = Tk()
    app = Developer(root)
    root.mainloop()