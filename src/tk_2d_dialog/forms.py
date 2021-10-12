from abc import ABCMeta
from abc import abstractmethod
import tkinter as tk
from tkinter import ttk


class _BaseForm(tk.Toplevel, metaclass=ABCMeta):

    def __init__(self, title, frame_names, *args, vert_space=10, **kwargs):
        self.vert_space = vert_space

        super().__init__(*args, **kwargs)
        self.title(title)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.holder = ttk.Frame(self)
        self.holder.grid(column=0, row=0, sticky="n")

        self.info_container = dict()
        for i, frame_name in enumerate(frame_names):
            vert_space_ = self.vert_space if i else 0.
            frame, dict_info = getattr(self, f'_config_{frame_name}')()
            frame.pack(fill='both', expand=True, pady=vert_space_)
            self.info_container.update(dict_info)

    def _config_name(self):
        frame = EntryFrame(self.holder, 'name')
        return frame, {'name': frame}

    def _config_coords(self):
        frame = CoordsFrame(self.holder)
        return frame, {'coords': frame}

    def _config_color(self):
        frame = ComboFrame(self.holder, 'color', default='blue',
                           values=['blue', 'red', 'green', 'yellow'])
        return frame, {'color': frame}

    def _config_size(self):
        frame = SpinFrame(self.holder, 'size')
        return frame, {'size': frame}

    def _config_allow(self):
        allow_frame = ttk.Frame(self.holder)

        translate_frame = BoolFrame(allow_frame, 'allow_translate')
        translate_frame.pack(side='left', fill='both', expand=True)

        delete_frame = BoolFrame(allow_frame, 'allow delete')
        delete_frame.pack(side='left', fill='both', expand=True)

        return allow_frame, {'allow_translate': translate_frame,
                             'allow_delete': delete_frame}

    def _config_text(self):
        frame = EntryFrame(self.holder, 'text')
        return frame, {'text': frame}

    def _config_button(self, edit):
        if edit:
            btn = ttk.Button(self.holder, command=self.on_edit,
                             text='Edit')
        else:
            btn = ttk.Button(self.holder, command=self.on_add,
                             text='Add')
        btn.pack(pady=self.vert_space)

    @abstractmethod
    def on_add(self, *args):
        pass

    @abstractmethod
    def on_edit(self, *args):
        pass

    def get(self):
        return {key: frame.get() for key, frame in self.info_container.items()}

    def set(self, values):
        for key, value in values.items():
            self.info_container[key].set(value)


class PointForm(_BaseForm):

    def __init__(self, *args, edit=False, vert_space=10, **kwargs):
        title = 'Add new point' if not edit else 'Edit point'
        frame_names = ['name', 'coords', 'color', 'size', 'allow', 'text']

        super().__init__(title, frame_names, *args, vert_space=vert_space, **kwargs)
        self._config_button(edit)

    def on_add(self, *args):
        pass

    def on_edit(self, *args):
        pass


class _LabeledFrame(ttk.Frame):

    def __init__(self, holder, label_text):
        super().__init__(holder)

        label = ttk.Label(self, text=label_text)
        label.pack()

    def get(self):
        return self.tk_var.get()

    def set(self, value):
        return self.tk_var.set(value)


class EntryFrame(_LabeledFrame):

    def __init__(self, holder, label_text, default=''):
        super().__init__(holder, label_text)

        self.tk_var = tk.StringVar()
        self.tk_var.set(default)

        entry = ttk.Entry(self, textvariable=self.tk_var)
        entry.pack()


class BoolFrame(_LabeledFrame):

    def __init__(self, holder, label_text, default=True):
        super().__init__(holder, label_text)

        self.tk_var = tk.BooleanVar()
        self.tk_var.set(default)
        btn = ttk.Checkbutton(self, variable=self.tk_var)
        btn.pack()


class ComboFrame(_LabeledFrame):

    def __init__(self, holder, label_text, default, values):
        super().__init__(holder, label_text)

        self.tk_var = tk.StringVar()
        self.tk_var.set(default)

        combo = ttk.Combobox(self, textvariable=self.tk_var,
                             values=values,
                             state='readonly')
        combo.pack()


class SpinFrame(_LabeledFrame):

    def __init__(self, holder, label_text, default=5, from_=1, to=15):
        super().__init__(holder, label_text)

        self.tk_var = tk.IntVar()
        self.tk_var.set(default)

        spin = ttk.Spinbox(self, textvariable=self.tk_var,
                           from_=from_, to=to, state='readonly')
        spin.pack()


class CoordsFrame(_LabeledFrame):

    def __init__(self, holder, label_text='coords'):
        super().__init__(holder, label_text)

        self.tk_var_x = tk.DoubleVar()
        self.tk_var_y = tk.DoubleVar()

        x_entry = ttk.Entry(self, textvariable=self.tk_var_x)
        y_entry = ttk.Entry(self, textvariable=self.tk_var_y)
        x_entry.pack(side='left')
        y_entry.pack(side='left')

    def get(self):
        return self.tk_var_x, self.tk_var_y

    def set(self, values):
        self.tk_var_x.set(values[0])
        self.tk_var_y.set(values[1])
