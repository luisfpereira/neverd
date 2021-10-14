from abc import ABCMeta
from abc import abstractmethod
import tkinter as tk
from tkinter import ttk

import tk_2d_dialog.objects as canvas_objects  # avoid circular import


class _BaseForm(tk.Toplevel, metaclass=ABCMeta):

    def __init__(self, canvas, frame_names, *args, obj=None,
                 vert_space=10, **kwargs):
        self.canvas = canvas
        self.vert_space = vert_space
        self.object = obj

        super().__init__(*args, **kwargs)
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

        self._config_button(self.edit)
        if self.edit:
            data = self.object.as_dict()
            self.set(data)

    @property
    def edit(self):
        return False if self.object is None else True

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

    def _config_sizes(self):
        container_frame = ttk.Frame(self.holder)

        size_frame = SpinFrame(container_frame, 'size')
        size_frame.pack(side='left', fill='both', expand=True)

        small_size_frame = SpinFrame(container_frame, 'small size')
        small_size_frame.pack(side='left', fill='both', expand=True)

        return container_frame, {'size': size_frame,
                                 'small_size': small_size_frame}

    def _config_width(self):
        frame = SpinFrame(self.holder, 'width', default=1)
        return frame, {'width': frame}

    def _config_allow(self):
        container_frame = ttk.Frame(self.holder)

        translate_frame = BoolFrame(container_frame, 'allow_translate')
        translate_frame.pack(side='left', fill='both', expand=True)

        edit_frame = BoolFrame(container_frame, 'allow edit')
        edit_frame.pack(side='left', fill='both', expand=True)

        delete_frame = BoolFrame(container_frame, 'allow delete')
        delete_frame.pack(side='left', fill='both', expand=True)

        return container_frame, {'allow_translate': translate_frame,
                                 'allow_delete': delete_frame,
                                 'allow_edit': edit_frame}

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

    def get(self):
        return {key: frame.get() for key, frame in self.info_container.items()}

    def set(self, values):
        for key, value in values.items():
            self.info_container[key].set(value)

    def on_edit(self, *args):
        data = self.get()
        self.object.update(**data)
        self.destroy()


class PointForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        frame_names = ['name', 'coords', 'color', 'size', 'allow', 'text']

        super().__init__(canvas, frame_names, *args, obj=obj,
                         vert_space=vert_space, **kwargs)
        title = 'Add new point' if not self.edit else 'Edit point'
        self.title(title)

    def on_add(self, *args):
        data = self.get()
        point = canvas_objects.Point(**data)
        self.canvas.add_object(point)
        self.destroy()


class LineForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        frame_names = ['name', 'coords', 'color', 'width', 'sizes', 'allow',
                       'text']

        super().__init__(canvas, frame_names, *args, obj=obj,
                         vert_space=vert_space, **kwargs)
        title = 'Add new line' if not self.edit else 'Edit line'
        self.title(title)

    def on_add(self, *args):
        data = self.get()
        line = canvas_objects.Line(**data)
        self.canvas.add_object(line)
        self.destroy()

    def _config_coords(self):
        frame = MultipleCoordsFrame(self.holder)
        return frame, {'coords': frame}


class SliderForm(_BaseForm):
    # TODO: transform data? how to deal with v?

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        frame_names = ['name', 'lines', 'coords', 'n_points', 'color', 'width',
                       'sizes', 'allow', 'text']

        super().__init__(canvas, frame_names, *args, obj=obj,
                         vert_space=vert_space, **kwargs)
        title = 'Add new slider' if not self.edit else 'Edit slider'
        self.title(title)

    def _get_lines(self):
        return self.canvas.get_by_type('Line')

    def _get_line_names(self):
        return [line.name for line in self._get_lines()]

    def _get_line_from_name(self, line_name):
        line_names = self._get_line_names()
        return self._get_lines()[line_names.index(line_name)]

    def _config_coords(self):
        # TODO: notice this is fixed size
        frame = MultipleCoordsFrame(self.holder, dim=1)

        if not self.edit:
            frame.set([[0.], [1.]])

        return frame, {'v': frame}

    def _config_n_points(self):
        frame = SpinFrame(self.holder, 'number of points', default=3, from_=2)
        return frame, {'n_points': frame}

    def _config_lines(self):
        if self.edit:
            line_names = [self.object.anchor.name]
        else:
            line_names = self._get_line_names()

        frame = ComboFrame(self.holder, 'anchor name', default=line_names[0],
                           values=line_names)
        return frame, {'anchor': frame}

    def on_add(self, *args):
        data = self.get()
        slider = canvas_objects.Slider(**data)
        self.canvas.add_object(slider)
        self.destroy()

    def get(self):
        data = super().get()

        line = self._get_line_from_name(data['anchor'])
        if self.edit:
            del data['anchor']
        else:
            data['anchor'] = line

        data['v_init'], data['v_end'] = [v[0] for v in data['v']]
        del data['v']

        return data

    def set(self, values):
        del values['coords']

        values['v'] = [[v] for v in [values['v_init'], values['v_end']]]
        del values['v_init']
        del values['v_end']

        super().set(values)


class _LabeledFrame(ttk.Frame):

    def __init__(self, holder, label_text):
        super().__init__(holder)

        if label_text is not None:
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

    def __init__(self, holder, label_text='coords', dim=2):
        super().__init__(holder, label_text)
        self.dim = dim

        self.tk_vars = [tk.DoubleVar() for _ in range(dim)]

        for tk_var in self.tk_vars:
            entry = ttk.Entry(self, textvariable=tk_var)
            side = 'top' if self.dim == 1 else 'left'
            entry.pack(side=side)

    def get(self):
        return [tk_var.get() for tk_var in self.tk_vars]

    def set(self, values):
        for tk_var, value in zip(self.tk_vars, values):
            tk_var.set(value)


class MultipleCoordsFrame(_LabeledFrame):

    def __init__(self, holder, label_text='coords', dim=2):
        super().__init__(holder, label_text)
        # TODO: add scrollbar
        # TODO: how to handle point addition in middle?
        self.dim = dim
        self.frames = []

    def _add_entry(self, coords):
        frame = CoordsFrame(self, None, dim=self.dim)
        frame.pack(fill='both', expand=True)
        frame.set(coords)

        self.frames.append(frame)

    def set(self, values):
        # TODO: assumes fixed size for now
        for values_ in values:
            self._add_entry(values_)

    def get(self):
        return [frame.get() for frame in self.frames]


OBJ2FORM = {
    'Point': PointForm,
    'Line': LineForm,
    'Slider': SliderForm
}
