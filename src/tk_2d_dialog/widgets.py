from abc import ABCMeta
from abc import abstractmethod
import tkinter as tk


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
        super().__init__(self.object.canvas,
                         tearoff=0)

    def unbind_menu_trigger(self):
        self.object.canvas.tag_bind(self.object.id, '<Button-2>')

    def bind_menu_trigger(self):
        self.object.canvas.tag_bind(self.object.id, '<Button-2>',
                                    self.on_popup_menu_trigger)

    def _config_bindings(self):
        self.add_command(label='Show/hide', command=self.on_show_hide)
        self.add_command(label='Delete', command=self.on_delete)

    def on_show_hide(self, *argss):
        if self.object._show:
            self.object.hide()
        else:
            self.object.show()

    def on_delete(self, *args):
        self.object.canvas.delete_object(self.object.id)

        # TODO: reactivate canvas popup
        self.object.canvas.popup_menu._bind_right_click()


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
