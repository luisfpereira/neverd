from abc import ABCMeta
import tkinter as tk

import numpy as np

from tk_2d_dialog.widgets import CanvasPopupMenu
from tk_2d_dialog.widgets import ObjectPopupMenu
from tk_2d_dialog.utils import flatten_list


class Canvas(tk.Canvas):

    def __init__(self, holder, calibration, image=None, width=800,
                 height=800, **canvas_kwargs):
        # TODO: inherit from tk?
        super().__init__(holder, width=width, height=height, **canvas_kwargs)
        self.calibration = calibration
        self.image = image or _NoneWidget(show=True)
        self.objects = {}
        self.popup_menu = CanvasPopupMenu(self)

        # update drawing canvas
        self.calibration.update_canvas(self)
        self.image.update_canvas(self)

        # TODO: create calibration and image widgets

    def map2real(self, coords):
        canvas_diff, real_diff = self.calibration.pt_bottom_right - self.calibration.pt_top_left
        u = (coords[0] - self.calibration.pt_top_left.canvas[0]) / canvas_diff[0]
        v = (coords[1] - self.calibration.pt_top_left.canvas[1]) / canvas_diff[1]

        x_real = real_diff[0] * u + self.calibration.pt_top_left.real[0]
        y_real = -abs(real_diff[1]) * v + self.calibration.pt_top_left.real[1]

        return x_real, y_real

    def map2canvas(self, coords):
        canvas_diff, real_diff = self.calibration.pt_bottom_right - self.calibration.pt_top_left
        u = (coords[0] - self.calibration.pt_top_left.real[0]) / abs(real_diff[0])
        v = (self.calibration.pt_top_left.real[1] - coords[1]) / abs(real_diff[1])

        x_canvas = canvas_diff[0] * u + self.calibration.pt_top_left.canvas[0]
        y_canvas = canvas_diff[1] * v + self.calibration.pt_top_left.canvas[1]

        return int(x_canvas), int(y_canvas)

    def get_by_type(self, obj_type):
        pass

    def add_object(self, obj):
        obj.update_canvas(self)

        item_id = obj.create_widget()

        self.objects[item_id] = obj

        if not obj._show:
            obj.hide()

    def delete_object(self, id):
        obj = self.objects[id]
        obj.destroy()
        del self.objects[id]


class _BaseWidget(metaclass=ABCMeta):

    def __init__(self, show):
        # TODO: probably show as input
        self._show = show
        self.canvas = None
        self._id = None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value
        self._on_widget_creation()

    def _on_widget_creation(self):
        pass

    def hide(self):
        self._show = False
        self.canvas.itemconfigure(self.id, state='hidden')

    def show(self):
        self._show = True
        self.canvas.itemconfigure(self.id, state='normal')

    def update_canvas(self, canvas):
        # TODO: update or set
        self.canvas = canvas

    def create_widget(self):
        pass


class _NoneWidget(_BaseWidget):
    pass


class _BaseObject(_BaseWidget, metaclass=ABCMeta):

    def __init__(self, name, text, show, allow_translation=True,
                 allow_deletion=True):
        super().__init__(show)
        self.name = name
        self.text = text
        self.allow_translation = allow_translation
        self.allow_deletion = allow_deletion

    def show_text(self):
        pass

    def _config_bindings(self):
        if self.allow_translation:
            self.canvas.tag_bind(self.id, '<Button-1>', self.on_config_delta_mov)
            self.canvas.tag_bind(self.id, '<B1-Motion>', self.on_translate)

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
        self.popup_menu.destroy()
        self.canvas.delete(self.id)

    def _create_popup_menu(self):
        self.popup_menu = ObjectPopupMenu(self)

    def on_enter(self, *args):
        self.canvas.popup_menu.unbind_menu_trigger()

    def on_leave(self, *args):
        self.canvas.popup_menu.bind_menu_trigger()


class CalibrationPoint:
    # TODO: abstract to Point

    def __init__(self, canvas, real):
        self.canvas = canvas
        self.real = real

    def __sub__(self, other):
        canvas_diff = tuple(self.canvas[i] - other.canvas[i] for i in range(2))
        real_diff = tuple(self.real[i] - other.real[i] for i in range(2))

        return canvas_diff, real_diff


class Calibration(_BaseWidget):

    def __init__(self, pt1, pt2, show=True):
        super().__init__(show)
        self._pt1 = pt1
        self._pt2 = pt2
        self.pt_top_left = pt1
        self.pt_bottom_right = pt2


class Image(_BaseWidget):

    def __init__(self, path, upper_left_corner=(0, 0), show=True):
        super().__init__(show)
        self.path = path
        self.upper_left_corner = upper_left_corner


class Point(_BaseObject):

    def __init__(self, name, coords, color='blue', size=5, text='', show=True,
                 allow_translation=True, allow_deletion=True):
        super().__init__(name, text, show, allow_translation=allow_translation,
                         allow_deletion=allow_deletion)
        self._init_coords = coords
        self.color = color
        self.size = size

    def __sub__(self, other):
        return self.canvas_coords - other.canvas_coords

    @property
    def coords(self):
        return np.array(self.canvas.map2real(self.canvas_coords))

    @property
    def canvas_coords(self):
        x, y, *_ = self.canvas.coords(self.id)
        return np.array([x + self.size, y + self.size])

    @canvas_coords.setter
    def canvas_coords(self, center_coords):
        x, y = center_coords[0] - self.size, center_coords[1] - self.size
        self.canvas.moveto(self.id, x, y)

    def _get_init_rect_corners(self):
        # in canvas coordinates
        x, y = self.canvas.map2canvas(self._init_coords)
        r = self.size
        x0, y0 = x - r, y - r
        x1, y1 = x + r, y + r

        return (x0, y0), (x1, y1)

    def create_widget(self):
        (x0, y0), (x1, y1) = self._get_init_rect_corners()

        self.id = self.canvas.create_oval(
            x0, y0, x1, y1, fill=self.color, outline="")

        return self.id


class LinePoint(Point):
    # TODO: delete should not be allowed

    def __init__(self, line, coords, color='blue', size=5, show=True,
                 allow_translation=True):
        super().__init__(None, coords, color=color, size=size, text='',
                         show=show, allow_translation=allow_translation,
                         allow_deletion=False)
        self.line = line

    @property
    def canvas(self):
        return self.line.canvas

    @canvas.setter
    def canvas(self, *args):
        pass

    @Point.canvas_coords.setter
    def canvas_coords(self, center_coords):
        super(LinePoint, type(self)).canvas_coords.fset(self, center_coords)
        self.line.update()


class MasterSliderPoint(LinePoint):

    def __init__(self, slider, coords, color='blue', size=5, show=True,
                 allow_translation=True):
        super().__init__(slider, coords, color=color, size=size, show=show,
                         allow_translation=allow_translation)

        # correct coords
        self._init_coords = self.line.anchor.find_closest_point(
            coords, canvas=False)

    @LinePoint.canvas_coords.setter
    def canvas_coords(self, center_coords):
        center_coords_ = self.line.anchor.find_closest_point(center_coords, canvas=True)
        super(MasterSliderPoint, type(self)).canvas_coords.fset(self, center_coords_)


class SliderPoint(LinePoint):

    def __init__(self, slider, v, color='blue', size=5, show=True):
        super().__init__(slider, None, color=color, size=size, show=show,
                         allow_translation=False)
        self.v = v

        # correct coords
        self._init_coords = self._get_init_coords()

    def _get_init_coords(self):
        pt1, pt2 = self.line.masters
        vec = pt2._init_coords - pt1._init_coords
        pt = pt1._init_coords + vec * self.v

        return self.line.anchor.find_closest_point(pt, canvas=False)

    @property
    def canvas_coords(self):
        dir_vec = self.line._get_direc()
        pt = self.line.masters[0].canvas_coords + self.v * dir_vec

        return self.line.anchor.find_closest_point(pt)

    @canvas_coords.setter
    def canvas_coords(self, center_coords):
        center_coords_ = self.line.anchor.find_closest_point(center_coords, canvas=True)
        super(LinePoint, type(self)).canvas_coords.fset(self, center_coords_)


class _AbstractLine(_BaseObject):
    # TODO: hide points in popup menu

    def __init__(self, name, points, width=1, size=5, color='red', text='',
                 show=True, allow_translation=True, allow_deletion=True):
        super().__init__(name, text, show, allow_translation=allow_translation,
                         allow_deletion=allow_deletion)
        self.points = points
        self.color = color
        self.width = width
        self.sliders = []

    @property
    def coords(self):
        return np.array([point.coords for point in self.points])

    @property
    def canvas_coords(self):
        coords = self.canvas.coords(self.id)
        return np.array([(c1, c2) for c1, c2 in zip(coords[::2], coords[1::2])])

    @canvas_coords.setter
    def canvas_coords(self, new_coords):
        for point, new_coords_ in zip(self.points, new_coords):
            point.canvas_coords = new_coords_

    def create_widget(self):

        # create line
        coords = [self.canvas.map2canvas(point._init_coords) for point in self.points]
        self.id = self.canvas.create_line(
            flatten_list(coords), fill=self.color, width=self.width)

        # create points (order matters for bindings)
        for point in self.points:
            point.create_widget()

        return self.id

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

    def find_closest_point(self, coords, canvas=True):
        line_coords = np.array(self.canvas_coords) if canvas else np.array(self.coords)

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

        par_proj = par_projs[closest_idx]
        if canvas:  # in pixel there's no floats
            par_proj = np.array([int(c) for c in par_proj])

        return closest_pt + par_proj

    def update(self):
        new_coords = [point.canvas_coords for point in self.points]
        self.canvas.coords(self.id, flatten_list(new_coords))

        return new_coords


class Line(_AbstractLine):

    def __init__(self, name, coords, width=1, size=5, color='red', text='',
                 show=True, allow_translation=True, allow_deletion=True):
        points = [LinePoint(self, coords_, color=color, size=size, show=show,
                            allow_translation=allow_translation)
                  for coords_ in coords]
        super().__init__(name, points, width=width, size=size, color=color,
                         text=text, show=show,
                         allow_translation=allow_translation,
                         allow_deletion=allow_deletion)


class Slider(_AbstractLine):

    def __init__(self, name, anchor, pt_init, pt_end, n_points, width=3,
                 size=5, color='green', text='', show=True, allow_deletion=True):
        # TODO: think about best way to pass slider coordinates
        self.anchor = anchor
        self.masters = [MasterSliderPoint(self, pt_init, color=color, size=size,
                                          show=show),
                        MasterSliderPoint(self, pt_end, color=color, size=size,
                                          show=show)]

        points = [self.masters[0]]
        for i in range(n_points - 2):
            points.append(SliderPoint(self, (i + 1) / (n_points - 1), color=color,
                                      size=size - 1, show=show))
        points.append(self.masters[1])

        super().__init__(name, points, width=width, size=size, color=color,
                         text=text, show=show, allow_deletion=allow_deletion,
                         allow_translation=False)

    def _get_direc(self):
        return self.masters[1] - self.masters[0]

    def update(self):
        new_coords = super().update()

        # also update sliders
        for point, new_coords_ in zip(self.points[1:-1], new_coords[1:-1]):
            point.canvas_coords = new_coords_
