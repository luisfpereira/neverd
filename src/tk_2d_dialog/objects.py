from abc import ABCMeta
from abc import abstractmethod

import tkinter as tk

from tk_2d_dialog.widgets import CanvasPopupMenu
from tk_2d_dialog.widgets import ObjectPopupMenu
from tk_2d_dialog.utils import flatten_list


class Canvas:

    def __init__(self, holder, calibration, image=None, width=800,
                 height=800, **canvas_kwargs):
        # TODO: inherit from tk?
        self.holder = holder
        self.calibration = calibration
        self.image = image or _NoneWidget(show=True)
        self.width = width
        self.height = height
        self.drawing_canvas = self._create_drawing_canvas(**canvas_kwargs)
        self.objects = {}
        self.popup_menu = CanvasPopupMenu(self)

        # update drawing canvas
        self.calibration.update_canvas(self)
        self.image.update_canvas(self)

        # TODO: create calibration and image widgets

    def _create_drawing_canvas(self, **canvas_kwargs):
        drawing_canvas = tk.Canvas(self.holder, width=self.width,
                                   height=self.height, **canvas_kwargs)
        drawing_canvas.pack()
        return drawing_canvas

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
        self.canvas.drawing_canvas.itemconfigure(self.id, state='hidden')

    def show(self):
        self._show = True
        self.canvas.drawing_canvas.itemconfigure(self.id, state='normal')

    def update_canvas(self, canvas):
        self.canvas = canvas

    def create_widget(self):
        pass


class _NoneWidget(_BaseWidget):
    pass


class _BaseObject(_BaseWidget, metaclass=ABCMeta):

    def __init__(self, name, text, show):
        super().__init__(show)
        self.name = name
        self.text = text

    def show_text(self):
        pass

    def _config_bindings(self):
        self.canvas.drawing_canvas.tag_bind(self.id, '<Button-1>',
                                            self.on_config_delta_mov)
        self.canvas.drawing_canvas.tag_bind(self.id, '<B1-Motion>',
                                            self.on_translate)
        self.canvas.drawing_canvas.tag_bind(self.id, '<ButtonRelease-1>',
                                            self.on_update_coords)

        self.canvas.drawing_canvas.tag_bind(self.id, '<Button-2>')

        self.canvas.drawing_canvas.tag_bind(self.id, '<Enter>', self.on_enter)
        self.canvas.drawing_canvas.tag_bind(self.id, '<Leave>', self.on_leave)

    def _on_widget_creation(self):
        self._config_bindings()
        self._create_popup_menu()

    def on_translate(self, event):
        x, y = event.x - self._delta[0], event.y - self._delta[1]
        self.canvas.drawing_canvas.moveto(self.id, x, y)

    @abstractmethod
    def on_update_coords(self, *args):
        pass

    def on_config_delta_mov(self, event):
        x, y = self._get_ref_point()
        self._delta = (event.x - x, event.y - y)

    @abstractmethod
    def _get_ref_point(self):
        pass

    def destroy(self):
        self.popup_menu.destroy()
        self.canvas.drawing_canvas.delete(self.id)

    def _create_popup_menu(self):
        self.popup_menu = ObjectPopupMenu(self)

    def on_enter(self, *args):
        self.canvas.popup_menu.unbind_menu_trigger()

    def on_leave(self, *args):
        self.canvas.popup_menu.bind_menu_trigger()


class CalibrationPoint:

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

    def __init__(self, name, coords, color='blue', size=5, text='', show=True):
        super().__init__(name, text, show)
        self.coords = coords
        self.color = color
        self.size = size

    def _get_ref_point(self):
        x, y = self.canvas.map2canvas(self.coords)
        return x - self.size, y - self.size

    def _get_center_from_canvas(self):
        x, y, *_ = self.canvas.drawing_canvas.coords(self.id)
        return x + self.size, y + self.size

    def _get_rect_corners(self):
        # in canvas coordinates
        x, y = self.canvas.map2canvas(self.coords)
        r = self.size
        x0, y0 = x - r, y - r
        x1, y1 = x + r, y + r

        return (x0, y0), (x1, y1)

    def create_widget(self):
        (x0, y0), (x1, y1) = self._get_rect_corners()

        self.id = self.canvas.drawing_canvas.create_oval(
            x0, y0, x1, y1, fill=self.color, outline="")

        return self.id

    def on_update_coords(self, *args):
        x0, y0, *_ = self.canvas.drawing_canvas.coords(self.id)
        self.coords = self.canvas.map2real((x0 + self.size, y0 + self.size))

    def translate_to(self, x_center, y_center):
        x, y = x_center - self.size, y_center - self.size
        self.canvas.drawing_canvas.moveto(self.id, x, y)


class LinePoint(Point):
    # TODO: delete should not be allowed

    def __init__(self, line, coords, color='blue', size=5, show=True):
        super().__init__(show, coords, color=color, size=size, text='',
                         show=show)
        self.line = line

    @property
    def canvas(self):
        return self.line.canvas

    @canvas.setter
    def canvas(self, *args):
        pass

    def on_translate(self, event):
        super().on_translate(event)
        new_coords = [point._get_center_from_canvas() for point in self.line.points]
        self.canvas.drawing_canvas.coords(self.line.id, flatten_list(new_coords))


class Line(_BaseObject):
    # TODO: hide points in popup menu

    def __init__(self, name, points, width=1, size=5, color='red',
                 text='', show=True):
        super().__init__(name, text, show)
        self.points = [LinePoint(self, coords, color=color, size=size, show=show)
                       for coords in points]
        self.color = color
        self.width = width

    def _get_ref_point(self):
        return self.canvas.map2canvas(self.points[0].coords)
        # TODO: depends on the clicked segment

    def create_widget(self):

        # create line
        coords = [self.canvas.map2canvas(point.coords) for point in self.points]

        self.id = self.canvas.drawing_canvas.create_line(
            flatten_list(coords), fill=self.color, width=self.width)

        # create points
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

    def on_translate(self, event):
        super().on_translate(event)
        coords = self.canvas.drawing_canvas.coords(self.id)
        for point, c1, c2 in zip(self.points, coords[::2], coords[1::2]):
            point.translate_to(c1, c2)

    def on_update_coords(self, *args):
        for point in self.points:
            point.on_update_coords()


class Slider(_BaseObject):
    # TODO: shared behavior with line?

    def __init__(self, name, text, anchor, pt_init, pt_end, n_points, width=3,
                 color='green', show=True):
        super().__init__(name, text, show)
        self.anchor = anchor
        self.pt_init = pt_init
        self.pt_end = pt_end
        self.n_points = n_points
        self.width = width
        self.color = color

    def _get_ref_point(self):
        return self.canvas.map2canvas(self.pt_init)
