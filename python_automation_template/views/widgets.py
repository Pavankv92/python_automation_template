"""
widgets.py

Portions of this module are derived from:
  Python GUI Programming with Tkinter (2nd Edition)
  Author: Alan D. Moore
  Source: https://github.com/PacktPublishing/Python-GUI-Programming-with-Tkinter-2E

Original code was adapted to this project under project licensing terms.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, cast
from ..constants import FieldTypes as FT


class Frame(ttk.Frame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _add_frame(self, label_text: str) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(self, text=label_text)
        frame.grid(sticky="nsew")
        return frame


##################
# Widget Classes #
##################


class ValidatedMixin:
    """Adds a validation functionality to an input widget"""

    def __init__(self, *args, error_var=None, **kwargs) -> None:
        self.error = error_var or tk.StringVar()
        super().__init__(*args, **kwargs)

        vcmd = self.register(self._validate)  # type: ignore
        invcmd = self.register(self._invalid)  # type: ignore

        style = ttk.Style()
        widget_class = self.winfo_class()
        validated_style = "ValidatedInput." + widget_class
        style.map(  # type: ignore
            validated_style,
            foreground=[("invalid", "white"), ("!invalid", "black")],
            fieldbackground=[("invalid", "darkred"), ("!invalid", "white")],
        )
        self.configure(style=validated_style)

        self.configure(
            validate="all",
            validatecommand=(vcmd, "%P", "%s", "%S", "%V", "%i", "%d"),  # type: ignore
            invalidcommand=(invcmd, "%P", "%s", "%S", "%V", "%i", "%d"),  # type: ignore
        )

    def _toggle_error(self, on=False) -> None:
        self.configure(foreground=("red" if on else "black"))

    def _validate(
        self,
        proposed: str,
        current: str,
        char: str,
        event: str,
        index: str,
        action: str,
    ) -> bool:
        """The validation method.

        Don't override this, override _key_validate, and _focus_validate
        """
        self.error.set("")

        valid = True
        # if the widget is disabled, don't validate
        state = str(self.configure("state")[-1])
        if state == tk.DISABLED:
            return valid

        if event == "focusout":
            valid = self._focusout_validate(event=event)
        elif event == "key":
            valid = self._key_validate(
                proposed=proposed,
                current=current,
                char=char,
                event=event,
                index=index,
                action=action,
            )
        return valid

    def _focusout_validate(self, **kwargs) -> bool:
        return True

    def _key_validate(self, **kwargs) -> bool:
        return True

    def _invalid(
        self,
        proposed: str,
        current: str,
        char: str,
        event: str,
        index: str,
        action: str,
    ) -> None:
        if event == "focusout":
            self._focusout_invalid(event=event)
        elif event == "key":
            self._key_invalid(
                proposed=proposed,
                current=current,
                char=char,
                event=event,
                index=index,
                action=action,
            )

    def _focusout_invalid(self, **kwargs) -> None:
        """Handle invalid data on a focus event"""
        pass

    def _key_invalid(self, **kwargs) -> None:
        """Handle invalid data on a key event.  By default we want to do nothing"""
        pass

    def trigger_focusout_validation(self) -> bool:
        valid = self._validate("", "", "", "focusout", "", "")
        if not valid:
            self._focusout_invalid(event="focusout")
        return valid


class DateEntry(ValidatedMixin, ttk.Entry):

    def _key_validate(self, action: str, index: str, char: str, **kwargs) -> bool:
        valid = True

        if action == "0":  # This is a delete action
            valid = True
        elif index in ("0", "1", "2", "3", "5", "6", "8", "9"):
            valid = char.isdigit()
        elif index in ("4", "7"):
            valid = char == "-"
        else:
            valid = False
        return valid

    def _focusout_validate(self, event) -> bool:
        valid = True
        if not self.get():  # type: ignore
            self.error.set("A value is required")
            valid = False
        try:
            datetime.strptime(self.get(), "%Y-%m-%d")  # type: ignore
        except ValueError:
            self.error.set("Invalid date")
            valid = False
        return valid


class RequiredEntry(ValidatedMixin, ttk.Entry):

    def _focusout_validate(self, event) -> bool:
        valid = True
        if not self.get():  # type: ignore
            valid = False
            self.error.set("A value is required")
        return valid


class ValidatedCombobox(ValidatedMixin, ttk.Combobox):

    def _key_validate(self, proposed: str, action: str, **kwargs) -> bool:
        valid = True
        # if the user tries to delete,
        # just clear the field
        if action == "0":
            self.set("")  # type: ignore
            return True

        # get our values list
        values = self.cget("values")  # type: ignore
        # Do a case-insensitve match against the entered text
        matching = [x for x in values if x.lower().startswith(proposed.lower())]
        if len(matching) == 0:
            valid = False
        elif len(matching) == 1:
            self.set(matching[0])  # type: ignore
            self.icursor(tk.END)  # type: ignore
            valid = False
        return valid

    def _focusout_validate(self, **kwargs) -> bool:
        valid = True
        if not self.get():  # type: ignore
            valid = False
            self.error.set("A value is required")
        return valid


class ValidatedSpinbox(ValidatedMixin, ttk.Spinbox):
    """A Spinbox that only accepts Numbers"""

    def __init__(
        self,
        *args,
        min_var=None,
        max_var=None,
        focus_update_var=None,
        from_="-Infinity",
        to="Infinity",
        **kwargs,
    ) -> None:
        super().__init__(*args, from_=from_, to=to, **kwargs)  # type: ignore
        increment = Decimal(str(kwargs.get("increment", "1.0")))  # type: ignore
        self.precision = increment.normalize().as_tuple().exponent
        # there should always be a variable,
        # or some of our code will fail
        self.variable = kwargs.get("textvariable")
        if not self.variable:
            self.variable = tk.DoubleVar()
            self.configure(textvariable=self.variable)

        if min_var:
            self.min_var = min_var
            self.min_var.trace_add("write", self._set_minimum)  # type: ignore
        if max_var:
            self.max_var = max_var
            self.max_var.trace_add("write", self._set_maximum)  # type: ignore
        self.focus_update_var = focus_update_var
        self.bind("<FocusOut>", self._set_focus_update_var)

    def _set_focus_update_var(self, event) -> None:
        value = self.get()  # type: ignore
        if self.focus_update_var and not self.error.get():
            self.focus_update_var.set(value)

    def _set_minimum(self, *_) -> None:
        current = self.get()  # type: ignore
        try:
            new_min = self.min_var.get()
            self.config(from_=new_min)  # type: ignore
        except (tk.TclError, ValueError):
            pass
        if not current:
            self.delete(0, tk.END)  # type: ignore
        else:
            self.variable.set(current)
        self.trigger_focusout_validation()

    def _set_maximum(self, *_) -> None:
        current = self.get()  # type: ignore
        try:
            new_max = self.max_var.get()
            self.config(to=new_max)  # type: ignore
        except (tk.TclError, ValueError):
            pass
        if not current:
            self.delete(0, tk.END)  # type: ignore
        else:
            self.variable.set(current)
        self.trigger_focusout_validation()

    def _key_validate(
        self, char: str, index: str, current: str, proposed: str, action: str, **kwargs
    ) -> bool:
        if action == "0":
            return True
        valid = True
        min_val = self.cget("from")  # type: ignore
        max_val = self.cget("to")  # type: ignore
        no_negative = min_val >= 0
        no_decimal = self.precision >= 0

        # First, filter out obviously invalid keystrokes
        if any(
            [
                (char not in "-1234567890."),
                (char == "-" and (no_negative or index != "0")),
                (char == "." and (no_decimal or "." in current)),
            ]
        ):
            return False

        # At this point, proposed is either '-', '.', '-.',
        # or a valid Decimal string
        if proposed in "-.":
            return True

        # Proposed is a valid Decimal string
        # convert to Decimal and check more:
        proposed = Decimal(proposed)  # type: ignore
        proposed_precision = proposed.as_tuple().exponent

        if any([(proposed > max_val), (proposed_precision < self.precision)]):  # type: ignore
            return False

        return valid

    def _focusout_validate(self, **kwargs) -> bool:
        valid = True
        value = self.get()  # type: ignore
        min_val = self.cget("from")  # type: ignore
        max_val = self.cget("to")  # type: ignore

        try:
            d_value = Decimal(value)  # type: ignore
        except InvalidOperation:
            self.error.set(f"Invalid number string: {value}")
            return False

        if d_value < min_val:  # type: ignore
            self.error.set(f"Value is too low (min {min_val})")
            valid = False
        if d_value > max_val:  # type: ignore
            self.error.set(f"Value is too high (max {max_val})")
            valid = False

        return valid


class ValidatedRadioGroup(ttk.Frame):
    """A validated radio button group"""

    def __init__(
        self,
        *args,
        variable=None,
        error_var=None,
        values=None,
        button_args=None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.variable = variable or tk.StringVar()
        self.error = error_var or tk.StringVar()
        self.values = values or list()
        button_args = button_args or dict()

        for v in self.values:
            button = ttk.Radiobutton(
                self, value=v, text=v, variable=self.variable, **button_args
            )
            button.pack(side=tk.LEFT, ipadx=10, ipady=2, expand=True, fill="x")  # type: ignore
        self.bind("<FocusOut>", self.trigger_focusout_validation)

    def trigger_focusout_validation(self, *_) -> None:
        self.error.set("")
        if not self.variable.get():  # type: ignore
            self.error.set("A value is required")


class BoundText(tk.Text):
    """A Text widget with a bound variable."""

    def __init__(self, *args, textvariable=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._variable = textvariable
        if self._variable:
            # insert any default value
            self.insert("1.0", self._variable.get())  # type: ignore
            self._variable.trace_add("write", self._set_content)  # type: ignore
            self.bind("<<Modified>>", self._set_var)

    def _set_var(self, *_) -> None:
        """Set the variable to the text contents"""
        if self.edit_modified():
            content = self.get("1.0", "end-1chars")  # type: ignore
            self._variable.set(content)
            self.edit_modified(False)

    def _set_content(self, *_) -> None:
        """Set the text contents to the variable"""
        self.delete("1.0", tk.END)  # type: ignore
        self.insert("1.0", self._variable.get())  # type: ignore


###########################
# Compound Widget Classes #
###########################


class LabelInput(ttk.Frame):
    """A widget containing a label and input together."""

    field_types = {
        FT.string: RequiredEntry,
        FT.string_list: ValidatedCombobox,
        FT.short_string_list: ValidatedRadioGroup,
        FT.iso_date_string: DateEntry,
        FT.long_string: BoundText,
        FT.decimal: ValidatedSpinbox,
        FT.integer: ValidatedSpinbox,
        FT.boolean: ttk.Checkbutton,
    }  # type: ignore

    def __init__(
        self,
        parent,
        label_text: str,
        var,
        input_class=None,
        input_args=None,
        label_args=None,
        field_spec=None,
        disable_var=None,
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        input_args = input_args or {}
        label_args = label_args or {}
        self.variable = var
        self.variable.label_widget = self  # type: ignore

        # Process the field spec to determine input_class and validation
        if field_spec:
            field_type = field_spec.get("type", FT.string)
            input_class = input_class or self.field_types.get(field_type)
            # min, max, increment
            if "min" in field_spec and "from_" not in input_args:
                input_args["from_"] = field_spec.get("min")
            if "max" in field_spec and "to" not in input_args:
                input_args["to"] = field_spec.get("max")
            if "inc" in field_spec and "increment" not in input_args:
                input_args["increment"] = field_spec.get("inc")
                # values
            if "values" in field_spec and "values" not in input_args:
                input_args["values"] = field_spec.get("values")

        # setup the label
        if input_class in (ttk.Checkbutton, ttk.Button):  # type: ignore
            # Buttons don't need labels, they're built-in
            input_args["text"] = label_text
        else:
            self.label = ttk.Label(self, text=label_text, **label_args)
            self.label.grid(row=0, column=0, sticky=(tk.W + tk.E))  # type: ignore

        # setup the variable
        if input_class in (
            ttk.Checkbutton,
            ttk.Button,
            ttk.Radiobutton,
            ValidatedRadioGroup,
        ):  # type: ignore
            input_args["variable"] = self.variable
        else:
            input_args["textvariable"] = self.variable

        # Setup the input
        if input_class == ttk.Radiobutton:  # type: ignore
            # for Radiobutton, create one input per value
            self.input = tk.Frame(self)
            for v in input_args.pop("values", []):
                button = input_class(self.input, value=v, text=v, **input_args)
                button.pack(side=tk.LEFT, ipadx=10, ipady=2, expand=True, fill="x")  # type: ignore
            self.input.error = getattr(button, "error", None)  # type: ignore
            self.input.trigger_focusout_validation = button._focusout_validate  # type: ignore
        else:
            self.input = input_class(self, **input_args)

        self.input.grid(row=1, column=0, sticky=(tk.W + tk.E))  # type: ignore
        self.columnconfigure(0, weight=1)  # type: ignore

        # Set up error handling & display
        error_style = "Error." + label_args.get("style", "TLabel")
        ttk.Style().configure(error_style, foreground="darkred")  # type: ignore
        self.error = getattr(self.input, "error", tk.StringVar())  # type: ignore
        ttk.Label(self, textvariable=self.error, style=error_style).grid(  # type: ignore
            row=2, column=0, sticky=(tk.W + tk.E)
        )

        # Set up disable variable
        if disable_var:
            self.disable_var = disable_var
            self.disable_var.trace_add("write", self._check_disable)  # type: ignore

    def _check_disable(self, *_) -> None:
        if not hasattr(self, "disable_var"):
            return

        if self.disable_var.get():
            self.input.configure(state=tk.DISABLED)
            self.variable.set("")
            self.error.set("")
        else:
            self.input.configure(state=tk.NORMAL)

    def grid(self, sticky=(tk.E + tk.W), **kwargs) -> None:
        """Override grid to add default sticky values"""
        super().grid(sticky=sticky, **kwargs)
