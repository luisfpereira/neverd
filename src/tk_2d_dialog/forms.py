
from abc import ABCMeta
import tkinter as tk
from tkinter import ttk

import tk_2d_dialog.objects as canvas_objects  # avoid circular import
from tk_2d_dialog.generic_widgets import ScrollableFrame


# TODO: improve defaults of line addition


class _BaseForm(tk.Toplevel, metaclass=ABCMeta):
    # TODO: bring title here

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

    def _config_coords(self, name='coords', label='coords'):
        frame = CoordsFrame(self.holder, label=label)
        return frame, {name: frame}

    def _config_color(self):
        frame = ComboFrame(self.holder, 'color', default='blue',
                           values=['blue', 'red', 'green', 'yellow',
                                   'black', 'white'])
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

    def _config_allow(self, allow_edit=True, allow_translate=True,
                      allow_delete=True):
        container_frame = ttk.Frame(self.holder)
        frame_dict = {}

        if allow_translate:
            translate_frame = BoolFrame(container_frame, 'allow_translate')
            translate_frame.pack(side='left', fill='both', expand=True)
            frame_dict['allow_translate'] = translate_frame

        if allow_edit:
            edit_frame = BoolFrame(container_frame, 'allow edit')
            edit_frame.pack(side='left', fill='both', expand=True)
            frame_dict['allow_edit'] = edit_frame

        if allow_delete:
            delete_frame = BoolFrame(container_frame, 'allow delete')
            delete_frame.pack(side='left', fill='both', expand=True)
            frame_dict['allow_delete'] = delete_frame

        return container_frame, frame_dict

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

    def _config_n_points(self):
        frame = SpinFrame(self.holder, 'number of points', default=2, from_=2)
        return frame, {'n_points': frame}

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
        if obj is None:
            frame_names.insert(1, 'n_points')

        super().__init__(canvas, frame_names, *args, obj=obj,
                         vert_space=vert_space, **kwargs)
        title = 'Add new line' if not self.edit else 'Edit line'
        self.title(title)

        if not self.edit:
            self._config_coords_bindings()
            self._set_default_coords()

    def _get_n_points_frame(self):
        return self.info_container['n_points']

    def _get_coords_frame(self):
        return self.info_container['coords']

    def _set_default_coords(self):
        coords_frame = self._get_coords_frame()
        coords_frame.set([[0., 0.], [1., 1.]])

    def _config_coords_bindings(self):
        n_points_frame = self._get_n_points_frame()
        n_points_frame.tk_var.trace('w', self._update_coords_frame)

    def _update_coords_frame(self, *args):
        n_points_frame = self._get_n_points_frame()
        n_points = n_points_frame.tk_var.get()

        coords_frame = self._get_coords_frame()
        n_frames = len(coords_frame.frames)
        if n_frames < n_points:
            coords_frame.add_entry([0., 0.])
        elif n_frames > n_points:
            coords_frame.remove_last_entry()

    def on_add(self, *args):
        data = self.get()
        del data['n_points']
        line = canvas_objects.Line(**data)
        self.canvas.add_object(line)
        self.destroy()

    def _config_coords(self):
        frame = MultipleCoordsFrame(self.holder)
        return frame, {'coords': frame}


class SliderForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, line_names=None,
                 **kwargs):
        frame_names = ['name', 'lines', 'coords', 'n_points', 'color', 'width',
                       'sizes', 'allow', 'text']
        self.line_names = line_names

        super().__init__(canvas, frame_names, *args, obj=obj,
                         vert_space=vert_space, **kwargs)
        title = 'Add new slider' if not self.edit else 'Edit slider'
        self.title(title)

    def _get_lines(self):
        return self.canvas.get_by_type('Line')

    def _get_line_names(self):
        return [line.name for line in self._get_lines()]

    def _get_available_line_names(self):
        if self.line_names is not None:
            return self.line_names
        else:
            return self._get_line_names()

    def _get_line_from_name(self, line_name):
        line_names = self._get_line_names()
        return self._get_lines()[line_names.index(line_name)]

    def _config_coords(self):
        frame = MultipleCoordsFrame(self.holder, dim=1)

        if not self.edit:
            frame.set([[0.], [1.]])

        return frame, {'v': frame}

    def _config_lines(self):
        if self.edit:
            line_names = [self.object.anchor.name]
        else:
            line_names = self._get_available_line_names()

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


class CalibrationRectangleForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        frame_names = ['canvas_coords', 'coords', 'keep_real', 'color',
                       'width', 'size', 'allow']

        super().__init__(canvas, frame_names, *args, obj=obj,
                         vert_space=vert_space, **kwargs)
        title = 'Add calibration' if not self.edit else 'Edit calibration'
        self.title(title)

        if not self.edit:
            self._set_default_coords()

    def _get_coords_frame(self):
        return self.info_container['coords']

    def _get_canvas_coords_frame(self):
        return self.info_container['canvas_coords']

    def _config_coords(self):
        frame = MultipleCoordsFrame(self.holder)
        return frame, {'coords': frame}

    def _config_canvas_coords(self):
        frame = MultipleCoordsFrame(self.holder, label='canvas coords')
        return frame, {'canvas_coords': frame}

    def _config_keep_real(self):
        frame = BoolFrame(self.holder, label='keep real')
        return frame, {'keep_real': frame}

    def _config_allow(self):
        return super()._config_allow(allow_edit=True, allow_translate=True,
                                     allow_delete=False)

    def _set_default_coords(self):
        coords_frame = self._get_coords_frame()
        coords_frame.set([[-10., 10.], [10., -10.]])

        canvas_coords_frame = self._get_canvas_coords_frame()
        width, height = float(self.canvas['width']), float(self.canvas['height'])
        canvas_coords_frame.set([[20., 20.], [width - 20, height - 20]])

    def on_add(self, *args):
        data = self.get()
        self.canvas.calibrate(**data)
        self.destroy()


class CanvasImageForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        frame_names = ['path', 'upper_left_corner', 'size']  # TODO: add size?
        super().__init__(canvas, frame_names, *args, obj=obj,
                         vert_space=vert_space, **kwargs)

        title = 'Add image' if not self.edit else 'Edit image'
        self.title(title)

    def _config_path(self):
        frame = EntryFrame(self.holder, 'path')
        return frame, {'path': frame}

    def _config_upper_left_corner(self):
        return super()._config_coords(name='upper_left_corner',
                                      label='upper left corner')

    def _config_size(self, allow_edit=True, allow_translate=True,
                     allow_delete=True):
        container_frame = ttk.Frame(self.holder)

        width_frame = EntryFrame(container_frame, 'width', default=300)
        width_frame.pack(side='left', fill='both', expand=True)

        height_frame = EntryFrame(container_frame, 'height', default=300)
        height_frame.pack(side='left', fill='both', expand=True)

        return container_frame, {'width': width_frame,
                                 'height': height_frame}

    def on_add(self, *args):
        data = self.get()

        # TODO: edit after using write entry
        data['size'] = (int(data['width']), int(data['height']))
        del data['width']
        del data['height']

        self.canvas.add_image(**data)
        self.destroy()


class _LabeledFrame(ttk.Frame):

    def __init__(self, holder, label):
        super().__init__(holder)

        if label is not None:
            label = ttk.Label(self, text=label)
            label.pack()

    def get(self):
        return self.tk_var.get()

    def set(self, value):
        return self.tk_var.set(value)


class EntryFrame(_LabeledFrame):
    # TODO: add type
    # TODO: add validation (e.g. non-empty)

    def __init__(self, holder, label, default=''):
        super().__init__(holder, label)

        self.tk_var = tk.StringVar()
        self.tk_var.set(default)

        entry = ttk.Entry(self, textvariable=self.tk_var)
        entry.pack()


class BoolFrame(_LabeledFrame):

    def __init__(self, holder, label, default=True):
        super().__init__(holder, label)

        self.tk_var = tk.BooleanVar()
        self.tk_var.set(default)
        btn = ttk.Checkbutton(self, variable=self.tk_var)
        btn.pack()


class ComboFrame(_LabeledFrame):

    def __init__(self, holder, label, default, values):
        super().__init__(holder, label)

        self.tk_var = tk.StringVar()
        self.tk_var.set(default)

        combo = ttk.Combobox(self, textvariable=self.tk_var,
                             values=values,
                             state='readonly')
        combo.pack()


class SpinFrame(_LabeledFrame):

    def __init__(self, holder, label, default=5, from_=1, to=15):
        super().__init__(holder, label)

        self.tk_var = tk.IntVar()
        self.tk_var.set(default)

        spin = ttk.Spinbox(self, textvariable=self.tk_var,
                           from_=from_, to=to, state='readonly')
        spin.pack()


class CoordsFrame(_LabeledFrame):

    def __init__(self, holder, label='coords', dim=2):
        super().__init__(holder, label)
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

    def __init__(self, holder, label='coords', dim=2, height=100):
        super().__init__(holder, label)
        self.dim = dim
        self.frames = []

        self.scrollable_frame = ScrollableFrame(self, height=height, width=1e6)
        self.scrollable_frame.pack()

    def add_entry(self, coords):
        frame = CoordsFrame(self.scrollable_frame, None, dim=self.dim)
        frame.set(coords)

        frame.pack()

        self.frames.append(frame)

    def remove_last_entry(self):
        self.frames[-1].destroy()
        del self.frames[-1]

    def set(self, values):
        for values_ in values:
            self.add_entry(values_)

    def get(self):
        return [frame.get() for frame in self.frames]


OBJ2FORM = {
    'Point': PointForm,
    'Line': LineForm,
    'Slider': SliderForm,
    'CalibrationRectangle': CalibrationRectangleForm,


}
