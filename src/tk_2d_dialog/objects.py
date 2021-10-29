from abc import ABCMeta
import tkinter as tk

import numpy as np
from PIL import ImageTk  # TODO: add PIL to dependencies
from PIL import Image

from tk_2d_dialog.popups import CanvasPopupMenu
from tk_2d_dialog.popups import ObjectPopupMenu
from tk_2d_dialog.popups import LinePopupMenu
from tk_2d_dialog.popups import SliderPopupMenu
from tk_2d_dialog.popups import ImagePopupMenu
from tk_2d_dialog.utils import flatten_list
from tk_2d_dialog.utils import get_bound_position
from tk_2d_dialog.utils import MAP_POS_TO_CURSOR_SYMBOL


ATOL = 1e-6


# TODO: add mouse position in real world coordinates at bottom (info bar?)
# TODO: cross-platform bindings
# TODO: edit behavior


class GeometricCanvas(tk.Canvas):
    type = 'GeometricCanvas'
    # TODO: retrieve size

    def __init__(self, holder, width=800, height=800, **canvas_kwargs):
        super().__init__(holder, width=width, height=height, **canvas_kwargs)
        self.objects = {}

        self.calibration_rectangle = None
        self.image = None

        self.popup_menu = CanvasPopupMenu(self)

    @property
    def calibrated(self):
        return self.calibration_rectangle is not None

    def has_image(self):
        return self.image is not None

    def map2real(self, coords):
        return self.calibration_rectangle.map2real(coords)

    def map2canvas(self, coords):
        return self.calibration_rectangle.map2canvas(coords)

    def get_by_type(self, obj_type):
        return [obj for obj in self.objects.values() if obj.type == obj_type]

    def get_names(self, obj_type=None):
        if obj_type:
            objects = self.get_by_type(obj_type)
        else:
            objects = self.objects.values()

        return [obj.name for obj in objects]

    def add_object(self, obj, show=True):
        if not self.calibrated:
            raise Exception('Cannot add objects before calibration')

        if obj.name == '' or obj.name in self.get_names():
            raise Exception('Name already exists')

        item_id = obj.create_widget(self)

        self.objects[item_id] = obj

        if not show:
            obj.hide()

    def delete_object(self, id):
        obj = self.objects[id]
        obj.destroy()
        del self.objects[id]

    def show_all(self):
        for obj in self.objects.values():
            obj.show()

    def hide_all(self):
        for obj in self.objects.values():
            obj.hide()

    def calibrate(self, canvas_coords, coords, keep_real=False, width=2,
                  size=8, color='black', allow_translate=True, allow_edit=True,
                  show=True):
        self.calibration_rectangle = _CalibrationRectangle(
            canvas_coords, coords, keep_real=keep_real, width=width,
            size=size, color=color, allow_translate=allow_translate,
            allow_edit=allow_edit)

        self.calibration_rectangle.create_widget(self)

        if not show:
            self.calibration_rectangle.hide()

    def add_image(self, path, upper_left_corner=(0, 0), size=None, show=True,
                  allow_translate=True, allow_edit=True, allow_delete=True):
        # TODO: allow resize?
        self.image = _CanvasImage(path=path, upper_left_corner=upper_left_corner,
                                  size=size, allow_translate=allow_translate,
                                  allow_edit=allow_edit,
                                  allow_delete=allow_delete)

        self.image.create_widget(self)
        self.tag_lower(self.image.id)  # move image back

        if not show:
            self.image.hide()

    def delete_image(self):
        self.image.destroy()
        self.image = None

    def is_hidden(self, obj_id):
        return self.itemcget(obj_id, 'state') == 'hidden'


class _BaseCanvasObject(metaclass=ABCMeta):

    def __init__(self, name, text, color, allow_translate, allow_delete,
                 allow_edit):
        self.name = name
        self.text = text
        self._allow_translate = allow_translate
        self._allow_delete = allow_delete
        self._allow_edit = allow_edit
        self._color = color

        self._id = None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if self._id is not None:
            raise Exception('A widget can be set only once')

        self._id = value
        self._on_widget_creation()

    def create_widget(self, canvas):
        self._set_canvas(canvas)

    def _set_canvas(self, canvas):
        self.canvas = canvas

    @property
    def canvas_coords(self):
        canvas_coords = self.canvas.coords(self.id)
        return canvas_coords

    @canvas_coords.setter
    def canvas_coords(self, values):
        self.canvas.coords(self.id, *values)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.canvas.itemconfigure(self.id, fill=value)

    @property
    def allow_translate(self):
        return self._allow_translate

    @allow_translate.setter
    def allow_translate(self, value):
        self._allow_translate = value
        if value:
            self.bind_translate()
        else:
            self.unbind_translate()

    @property
    def allow_delete(self):
        return self._allow_delete

    @allow_delete.setter
    def allow_delete(self, value):
        self._allow_delete = value
        if value:
            self.bind_delete()
        else:
            self.unbind_delete()

    @property
    def allow_edit(self):
        return self._allow_edit

    @allow_edit.setter
    def allow_edit(self, value):
        self._allow_edit = value
        if value:
            self.bind_edit()
        else:
            self.unbind_edit()

    def hide(self):
        self.canvas.itemconfigure(self.id, state='hidden')

    def show(self):
        self.canvas.itemconfigure(self.id, state='normal')

    def bind_translate(self):
        self.canvas.tag_bind(self.id, '<Button-1>', self.on_config_delta_mov)
        self.canvas.tag_bind(self.id, '<B1-Motion>', self.on_translate)

    def unbind_translate(self):
        self.canvas.tag_unbind(self.id, '<Button-1>')
        self.canvas.tag_unbind(self.id, '<B1-Motion>')

    def bind_delete(self):
        self.popup_menu.bind_delete()

    def unbind_delete(self):
        self.popup_menu.unbind_delete()

    def bind_edit(self):
        self.popup_menu.bind_edit()

    def unbind_edit(self):
        self.popup_menu.unbind_edit()

    def _config_bindings(self):
        if self.allow_translate:
            self.bind_translate()

        self.canvas.tag_bind(self.id, '<Enter>', self.on_enter)
        self.canvas.tag_bind(self.id, '<Leave>', self.on_leave)

    def _on_widget_creation(self):
        self._config_bindings()
        self._create_popup_menu()

    def on_translate(self, event):
        self.canvas_coords = self._click_coords + self._get_delta_mov(event)

    def on_config_delta_mov(self, event):
        self._click_mouse_coords = event.x, event.y
        self._click_coords = self.canvas_coords

    def _get_delta_mov(self, event):
        return np.array((event.x - self._click_mouse_coords[0],
                         event.y - self._click_mouse_coords[1]))

    def destroy(self):
        self._destroy_popup_menu()
        self.canvas.delete(self.id)

    def _create_popup_menu(self):
        self.popup_menu = ObjectPopupMenu(self)

    def _destroy_popup_menu(self):
        self.popup_menu.destroy()

    def on_enter(self, *args):
        self.canvas.popup_menu.unbind_menu_trigger()

    def on_leave(self, *args):
        self.canvas.popup_menu.bind_menu_trigger()

    def as_dict(self):
        data = {'name': self.name,
                'text': self.text,
                'color': self.color,
                'allow_translate': self.allow_translate,
                'allow_delete': self.allow_delete,
                'allow_edit': self.allow_edit}

        return self._clean_data_dict(data)

    def update(self, name=None, text=None, color=None, allow_translate=None,
               allow_delete=None, allow_edit=None):
        if name is not None:
            self.name = name

        if color is not None:
            self.color = color

        if text is not None:
            self.text = text

        if allow_translate is not None:
            self.allow_translate = allow_translate

        if allow_delete is not None:
            self.allow_delete = allow_delete

        if allow_edit is not None:
            self.allow_edit = allow_edit

    def _clean_data_dict(self, data):
        return {key: value for key, value in data.items() if value is not None}


class _CompositeBaseObject(_BaseCanvasObject, metaclass=ABCMeta):

    def __init__(self, *args, width=1, size=4, **kwargs):
        super().__init__(*args, **kwargs)
        self._size = size
        self._width = width

    @property
    def coords(self):
        return np.array([point.coords for point in self.points])

    @coords.setter
    def coords(self, values):
        for point, new_coords in zip(self.points, values):
            point.coords = new_coords

    @property
    def canvas_coords(self):
        return np.array([point.canvas_coords for point in self.points])

    @canvas_coords.setter
    def canvas_coords(self, values):
        for point, new_coords in zip(self.points, values):
            point.canvas_coords = new_coords

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self.canvas.itemconfigure(self.id, width=value)

    @_BaseCanvasObject.color.setter
    def color(self, value):
        super(_CompositeBaseObject, type(self)).color.fset(self, value)

        for point in self.points:
            point.color = self.color

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        for point in self.points:
            point.size = value

    def show(self):
        super().show()
        for point in self.points:
            point.show()

    def hide(self):
        super().hide()
        for point in self.points:
            point.hide()

    def destroy(self):
        super().destroy()
        for point in self.points:
            point.destroy()

    def _create_points(self, canvas):
        for point in self.points:
            point.create_widget(canvas)

    def update(self, name=None, coords=None, color=None, width=None, size=None,
               small_size=None, text=None, allow_translate=None, allow_delete=None,
               allow_edit=None):
        super().update(name=name, text=text, color=color,
                       allow_translate=allow_translate,
                       allow_delete=allow_delete, allow_edit=allow_edit)

        if width is not None:
            self.width = width

        if size is not None:
            self.size = size

        if coords is not None:
            self.coords = coords

    def as_dict(self):
        data = super().as_dict()
        data.update(
            {'coords': list(self.coords),
             'width': self.width,
             'size': self.size})

        return self._clean_data_dict(data)


class _CalibrationRectangle(_CompositeBaseObject):
    # TODO: translate similar to Image?
    type = 'CalibrationRectangle'

    def __init__(self, canvas_coords, coords, width=2, size=8,
                 color='black', keep_real=False, allow_translate=True,
                 allow_edit=True):
        super().__init__(None, None, color, width=width, size=size,
                         allow_translate=allow_translate, allow_delete=False,
                         allow_edit=allow_edit)
        self._pt1 = _MasterCalibrationPoint(self, canvas_coords[0], coords[0],
                                            color=color, size=size)
        self._pt2 = _MasterCalibrationPoint(self, canvas_coords[1], coords[1],
                                            color=color, size=size)
        self.keep_real = keep_real
        self._min_dist = 2

    @_CompositeBaseObject.color.setter
    def color(self, value):
        self._color = value
        self.canvas.itemconfigure(self.id, outline=value)
        for point in self.points:
            point.color = value

    @property
    def points(self):
        return [self._pt1, self._pt2]

    def create_widget(self, canvas):
        self.canvas = canvas

        # create rectangle
        pt_top_left, pt_bottom_right = self._get_corners()
        self.id = self.canvas.create_rectangle(*pt_top_left.canvas_coords,
                                               *pt_bottom_right.canvas_coords,
                                               outline=self.color,
                                               width=self.width)
        # create points
        self._create_points(canvas)

    def _get_corners(self):
        # alternative is to modify mapping functions
        pt1_position = self._pt1.position
        pt2_position = self._pt2.position

        if pt1_position == 'top_left' and pt2_position == 'bottom_right':
            return self._pt1, self._pt2
        elif pt1_position == 'bottom_right' and pt2_position == 'top_left':
            return self._pt2, self._pt1
        elif (pt1_position == 'bottom_left' and pt2_position == 'top_right') or pt1_position == 'top_right' and pt2_position == 'bottom_left':
            if (pt1_position == 'bottom_left' and pt2_position == 'top_right'):
                pt_bottom_left, pt_top_right = self._pt1, self._pt2
            else:
                pt_bottom_left, pt_top_right = self._pt2, self._pt1

            # pt top left
            canvas_coords = (pt_bottom_left.canvas_coords[0],
                             pt_top_right.canvas_coords[1])
            coords = (pt_bottom_left.coords[0],
                      pt_top_right.coords[1])
            pt_top_left = _CalibrationPoint(canvas_coords, coords)

            # pt bottom right
            canvas_coords = (pt_top_right.canvas_coords[0],
                             pt_bottom_left.canvas_coords[1])
            coords = (pt_top_right.coords[0],
                      pt_bottom_left.coords[1])
            pt_bottom_right = _CalibrationPoint(canvas_coords, coords)

            return pt_top_left, pt_bottom_right

    def map2real(self, coords):
        pt_top_left, pt_bottom_right = self._get_corners()

        canvas_diff, real_diff = pt_bottom_right - pt_top_left
        u = (coords - pt_top_left.canvas_coords) / canvas_diff

        return real_diff * u * np.array([1, 1]) + pt_top_left.coords

    def map2canvas(self, coords):
        pt_top_left, pt_bottom_right = self._get_corners()

        canvas_diff, real_diff = pt_bottom_right - pt_top_left
        u = (coords - pt_top_left.coords) / real_diff

        return canvas_diff * u + pt_top_left.canvas_coords

    def update_coords(self):
        # when master points are updated
        pt_top_left, pt_bottom_right = self._get_corners()

        self.canvas.coords(self.id, *pt_top_left.canvas_coords,
                           *pt_bottom_right.canvas_coords)

    def update(self, name=None, coords=None, canvas_coords=None, color=None,
               width=None, size=None, keep_real=None, allow_translate=None,
               allow_delete=None, allow_edit=None):

        if keep_real is not None:
            self.keep_real = keep_real

        super().update(name=name, coords=coords, color=color, width=width,
                       size=size,
                       allow_translate=allow_translate, allow_delete=allow_delete,
                       allow_edit=allow_edit)

        if canvas_coords is not None:
            self.canvas_coords = np.array(canvas_coords)

    def as_dict(self):
        data = super().as_dict()
        del data['allow_delete']

        data.update(
            {'canvas_coords': [point.canvas_coords for point in self.points],
             'keep_real': self.keep_real})

        return self._clean_data_dict(data)


class _CanvasImage(_BaseCanvasObject):
    type = 'CanvasImage'
    # TODO: keep ratio -> Ctrl-Motion
    # TODO: enlarge from center -> Shift-Ctrl-Motion
    # TODO: make current size appear near the mouse when changing size?
    # TODO: set opacity

    def __init__(self, path, upper_left_corner=(0, 0), size=None,
                 allow_translate=True, allow_delete=True, allow_edit=True):
        super().__init__(None, None, None, allow_translate=allow_translate,
                         allow_delete=allow_delete, allow_edit=allow_edit)
        self._init_path = path
        self._init_upper_left_corner = upper_left_corner
        self._init_size = size

        self._image = None
        self._photo_image = None

    @property
    def upper_left_corner(self):
        return self.canvas_coords

    @upper_left_corner.setter
    def upper_left_corner(self, coords):
        self.canvas_coords = coords

    @property
    def size(self):
        return self._image.size

    @size.setter
    def size(self, value):
        self._photo_image = self._get_photo_image(value)
        self.canvas.itemconfig(self.id, image=self._photo_image)

    @property
    def path(self):
        return self._original_image.filename

    @path.setter
    def path(self, value):
        if self.path == value:
            return

        self._original_image = Image.open(value)
        self._photo_image = self._get_photo_image(self.size)
        self.canvas.itemconfig(self.id, image=self._photo_image)

    def bind_translate(self):
        self.canvas.tag_bind(self.id, '<Motion>', self.on_config_resize)

        self.canvas.tag_bind(self.id, '<Control-1>', self.on_config_delta_mov)
        self.canvas.tag_bind(self.id, '<Control-1>',
                             self.on_config_cursor_translate, add='+')
        self.canvas.tag_bind(self.id, '<Control-B1-Motion>', self.on_translate)
        self.canvas.tag_bind(self.id, '<ButtonRelease-1>', self.on_reset_cursor)

    def _get_photo_image(self, size):
        self._image = self._original_image
        if size is not None:
            self._image = self._original_image.resize(size)

        return ImageTk.PhotoImage(self._image)

    def create_widget(self, canvas):
        super().create_widget(canvas)

        self._original_image = Image.open(self._init_path)

        self._photo_image = self._get_photo_image(self._init_size)
        self.id = self.canvas.create_image(*self._init_upper_left_corner,
                                           image=self._photo_image, anchor='nw')

    def _create_popup_menu(self):
        self.popup_menu = ImagePopupMenu(self)

    def on_enter(self, *args):
        pass

    def on_leave(self, *args):
        self._unbind_resize()

    def on_config_cursor_translate(self, *args):
        self.canvas.config(cursor='fleur')

    def _config_cursor_bound(self, position):
        symbol = MAP_POS_TO_CURSOR_SYMBOL.get(position)
        self.canvas.config(cursor=symbol)

    def on_reset_cursor(self, *args):
        self.canvas.config(cursor='')

    def _unbind_resize(self):
        self.canvas.tag_unbind(self.id, '<B1-Motion>')
        self.on_reset_cursor()

    def on_config_resize(self, event):
        tol = 3

        position = get_bound_position(self.canvas, self.id, event.x, event.y,
                                      tol=tol)
        if position is not None:
            self.on_config_delta_mov(event)  # avoid resize bug
            self.canvas.tag_bind(self.id, '<1>', self.on_config_delta_mov)
            self._config_cursor_bound(position)

            self.canvas.tag_bind(self.id, '<B1-Motion>',
                                 lambda event, pos=position: self._on_resize(event, pos))

        else:
            self._unbind_resize()

    def _on_resize(self, event, position):
        map_pos_to_zero_index = {'left': 1, 'right': 1, 'top': 0, 'bottom': 0}

        delta = self._get_delta_mov(event)
        index = map_pos_to_zero_index.get(position, None)
        if index is not None:
            delta[index] = 0

        if 'left' in position:
            delta[0] *= -1

        if 'top' in position:
            delta[1] *= -1

        previous_size = self._image.size
        self.size = (previous_size[0] + delta[0], previous_size[1] + delta[1])

        self.on_config_delta_mov(event)

        if 'left' in position or 'top' in position:
            pos_split = position.split('-')
            if len(pos_split) > 1:
                if pos_split[0] == 'top' and pos_split[1] != 'left':
                    delta[0] = 0
                elif pos_split[0] == 'bottom':
                    delta[1] = 0

            previous_coords = self.canvas_coords
            self.canvas_coords = (previous_coords[0] - delta[0],
                                  previous_coords[1] - delta[1])

    def update(self, allow_translate=None, allow_delete=None, allow_edit=None,
               path=None, upper_left_corner=None, size=None,):
        super().update(allow_translate=allow_translate,
                       allow_delete=allow_delete, allow_edit=allow_edit)

        if path is not None:
            self.path = path

        if upper_left_corner is not None:
            self.upper_left_corner = upper_left_corner

        if size is not None:
            self.size = size

    def as_dict(self):
        data = super().as_dict()
        data.update({
            'upper_left_corner': self.upper_left_corner,
            'path': self.path,
            'size': self.size,
        })

        return self._clean_data_dict(data)


class Point(_BaseCanvasObject):
    type = 'Point'

    def __init__(self, name, coords, color='blue', size=5, text='',
                 allow_translate=True, allow_delete=True, allow_edit=True):
        super().__init__(name, text, color, allow_translate, allow_delete,
                         allow_edit)
        self._init_coords = coords
        self._size = size

    def __sub__(self, other):
        return self.canvas_coords - other.canvas_coords

    @property
    def size(self):
        # TODO: make it "automatic"?
        return self._size

    @size.setter
    def size(self, value):
        coords = self.canvas_coords
        self._size = value

        (x0, y0), (x1, y1) = self._get_rect_corners(coords)
        self.canvas.coords(self.id, x0, y0, x1, y1)

    @property
    def coords(self):
        return np.array(self.canvas.map2real(self.canvas_coords))

    @coords.setter
    def coords(self, values):
        self.canvas_coords = self.canvas.map2canvas(np.array(values))

    @coords.setter
    def coords(self, coords):
        self.canvas_coords = self.canvas.map2canvas(coords)

    @property
    def canvas_coords(self):
        x, y, *_ = self.canvas.coords(self.id)
        return np.array([x, y]) + self.size

    @canvas_coords.setter
    def canvas_coords(self, center_coords):
        x1, y1 = center_coords - self.size
        x2, y2 = center_coords + self.size
        self.canvas.coords(self.id, [x1, y1, x2, y2])

    def _get_rect_corners(self, coords):
        # in canvas coordinates
        x, y = coords

        r = self.size
        x0, y0 = x - r, y - r
        x1, y1 = x + r, y + r

        return (x0, y0), (x1, y1)

    def _get_init_coords(self):
        return self.canvas.map2canvas(self._init_coords)

    def create_widget(self, canvas):
        super().create_widget(canvas)

        (x0, y0), (x1, y1) = self._get_rect_corners(self._get_init_coords())

        self.id = self.canvas.create_oval(
            x0, y0, x1, y1, fill=self.color, outline="")

        return self.id

    def update(self, name=None, coords=None, color=None, size=None, text=None,
               allow_translate=None, allow_delete=None, allow_edit=None):
        super().update(name, text, color, allow_translate, allow_delete,
                       allow_edit)

        if size is not None:
            self.size = size

        if coords is not None:
            self.coords = coords

    def as_dict(self):
        data = super().as_dict()
        data.update(
            {'coords': list(self.coords),
             'size': self.size})

        return self._clean_data_dict(data)


class _DependentPoint(Point, metaclass=ABCMeta):

    def __init__(self, master, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master = master

    @property
    def popup_menu(self):
        return self.master.popup_menu

    def _create_popup_menu(self):
        # uses line menu
        self.popup_menu.add_triggerer(self)

    def _destroy_popup_menu(self):
        pass


class _CalibrationPoint:

    def __init__(self, canvas_coords, coords):
        self._canvas_coords = np.array(canvas_coords)
        self._coords = np.array(coords)

    def __sub__(self, other):
        canvas_diff = self.canvas_coords - other.canvas_coords
        real_diff = self.coords - other.coords

        return canvas_diff, real_diff

    @property
    def canvas_coords(self):
        return self._canvas_coords

    @property
    def coords(self):
        return self._coords


class _MasterCalibrationPoint(_DependentPoint, _CalibrationPoint):

    def __init__(self, calibration_rectangle, canvas_coords, coords,
                 keep_real=False, color='green', size=5):
        _DependentPoint.__init__(self, calibration_rectangle, None, None,
                                 color=color, size=size)
        _CalibrationPoint.__init__(self, canvas_coords, coords)

    def __sub__(self, other):
        return _CalibrationPoint.__sub__(self, other)

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, center_coords):

        # collect previous coords
        if self.master.keep_real:
            previous_coords = self._collect_previous_obj_coords()

        # update calibration
        self._coords = np.array(center_coords)

        # update coords
        if self.master.keep_real:
            self._update_obj_coords(previous_coords)

    @property
    def canvas_coords(self):
        return self._canvas_coords

    @canvas_coords.setter
    def canvas_coords(self, center_coords):
        pt1, pt2 = self.master.points
        other = pt2 if self is pt1 else pt1
        diff = np.abs(center_coords - other.canvas_coords)
        if np.any(diff < self.master._min_dist):
            return

        # collect previous coords
        if self.master.keep_real:
            previous_coords = self._collect_previous_obj_coords()

        # update calibration
        self._canvas_coords = np.array(center_coords)
        Point.canvas_coords.__set__(self, center_coords)
        self.master.update_coords()

        # update coords
        if self.master.keep_real:
            self._update_obj_coords(previous_coords)

    def _get_init_coords(self):
        return self._canvas_coords

    def _collect_previous_obj_coords(self):
        coords = []
        for obj in self.canvas.objects.values():  # assumes dict is ordered
            coords.append(obj.coords)

        return coords

    def _update_obj_coords(self, coords):
        for obj, coords in zip(self.canvas.objects.values(), coords):
            obj.update(coords=coords)

    @property
    def position(self):
        pt1, pt2 = self.master.points
        other = pt2 if self is pt1 else pt1

        if self.canvas_coords[0] < other.canvas_coords[0]:
            if self.canvas_coords[1] < other.canvas_coords[1]:
                return 'top_left'
            else:
                return 'bottom_left'

        else:
            if self.canvas_coords[1] < other.canvas_coords[1]:
                return 'top_right'
            else:
                return 'bottom_right'


class _LinePoint(_DependentPoint):

    def __init__(self, line, coords, color='blue', size=5, allow_translate=True):
        super().__init__(line, None, coords, color=color, size=size, text='',
                         allow_translate=allow_translate)

    @property
    def canvas(self):
        return self.master.canvas

    def _set_canvas(self, *args):
        pass

    @Point.canvas_coords.setter
    def canvas_coords(self, center_coords):
        super(_LinePoint, type(self)).canvas_coords.fset(self, center_coords)
        self.master.update_coords()


class _MasterSliderPoint(_LinePoint):

    def __init__(self, slider, v, color='blue', size=5, allow_translate=True):
        super().__init__(slider, None, color=color, size=size,
                         allow_translate=allow_translate)
        self.v = v

    def _get_init_coords(self):
        return self.master.anchor.get_coords_by_v(self.v)

    @_LinePoint.canvas_coords.setter
    def canvas_coords(self, center_coords):
        center_coords_ = self.master.anchor.find_closest_point(center_coords)
        self.v = self.master.anchor.get_v(center_coords_)
        super(_MasterSliderPoint, type(self)).canvas_coords.fset(self, center_coords_)

    def update_coords(self):
        # when line changes, to keep v
        self.canvas_coords = self.master.anchor.get_coords_by_v(self.v)


class _SlaveSliderPoint(_LinePoint):

    def __init__(self, slider, t, color='blue', size=5):
        super().__init__(slider, None, color=color, size=size,
                         allow_translate=False)
        self._t = t

    def _get_init_coords(self):
        return self.master.anchor.get_coords_by_v(self.v)

    @property
    def t(self):
        return self._t

    @t.setter
    def t(self, value):
        self._t = value
        self.canvas_coords = self.canvas_coords  # beautiful
        self.master.update_coords()

    @property
    def v(self):
        return self.master.master_pts[0].v + self.t * (self.master.master_pts[1].v - self.master.master_pts[0].v)

    @property
    def canvas_coords(self):
        return self.master.anchor.get_coords_by_v(self.v)

    @canvas_coords.setter
    def canvas_coords(self, center_coords):
        if not np.allclose(center_coords, self.canvas_coords):
            raise Exception('Invalid center coords.')

        super(_LinePoint, type(self)).canvas_coords.fset(self, center_coords)


class _AbstractLine(_CompositeBaseObject, metaclass=ABCMeta):

    def __init__(self, name, points, width=1, size=5, small_size=3, color='red',
                 text='', allow_translate=True, allow_delete=True,
                 allow_edit=True):
        super().__init__(name, text, color, allow_translate, allow_delete,
                         allow_edit=allow_edit, width=width, size=size)
        self.points = points
        self.sliders = []
        self._small_size = small_size  # sizes are useless until they're set

    @_CompositeBaseObject.allow_translate.setter
    def allow_translate(self, value):
        super(_AbstractLine, type(self)).allow_translate.fset(self, value)

        for slider in self.sliders:
            slider.allow_translate = value

    @_CompositeBaseObject.size.setter
    def size(self, value):
        self._size = value
        self.points[0].size = value

    @property
    def small_size(self):
        return self._small_size

    @small_size.setter
    def small_size(self, value):
        self._small_size = value
        for point in self.points[1:]:
            point.size = value

    def create_widget(self, canvas):
        self.canvas = canvas

        # create line
        coords = [point._get_init_coords() for point in self.points]
        self.id = self.canvas.create_line(
            flatten_list(coords), fill=self.color, width=self.width)

        # create points (order matters for bindings)
        self._create_points(canvas)

        return self.id

    def show(self):
        super().show()
        for slider in self.sliders:
            slider.show(from_anchor=True)

    def hide(self):
        super().hide()
        for slider in self.sliders:
            slider.hide(from_anchor=True)

    def destroy(self):
        super().destroy()
        for slider in self.sliders.copy():
            slider.destroy()

    def find_closest_point(self, coords):
        # check first if already in line
        if self._which_segment(coords) is not None:
            return coords

        line_coords = self.canvas_coords

        pt = np.array(coords)
        dist = np.linalg.norm(line_coords - pt, axis=1)

        closest_idx = np.argmin(dist)
        n_pts = line_coords.shape[0]

        closest_pt = line_coords[closest_idx, :]

        pt_left = line_coords[closest_idx - 1, :] if closest_idx > 0 else np.nan
        pt_right = line_coords[closest_idx + 1, :] if closest_idx < n_pts - 1 else np.nan

        direcs = [pt_left - closest_pt, pt_right - closest_pt]
        direcs = [direc / np.linalg.norm(direc) for direc in direcs]
        vec = pt - closest_pt

        par_projs = []
        for direc in direcs:
            scalar = np.dot(vec, direc)
            if scalar > 0:
                par_projs.append(scalar * direc)
            else:
                par_projs.append(np.inf)
        perp_projs = [vec - par_proj for par_proj in par_projs]

        par_projs.append(np.zeros(2))
        perp_projs.append(vec)

        closest_idx = np.argmin(np.linalg.norm(perp_projs, axis=1))

        return closest_pt + par_projs[closest_idx]

    def update_coords(self):
        new_coords = [point.canvas_coords for point in self.points]
        self.canvas.coords(self.id, flatten_list(new_coords))

        for slider in self.sliders:
            slider.update_master_pts()

        return new_coords

    def get_coords_by_v(self, v):
        vlims = self._get_vlims()
        for seg_index, (vlim1, vlim2) in enumerate(vlims):
            if v >= vlim1 and v <= vlim2:
                break
        s = (v - vlim1) / (vlim2 - vlim1)
        pt1 = self.points[seg_index].canvas_coords
        pt2 = self.points[seg_index + 1].canvas_coords

        return pt1 + s * (pt2 - pt1)

    def get_v(self, coords):
        # stepwise-linear curve independent variable
        seg_index = self._which_segment(coords)
        s = self.get_s(seg_index, coords)
        vlims = self._get_vlims()[seg_index]

        return vlims[0] + s * (vlims[1] - vlims[0])

    def _get_vlims(self):
        points = self.canvas_coords
        t_vecs = []
        for pt1, pt2 in zip(points, points[1::]):
            t_vecs.append(pt2 - pt1)

        ts = np.linalg.norm(np.array(t_vecs), axis=1)
        ts = np.cumsum(ts / np.sum(ts))
        ts = [0.] + list(ts)

        return [(t0, t1) for t0, t1 in zip(ts, ts[1::])]

    def get_s(self, seg_index, coords):
        # segment independent variable
        pt1 = self.points[seg_index].canvas_coords
        pt2 = self.points[seg_index + 1].canvas_coords
        t_vec = pt2 - pt1

        # TODO: when both are 0 (it should not be possible - overlap)
        i = 1 if abs(t_vec[0]) < ATOL else 0

        return (coords[i] - pt1[i]) / t_vec[i]

    def _which_segment(self, coords):
        points = self.canvas_coords

        for seg_index, (pt1, pt2) in enumerate(zip(points, points[1::])):
            t_vec = pt2 - pt1
            if abs(t_vec[0]) < ATOL:
                i, j = 0, 1
            else:
                i, j = 1, 0

            s = (coords[j] - pt1[j]) / t_vec[j]
            z_cmp = pt1[i] + t_vec[i] * s
            if 0 <= s <= 1 and abs(z_cmp - coords[i]) < ATOL:
                return seg_index

    def add_slider(self, slider):
        self.sliders.append(slider)

    def remove_slider(self, slider):
        self.sliders.remove(slider)

    def update(self, name=None, coords=None, color=None, width=None, size=None,
               small_size=None, text=None, allow_translate=None, allow_delete=None,
               allow_edit=None):
        super().update(name=name, coords=coords, text=text, color=color,
                       width=width, size=size,
                       allow_translate=allow_translate, allow_delete=allow_delete,
                       allow_edit=allow_edit)

        if small_size is not None:
            self.small_size = small_size

    def as_dict(self):
        data = super().as_dict()
        data['small_size'] = self.small_size

        return self._clean_data_dict(data)


class Line(_AbstractLine):
    type = 'Line'

    def __init__(self, name, coords, width=1, size=5, small_size=4, color='red',
                 text='', allow_translate=True, allow_delete=True,
                 allow_edit=True):

        points = [_LinePoint(self, coords_, color=color, size=small_size,
                             allow_translate=allow_translate)
                  for coords_ in coords]
        points[0]._size = size

        super().__init__(name, points, width=width, size=size,
                         small_size=small_size, color=color, text=text,
                         allow_translate=allow_translate,
                         allow_delete=allow_delete, allow_edit=allow_edit)

    def _create_popup_menu(self):
        self.popup_menu = LinePopupMenu(self)

    def add_point(self, coords, pos=None):
        point = _LinePoint(self, self.canvas.map2real(coords), color=self.color,
                           size=self.small_size, allow_translate=self.allow_translate)
        point.create_widget(self.canvas)

        if pos not in ['begin', 'end']:
            seg_index = self._which_segment(point.canvas_coords)
            self.points.insert(seg_index + 1, point)

        elif pos == 'begin':
            point.size = self.size
            self.points.insert(0, point)

        else:
            self.points.append(point)

        self.update_coords()

    def remove_point(self, point):
        if len(self.points) < 3:
            return

        index = self.points.index(point)

        self.points[index].destroy()
        del self.points[index]

        if index == 0:
            self.points[0].size = self.size

        self.update_coords()


class Slider(_AbstractLine):
    type = 'Slider'

    def __init__(self, name, anchor, v_init, v_end, n_points, width=3,
                 size=5, small_size=4, color='green', text='', allow_delete=True,
                 allow_translate=True, allow_edit=True):
        self.anchor = anchor
        self.anchor.add_slider(self)

        self.master_pts = [_MasterSliderPoint(self, v_init, color=color,
                                              size=size),
                           _MasterSliderPoint(self, v_end, color=color,
                                              size=small_size)]

        points = [self.master_pts[0]]
        for t in self._get_ts(n_points):
            points.append(_SlaveSliderPoint(self, t, color=color,
                                            size=small_size))
        points.append(self.master_pts[1])

        super().__init__(name, points, width=width, size=size,
                         small_size=small_size, color=color, text=text,
                         allow_delete=allow_delete,
                         allow_translate=allow_translate, allow_edit=allow_edit)

    def _get_ts(self, n_points):
        return [(i + 1) / (n_points - 1) for i in range(n_points - 2)]

    @property
    def n_points(self):
        return len(self.points)

    @n_points.setter
    def n_points(self, n_points):
        if self.n_points == n_points or n_points < 3:
            return

        previous_n = self.n_points

        if previous_n > n_points:  # delete points
            diff_n = previous_n - n_points
            for i in range(diff_n):
                self.points[i + 1].destroy()

            del self.points[1:(1 + diff_n)]

        # add missing points
        ts = self._get_ts(n_points)
        if len(ts) > previous_n - 2:
            for t in ts[previous_n - 2:]:
                new_point = _SlaveSliderPoint(self, t, color=self.color,
                                              size=self.small_size)
                new_point.create_widget(self.canvas)
                self.points.insert(-1, new_point)

        # update points t
        if len(ts) > 0:
            for point, t in zip(self.points[1:-1], ts):
                point.t = t
        else:
            self.update_coords()  # guarantees update of line coords

    @property
    def v_init(self):
        return self.master_pts[0].v

    @v_init.setter
    def v_init(self, value):
        self.master_pts[0].canvas_coords = self.anchor.get_coords_by_v(value)

    @property
    def v_end(self):
        return self.master_pts[1].v

    @v_end.setter
    def v_end(self, value):
        self.master_pts[1].canvas_coords = self.anchor.get_coords_by_v(value)

    def _create_popup_menu(self):
        self.popup_menu = SliderPopupMenu(self)

    def _get_direc(self):
        return self.master_pts[1] - self.master_pts[0]

    def update_coords(self):
        new_coords = super().update_coords()

        # also update slaves
        for point, new_coords_ in zip(self.points[1:-1], new_coords[1:-1]):
            point.canvas_coords = new_coords_

    def update_master_pts(self):
        for pt in self.master_pts:
            pt.update_coords()

    def destroy(self):
        super().destroy()
        self.anchor.remove_slider(self)

    def on_config_delta_mov(self, event):
        self.anchor._click_mouse_coords = event.x, event.y
        self.anchor._click_coords = self.anchor.canvas_coords

    def on_translate(self, event):
        self.anchor.canvas_coords = self.anchor._click_coords + self.anchor._get_delta_mov(event)

    def show(self, from_anchor=False):
        if from_anchor:
            super().show()
        else:
            self.anchor.show()

    def hide(self, from_anchor=False):
        if from_anchor:
            super().hide()
        else:
            self.anchor.hide()

    def update(self, name=None, v_init=None, v_end=None, n_points=None,
               color=None, width=None, size=None, small_size=None, text=None,
               allow_translate=None, allow_delete=None, allow_edit=None,
               **kwargs):
        super().update(name, None, color, width, size, small_size, text,
                       allow_translate, allow_delete, allow_edit)

        if v_init is not None:
            self.v_init = v_init

        if v_end is not None:
            self.v_end = v_end

        if n_points is not None:
            self.n_points = n_points

    def as_dict(self):
        data = super().as_dict()

        data.update({'v_init': self.v_init,
                     'v_end': self.v_end,
                     'n_points': self.n_points})

        return self._clean_data_dict(data)


TYPE2OBJ = {
    'Point': Point,
    'Line': Line,
    'Slider': Slider
}
