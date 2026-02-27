from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from queue import Queue
from . import widgets as w


from .utils import SerialInterface, TicketPurpose, TicketHandler
from .models import SettingsModel
from .logging_config import logger


class PageFileds:
    fields = {"com_port": {"type": "str", "value": ""}}


class InstrumentSettings(SettingsModel):
    def __init__(self, fields, file_name):
        super().__init__(fields=fields, file_name=file_name)


class InstrumentMainPage(w.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_queue = Queue()
        self._ticket_handler = TicketHandler(self.message_queue, self)
        self._fields = PageFileds()
        self._settings_file_name = "instruments_settings.json"
        self._settings_model = InstrumentSettings(
            fields=self._fields.fields, file_name=self._settings_file_name
        )
        self._load_settings()
        self._settings_vars = {"com_port": tk.StringVar()}

        # widgets
        self._status_var = tk.StringVar()

        self.bind("<<CheckQueue>>", self._check_queue)

    def _load_settings(self):
        vartypes = {
            "bool": tk.BooleanVar,
            "str": tk.StringVar,
            "int": tk.IntVar,
            "float": tk.DoubleVar,
        }
        for key, data in self._settings_model.fields.items():
            vartype = vartypes.get(data["type"], tk.StringVar)
            if key in self._settings_vars.keys():
                self._settings_vars[key].set(data["value"])

        for var in self._settings_vars.values():
            var.trace_add("write", self._save_settings)

    def _get_errors(self):
        """return all the errors from all the inputs"""
        errors = {}
        for key, var in self._settings_vars.items():
            inp = var.label_widget.input
            error = var.lable_widgets.error
            if hasattr(inp, "trigger_focusout_validation"):
                inp.trigger_focusout_validation()
            if error.get():
                errors[key] = error.get()
        return errors

    def _save_settings(self, *_):
        for key, varaible in self._settings_vars.items():
            try:
                self._settings_model.set(key, varaible.get())
            except tk.TclError:
                pass
        self._settings_model.save()

    def make_read_only(self):
        for child in self._basic_settings_frame.winfo_children():
            if hasattr(child, "input"):
                if isinstance(child.input, ttk.Button):
                    continue

                child.input.state(["readonly"])
                if isinstance(child.input, ttk.Spinbox):
                    child.input.bind("<Button=1>", lambda e: "break")
                    child.input.bind("<MouseWheel>", lambda e: "break")

    def _check_queue(self, event):
        if not self._message_queue.empty():
            ticket = self._message_queue.get()
            if ticket.ticket_type == TicketPurpose.UPDATE_STATUS:
                self._status_var.set((ticket.ticket_value))
            if ticket.ticket_type == TicketPurpose.EXECUTION_COMPLETED:
                self._status_var.set((ticket.ticket_value))
            if ticket.ticket_type == TicketPurpose.ERROR_MESSAGE:
                self._status_var.set((ticket.ticket_value))
            if ticket.ticket_type == TicketPurpose.UPDATE_PROGRESS:
                self._status_var.set((ticket.ticket_value))
