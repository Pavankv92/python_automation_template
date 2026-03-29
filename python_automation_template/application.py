import tkinter as tk
from tkinter import ttk

from python_automation_template.views.instrument_view import InstrumentMainPage


class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Application")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.notebook = ttk.Notebook(self)
        self.notebook.enable_traversal()
        self.notebook.grid(row=0, sticky='nsew')

        # all Pages
        self.main_page = InstrumentMainPage()

        self.notebook.add(self.main_page, text="Robot", sticky='nsew')
