from abc import ABCMeta
import tkinter as tk

import numpy as np

from tk_2d_dialog.widgets import CanvasPopupMenu
from tk_2d_dialog.widgets import ObjectPopupMenu
from tk_2d_dialog.utils import flatten_list


ATOL = 1e-6


class Canvas(tk.Canvas):
    type = 'Canvas'

    def __init__(self, holder, calibration, image=None, width=800,
                 height=800, **canvas_kwargs):
        super().__init__(holder, width=width, height=height, **canvas_kwargs)
        self.calibration = calibration
        self.image = image or _NoneWidget(show=True)
        self.objects = {}
        self.popup_menu = CanvasPopupMenu(self)

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

        return x_canvas, y_canvas

    def get_by_type(self, obj_type):
        return [obj for obj in self.objects.values() if obj.type == obj_type]

    def add_object(self, obj):
        item_id = obj.create_widget(self)

        self.objects[item_id] = obj

        if not obj._show:
            obj.hide()

    def delete_object(self, id):
        obj = self.objects[id]
        obj.destroy()
        del self.objects[id]


class _BaseWidget(metaclass=ABCMeta):

    def __init__(self, show):
        self._show = show
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

    def _on_widget_creation(self):
        pass

    def hide(self):
        self._show = False
        self.canvas.itemconfigure(self.id, state='hidden')

    def show(self):
        self._show = True
        self.canvas.itemconfigure(self.id, state='normal')

    def create_widget(self, canvas):
        self._set_canvas(canvas)

    def _set_canvas(self, canvas):
        self.canvas = canvas


class _NoneWidget(_BaseWidget):
    pass


class _BaseObject(_BaseWidget, metaclass=ABCMeta):

    def __init__(self, name, text, color, show, allow_translate, allow_delete,
                 allow_edit):
        super().__init__(show)
        self.name = name
        self.text = text
        self._allow_translate = allow_translate
        self._allow_delete = allow_delete
        self._allow_edit = allow_edit
        self._color = color

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

    def show_text(self):
        pass

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
        # TODO: update to be more general
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

    def as_dict(self):
        data = {'name': self.name,
                'text': self.text,
                'color': self.color,
                'allow_translate': self.allow_translate,
                'allow_delete': self.allow_delete,
                'allow_edit': self.allow_edit}

        return data

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
    type = 'Point'

    def __init__(self, name, coords, color='blue', size=5, text='', show=True,
                 allow_translate=True, allow_delete=True, allow_edit=True):
        super().__init__(name, text, color, show, allow_translate, allow_delete,
                         allow_edit)
        self._init_coords = coords
        self._size = size

    def __sub__(self, other):
        return self.canvas_coords - other.canvas_coords

    @property
    def size(self):
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

    @property
    def canvas_coords(self):
        x, y, *_ = self.canvas.coords(self.id)
        return np.array([x + self.size, y + self.size])

    @canvas_coords.setter
    def canvas_coords(self, center_coords):
        x, y = center_coords[0] - self.size, center_coords[1] - self.size
        self.canvas.moveto(self.id, x, y)

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
            self.canvas_coords = self.canvas.map2canvas(coords)

    def as_dict(self):
        data = super().as_dict()
        data.update(
            {'coords': list(self.coords),
             'size': self.size})

        return data


class LinePoint(Point):

    def __init__(self, line, coords, color='blue', size=5, show=True,
                 allow_translate=True):
        super().__init__(None, coords, color=color, size=size, text='',
                         show=show, allow_translate=allow_translate)
        self.line = line

    @property
    def popup_menu(self):
        return self.line.popup_menu

    def _create_popup_menu(self):
        # uses line menu
        self.popup_menu.add_triggerer(self)

    @property
    def canvas(self):
        return self.line.canvas

    def _set_canvas(self, *args):
        pass

    @Point.canvas_coords.setter
    def canvas_coords(self, center_coords):
        super(LinePoint, type(self)).canvas_coords.fset(self, center_coords)
        self.line.update_coords()


class MasterSliderPoint(LinePoint):

    def __init__(self, slider, v, color='blue', size=5, show=True,
                 allow_translate=True):
        super().__init__(slider, None, color=color, size=size, show=show,
                         allow_translate=allow_translate)
        self.v = v

    def _get_init_coords(self):
        return self.line.anchor.get_coords_by_v(self.v)

    @LinePoint.canvas_coords.setter
    def canvas_coords(self, center_coords):
        center_coords_ = self.line.anchor.find_closest_point(center_coords)
        super(MasterSliderPoint, type(self)).canvas_coords.fset(self, center_coords_)
        self.v = self.line.anchor.get_v(center_coords_)

    def update_coords(self):  # TODO: need to rename
        # when line changes, to keep v
        self.canvas_coords = self.line.anchor.get_coords_by_v(self.v)


class SlaveSliderPoint(LinePoint):

    def __init__(self, slider, t, color='blue', size=5, show=True):
        super().__init__(slider, None, color=color, size=size, show=show,
                         allow_translate=False)
        self.t = t

    def _get_init_coords(self):
        return self.line.anchor.get_coords_by_v(self.v)

    @property
    def v(self):
        return self.line.master_pts[0].v + self.t * (self.line.master_pts[1].v - self.line.master_pts[0].v)

    @property
    def canvas_coords(self):
        return self.line.anchor.get_coords_by_v(self.v)

    @canvas_coords.setter
    def canvas_coords(self, center_coords):
        if not np.allclose(center_coords, self.canvas_coords):
            raise Exception('Invalid center coords.')

        super(LinePoint, type(self)).canvas_coords.fset(self, center_coords)


class _AbstractLine(_BaseObject, metaclass=ABCMeta):

    def __init__(self, name, points, width=1, size=5, small_size=3, color='red',
                 text='', show=True, allow_translate=True, allow_delete=True,
                 allow_edit=True):
        super().__init__(name, text, color, show, allow_translate, allow_delete,
                         allow_edit=allow_edit)
        self.points = points
        self._width = width
        self.sliders = []
        self._size = size  # sizes are useless until they're set
        self._small_size = small_size

    @_BaseObject.allow_translate.setter
    def allow_translate(self, value):
        super(_AbstractLine, type(self)).allow_translate.fset(self, value)

        for slider in self.sliders:
            slider.allow_translate = value

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

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self.canvas.itemconfigure(self.id, width=value)

    @_BaseObject.color.setter
    def color(self, value):
        super(_AbstractLine, type(self)).color.fset(self, value)

        for point in self.points:
            point.color = self.color

    @property
    def size(self):
        return self._size

    @size.setter
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
        for point in self.points:
            point.create_widget(canvas)

        return self.id

    def show(self):
        super().show()
        for point in self.points:
            point.show()

        for slider in self.sliders:
            slider.show(from_anchor=True)

    def hide(self):
        super().hide()
        for point in self.points:
            point.hide()

        for slider in self.sliders:
            slider.hide(from_anchor=True)

    def destroy(self):
        super().destroy()
        for point in self.points:
            point.destroy()

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
                z_cmp = pt1[0]
                i = 0
            else:
                s = (coords[0] - pt1[0]) / t_vec[0]
                z_cmp = pt1[1] + t_vec[1] * s
                i = 1

            if abs(z_cmp - coords[i]) < ATOL:
                return seg_index

    def add_slider(self, slider):
        self.sliders.append(slider)

    def remove_slider(self, slider):
        self.sliders.remove(slider)

    def update(self, name=None, coords=None, color=None, width=None, size=None,
               small_size=None, text=None, allow_translate=None, allow_delete=None,
               allow_edit=None):
        super().update(name, text, color, allow_translate, allow_delete,
                       allow_edit)

        if width is not None:
            self.width = width

        if size is not None:
            self.size = size

        if small_size is not None:
            self.small_size = small_size

        if coords is not None:
            self.canvas_coords = [self.canvas.map2canvas(coords_) for coords_ in coords]

    def as_dict(self):
        data = super().as_dict()
        data.update(
            {'coords': list(self.coords),
             'width': self.width,
             'size': self.size,
             'small_size': self.small_size
             })

        return data


class Line(_AbstractLine):
    type = 'Line'

    def __init__(self, name, coords, width=1, size=5, small_size=4, color='red',
                 text='', show=True, allow_translate=True, allow_delete=True,
                 allow_edit=True):

        points = [LinePoint(self, coords_, color=color, size=small_size, show=show,
                            allow_translate=allow_translate)
                  for coords_ in coords]
        points[0]._size = size

        super().__init__(name, points, width=width, size=size,
                         small_size=small_size, color=color, text=text,
                         show=show, allow_translate=allow_translate,
                         allow_delete=allow_delete, allow_edit=allow_edit)


class Slider(_AbstractLine):
    type = 'Slider'
    # TODO: change update?

    def __init__(self, name, anchor, v_init, v_end, n_points, width=3,
                 size=5, small_size=4, color='green', text='', show=True, allow_delete=True,
                 allow_translate=True, allow_edit=True):
        self.anchor = anchor
        self.anchor.add_slider(self)

        self.master_pts = [MasterSliderPoint(self, v_init, color=color, size=size,
                                             show=show),
                           MasterSliderPoint(self, v_end, color=color,
                                             size=small_size, show=show)]

        points = [self.master_pts[0]]
        for i in range(n_points - 2):
            points.append(SlaveSliderPoint(self, (i + 1) / (n_points - 1), color=color,
                                           size=small_size, show=show))
        points.append(self.master_pts[1])

        super().__init__(name, points, width=width, size=size,
                         small_size=small_size, color=color, text=text,
                         show=show, allow_delete=allow_delete,
                         allow_translate=allow_translate, allow_edit=allow_edit)

    def _get_direc(self):
        return self.master_pts[1] - self.master_pts[0]

    def update_coords(self):
        new_coords = super().update_coords()

        # also update sliders
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

    def as_dict(self):
        data = super().as_dict()

        v = [self.anchor.get_v(point.canvas_coords) for point in self.master_pts]
        data.update({'v': v})

        return data
