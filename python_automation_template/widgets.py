from tkinter import ttk


class Frame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _add_frame(self, label_text):
        frame = ttk.LabelFrame(self, text=label_text)
        frame.grid(sticky="nsew")
        return frame
