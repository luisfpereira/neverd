
import os
from abc import ABCMeta
from abc import abstractmethod
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

import numpy as np
from PIL import Image
from PIL import ImageTk

import tk_2d_dialog.objects as canvas_objects  # avoid circular import
from tk_2d_dialog.generic_widgets import ScrollableFrame
from tk_2d_dialog.utils import get_image_path


IMG_FORMATS = ['.gif', '.jpg', '.jpeg', '.png']


class _BaseForm(tk.Toplevel, metaclass=ABCMeta):

    def __init__(self, canvas, frame_names, *args, obj=None, title=None,
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

        if title:
            self.title(title)

    @property
    def edit(self):
        return False if self.object is None else True

    def _config_name(self):
        forbidden_values = self.canvas.get_names()
        if self.edit:
            forbidden_values.remove(self.object.name)

        frame = StringEntryFrame(self.holder, 'name', allow_empty=False,
                                 forbidden_values=forbidden_values)
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

        size_frame = SpinFrame(container_frame, 'size', default=5)
        size_frame.pack(side='left', fill='both', expand=True)

        small_size_frame = SpinFrame(container_frame, 'small size', default=3)
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
        frame = StringEntryFrame(self.holder, 'text')
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

    def _post_process_get_data(self, data):
        return data

    def _preprocess_set_data(self, values):
        return values

    def _add_object(self, data):
        point = canvas_objects.TYPE2OBJ[self.obj_type](**data)
        self.canvas.add_object(point)

    def _get_invalid_frames(self):
        """Returns invalid frames.
        """
        return [label_frame for label_frame in self.info_container.values() if not label_frame.validate()]

    def _validate(self):
        invalid_frames = self._get_invalid_frames()
        if len(invalid_frames) == 0:
            return True

        # create message box
        invalid_names = [frame.name for frame in invalid_frames]
        message = f'The following fields are invalid:\n{", ".join(invalid_names)}'
        messagebox.showwarning(message=message)

        return False

    def get(self):
        data = {key: frame.get() for key, frame in self.info_container.items()}
        return self._post_process_get_data(data)

    def set(self, values):
        values = self._preprocess_set_data(values)
        for key, value in values.items():
            self.info_container[key].set(value)

    def on_add(self):
        if not self._validate():
            return

        data = self.get()
        self._add_object(data)
        self.destroy()

    def on_edit(self, *args):
        if not self._validate():
            return

        data = self.get()
        self.object.update(**data)
        self.destroy()


class PointForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        self.obj_type = 'Point'
        frame_names = ['name', 'coords', 'color', 'size', 'allow', 'text']

        title = 'Add new point' if obj is None else 'Edit point'
        super().__init__(canvas, frame_names, *args, obj=obj, title=title,
                         vert_space=vert_space, **kwargs)


class LineForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        self.obj_type = 'Line'
        frame_names = ['name', 'coords', 'color', 'width', 'sizes', 'allow',
                       'text']
        if obj is None:
            frame_names.insert(1, 'n_points')

        title = 'Add new line' if obj is None else 'Edit line'
        super().__init__(canvas, frame_names, *args, obj=obj, title=title,
                         vert_space=vert_space, **kwargs)

        if not self.edit:
            self._config_coords_bindings()
            self._set_default_coords()

    def _config_coords_bindings(self):
        n_points_frame = self._get_n_points_frame()
        n_points_frame.tk_var.trace('w', self._update_coords_frame)

    def _get_n_points_frame(self):
        return self.info_container['n_points']

    def _get_coords_frame(self):
        return self.info_container['coords']

    def _set_default_coords(self):
        coords_frame = self._get_coords_frame()
        coords_frame.set([[0., 0.], [0., 0.]])

    def _update_coords_frame(self, *args):
        n_points_frame = self._get_n_points_frame()
        n_points = n_points_frame.tk_var.get()

        coords_frame = self._get_coords_frame()
        n_frames = len(coords_frame.frames)
        if n_frames < n_points:
            coords_frame.add_entry([0., 0.])
        elif n_frames > n_points:
            coords_frame.remove_last_entry()

    def _post_process_get_data(self, data):
        if not self.edit:
            del data['n_points']

        return data

    def _config_coords(self):
        frame = MultipleCoordsFrame(self.holder)
        return frame, {'coords': frame}


class SliderForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, line_names=None,
                 **kwargs):
        self.obj_type = 'Slider'
        frame_names = ['name', 'lines', 'coords', 'n_points', 'color', 'width',
                       'sizes', 'allow', 'text']
        self.line_names = line_names

        title = 'Add new slider' if obj is None else 'Edit slider'
        super().__init__(canvas, frame_names, *args, obj=obj, title=title,
                         vert_space=vert_space, **kwargs)

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

    def _get_lines(self):
        return self.canvas.get_by_type('Line')

    def _get_line_names(self):
        return self.canvas.get_names('Line')

    def _get_available_line_names(self):
        if self.line_names is not None:
            return self.line_names
        else:
            return self._get_line_names()

    def _get_line_from_name(self, line_name):
        line_names = self._get_line_names()
        return self._get_lines()[line_names.index(line_name)]

    def _post_process_get_data(self, data):
        line = self._get_line_from_name(data['anchor'])
        if self.edit:
            del data['anchor']
        else:
            data['anchor'] = line

        data['v_init'], data['v_end'] = [v[0] for v in data['v']]
        del data['v']

        return data

    def _preprocess_set_data(self, values):
        del values['coords']

        values['v'] = [[v] for v in [values['v_init'], values['v_end']]]
        del values['v_init']
        del values['v_end']

        return values


class CalibrationRectangleForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        frame_names = ['canvas_coords', 'coords', 'keep_real', 'color',
                       'width', 'size', 'allow']

        title = 'Add calibration' if obj is None else 'Edit calibration'
        super().__init__(canvas, frame_names, *args, obj=obj, title=title,
                         vert_space=vert_space, **kwargs)

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

    def _add_object(self, data):
        self.canvas.calibrate(**data)


class CanvasImageForm(_BaseForm):

    def __init__(self, canvas, *args, obj=None, vert_space=10, **kwargs):
        frame_names = ['path', 'upper_left_corner', 'size', 'allow']

        title = 'Add image' if obj is None else 'Edit image'
        super().__init__(canvas, frame_names, *args, obj=obj, title=title,
                         vert_space=vert_space, **kwargs)

    def _config_path(self):
        frame = PathEntryFrame(self.holder, 'path', self.on_browse)
        return frame, {'path': frame}

    def _config_upper_left_corner(self):
        return super()._config_coords(name='upper_left_corner',
                                      label='upper left corner')

    def _config_size(self, allow_edit=True, allow_translate=True,
                     allow_delete=True):
        container_frame = ttk.Frame(self.holder)

        width_frame = IntEntryFrame(container_frame, 'width', default=300,
                                    min_value=10)
        width_frame.pack(side='left', fill='both', expand=True)

        height_frame = IntEntryFrame(container_frame, 'height', default=300,
                                     min_value=10)
        height_frame.pack(side='left', fill='both', expand=True)

        return container_frame, {'width': width_frame,
                                 'height': height_frame}

    def _post_process_get_data(self, data):
        data['size'] = (data['width'], data['height'])
        del data['width']
        del data['height']

        return data

    def _preprocess_set_data(self, values):
        values['width'], values['height'] = values['size']
        del values['size']

        return values

    def _add_object(self, data):
        self.canvas.add_image(**data)

    def on_browse(self, *args):
        previous_path = self.info_container['path'].get()

        title = 'Choose image'
        filetypes = [('image files', fmt) for fmt in IMG_FORMATS]
        path = filedialog.askopenfilename(title=title, filetypes=filetypes)

        if path == "":
            return

        path = os.path.relpath(path)

        if path == previous_path:
            return

        self.info_container['path'].set(path)

        image = Image.open(path)
        self.info_container['width'].set(image.size[0])
        self.info_container['height'].set(image.size[1])


class _LabeledFrame(ttk.Frame):

    def __init__(self, holder, label):
        super().__init__(holder)
        self.label = None

        if label is not None:
            self.label = ttk.Label(self, text=label)
            self.label.pack()

    @property
    def name(self):
        return self.label.cget('text') if self.label is not None else None

    def get(self):
        return self.tk_var.get()

    def set(self, value):
        return self.tk_var.set(value)

    def validate(self):
        return True


class _EntryFrame(_LabeledFrame, metaclass=ABCMeta):

    def __init__(self, holder, label, default):
        super().__init__(holder, label)

        self.tk_var = self._create_tk_var()
        self.tk_var.set(default)

        self.entry = ttk.Entry(self, textvariable=self.tk_var)
        self.entry.pack()

    @abstractmethod
    def _create_tk_var(self):
        pass


class StringEntryFrame(_EntryFrame):

    def __init__(self, holder, label, default='', allow_empty=True,
                 forbidden_values=None):
        self.allow_empty = allow_empty
        self.forbidden_values = forbidden_values if forbidden_values is not None else ()

        super().__init__(holder, label, default)

    def _create_tk_var(self):
        return tk.StringVar()

    def validate(self):
        value = self.get()
        if not self.allow_empty:
            if value == '':
                return False

        if value in self.forbidden_values:
            return False

        return True


class IntEntryFrame(_EntryFrame):
    def __init__(self, holder, label, default=0, min_value=None, max_value=None):
        super().__init__(holder, label, default)
        self.min_value = min_value
        self.max_value = max_value

    def _create_tk_var(self):
        return tk.IntVar()

    def validate(self):
        value = self.get()

        if self.min_value is not None:
            if value < self.min_value:
                return False

        if self.max_value is not None:
            if value > self.max_value:
                return False

        return True


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

    def validate(self):
        try:
            self.get()
        except tk.TclError:
            return False

        return True


class MultipleCoordsFrame(_LabeledFrame):

    def __init__(self, holder, label='coords', dim=2, height=100,
                 allow_rep=False):
        super().__init__(holder, label)
        self.allow_rep = allow_rep
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

    def validate(self):
        # verify each frame
        for frame in self.frames:
            if not frame.validate():
                return False

        # verify repetitions
        if not self.allow_rep:
            for i, frame in enumerate(self.frames):
                coords = frame.get()
                for other_frame in self.frames[i + 1:]:
                    other_coords = other_frame.get()
                    if np.allclose(coords, other_coords):
                        return False

        return True


class PathEntryFrame(_LabeledFrame):

    def __init__(self, holder, label, command, default='', allow_empty=False):
        super().__init__(holder, label)

        self.path_frame = StringEntryFrame(self, None, default=default,
                                           allow_empty=allow_empty)
        self.path_frame.pack(side='left', fill='both')
        self.path_frame.entry.configure(state='readonly')

        self.button = self._create_button(command)
        self.button.pack(side='left', fill='y')

    def _create_button(self, command):
        filename = get_image_path('load_icon.gif')

        img = Image.open(filename).convert('RGBA')
        self._button_image = ImageTk.PhotoImage(img)

        button = ttk.Button(self, command=command, image=self._button_image)
        return button

    def get(self):
        return self.path_frame.get()

    def set(self, value):
        self.path_frame.set(value)

    def validate(self):
        return self.path_frame.validate()


OBJ2FORM = {
    'Point': PointForm,
    'Line': LineForm,
    'Slider': SliderForm,
    'CalibrationRectangle': CalibrationRectangleForm,
    'CanvasImage': CanvasImageForm,
}
