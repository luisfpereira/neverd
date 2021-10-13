from abc import ABCMeta
from abc import abstractmethod
import tkinter as tk

from tk_2d_dialog.forms import OBJ2FORM
from tk_2d_dialog.forms import PointForm
from tk_2d_dialog.forms import LineForm
from tk_2d_dialog.forms import SliderForm


class _BasePopupMenu(tk.Menu, metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind_menu_trigger()
        self._config_bindings()

    def unbind_menu_trigger(self):
        self.master.unbind('<Button-2>')

    def bind_menu_trigger(self):
        self.master.bind('<Button-2>',
                         self.on_popup_menu_trigger)

    def on_popup_menu_trigger(self, event):
        self.tk_popup(event.x_root, event.y_root)
        self.grab_release()

    @abstractmethod
    def _config_bindings(self):
        pass

    def has_item(self, item_label):
        try:
            self.index(item_label)
            return True
        except tk.TclError:
            return False


class CanvasPopupMenu(_BasePopupMenu):

    def __init__(self, canvas):
        self.canvas = canvas
        super().__init__(self.canvas,
                         tearoff=0)

    def _bind_right_click(self):
        """Binds right click.

        Notes:
            Trick to bind canvas again when object is deleted with a popup menu,
            without triggering it instantaneously.
        """
        self.canvas.bind('<Button-2>', self.on_right_click)

    def on_right_click(self, event=None):
        if self._binded is True:
            super().bind_menu_trigger()
            self.canvas.event_generate('<Button-2>',
                                       rootx=event.x_root,
                                       rooty=event.y_root)
        self._binded = True

    def unbind_menu_trigger(self):
        self._binded = False
        super().unbind_menu_trigger()

    def bind_menu_trigger(self):
        self._binded = True
        super().bind_menu_trigger()

    def _config_bindings(self):
        self.add_command(label='Show/hide calibration',
                         command=self.on_show_hide_cal)
        self.add_command(label='Show/hide image',
                         command=self.on_show_hide_img)
        self.add_command(label='Show all',
                         command=self.on_show_all)
        self.add_command(label='Hide all',
                         command=self.on_hide_all)
        self.add_command(label='Show objects properties',
                         command=self.on_show_objs_props)

        add_popup_menu = AddPopupMenu(self.canvas, tearoff=0)
        self.add_cascade(label='Add object', menu=add_popup_menu)

    def on_show_hide_cal(self, *args):
        if self.canvas.calibration._show:
            self.canvas.calibration.hide()
        else:
            self.canvas.calibration.show()

    def on_show_hide_img(self, *args):
        if self.canvas.image._show:
            self.canvas.image.hide()
        else:
            self.canvas.image.show()

    def on_show_all(self, *args):
        for obj in self.canvas.objects.values():
            obj.show()

    def on_hide_all(self, *args):
        for obj in self.canvas.objects.values():
            obj.hide()

    def on_show_objs_props(self, *args):
        print('Show obj properties')
        # TODO
        pass


class ObjectPopupMenu(_BasePopupMenu):

    def __init__(self, obj):
        self.object = obj
        self.triggerers = []
        super().__init__(self.object.canvas,
                         tearoff=0)

    def _unbind_menu_trigger(self, obj):
        self.object.canvas.tag_unbind(obj.id, '<Button-2>')

    def _bind_menu_trigger(self, obj):
        self.object.canvas.tag_bind(obj.id, '<Button-2>',
                                    self.on_popup_menu_trigger)

    def unbind_menu_trigger(self):
        for obj in [self.object] + self.triggerers:
            self._unbind_menu_trigger(obj)

    def bind_menu_trigger(self):
        for obj in [self.object] + self.triggerers:
            self._bind_menu_trigger(obj)

    def _bind_item(self, label, command):
        if not self.has_item(label):
            self.add_command(label=label, command=command)

    def _unbind_item(self, label):
        if self.has_item(label):
            self.delete(label)

    def bind_delete(self):
        self._bind_item('Delete', self.on_delete)

    def unbind_delete(self):
        self._unbind_item('Delete')

    def bind_edit(self):
        self._bind_item('Edit', self.on_edit)

    def unbind_edit(self):
        self._unbind_item('Edit')

    def _config_bindings(self):
        self.add_command(label='Show/hide', command=self.on_show_hide)

        if self.object.allow_edit:
            self.bind_edit()

        if self.object.allow_delete:
            self.bind_delete()

    def on_show_hide(self, *args):
        if self.object._show:
            self.object.hide()
        else:
            self.object.show()

    def on_delete(self, *args):
        self.object.canvas.delete_object(self.object.id)
        self.object.canvas.popup_menu._bind_right_click()

    def add_triggerer(self, obj):
        self.triggerers.append(obj)
        self._bind_menu_trigger(obj)

    def remove_triggerer(self, obj):
        self.triggerers.remove(obj)
        self._unbind_menu_trigger(obj)

    def on_edit(self):
        OBJ2FORM.get(self.object.type, lambda *args, **kwargs: None)(self.object.canvas, obj=self.object)


class AddPopupMenu(tk.Menu):

    def __init__(self, canvas, *args, **kwargs):
        self.canvas = canvas
        super().__init__(canvas, *args, **kwargs)
        self._config_bindings()

    def _config_bindings(self):
        self.add_command(label='Point', command=self.on_add_point)
        self.add_command(label='Line', command=self.on_add_line)
        self.add_command(label='Slider', command=self.on_add_slider)

    def on_add_point(self):
        PointForm(self.canvas)

    def on_add_line(self):
        LineForm(self.canvas)

    def on_add_slider(self):
        SliderForm(self.canvas)


class ObjectPropertiesFrame:
    pass


class PointTreeview:
    pass


class LineTreeview:
    pass


class SliderTreeview:
    pass


class ColorDropDown:
    pass


class WidthDropDown:
    pass


class SizeDropDown:
    pass
