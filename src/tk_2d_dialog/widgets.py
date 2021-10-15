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
        self._config_bindings()
        self.bind_menu_trigger()

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
        self.preferred_order = self._define_preferred_order()
        super().__init__(self.object.canvas,
                         tearoff=0)

    def _define_preferred_order(self):
        return ['Show/hide', 'Edit', 'Delete']

    def _get_placement_index(self, label):
        index = self.preferred_order.index(label)
        for label in self.preferred_order[:index]:
            if not self.has_item(label):
                index -= 1

        return index

    def _unbind_menu_trigger(self, obj):
        self.object.canvas.tag_unbind(obj.id, '<Button-2>')

    def _bind_menu_trigger(self, obj):
        self.object.canvas.tag_bind(obj.id, '<Button-2>',
                                    self.on_popup_menu_trigger, add='+')

    def unbind_menu_trigger(self):
        for obj in [self.object] + self.triggerers:
            self._unbind_menu_trigger(obj)

    def bind_menu_trigger(self):
        for obj in [self.object] + self.triggerers:
            self._bind_menu_trigger(obj)

    def _bind_item(self, label, command):
        # TODO: move parent?
        if not self.has_item(label):
            if label in self.preferred_order:
                index = self._get_placement_index(label)
                self.insert_command(index=index, label=label,
                                    command=command)
            else:
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


class LinePopupMenu(ObjectPopupMenu):

    def _config_bindings(self):
        super()._config_bindings()

        self.bind_store_click_position()

        if self.object.allow_edit:
            self.bind_add_point()
            self._bind_item('Refine', self.on_refine)
            self.bind_add_slider()

    def _define_preferred_order(self):
        order = super()._define_preferred_order()
        order.extend(['Refine',
                      'Add point',
                      'Remove point',
                      'Add slider'])
        return order

    def bind_store_click_position(self):
        self.object.canvas.tag_bind(self.object.id, '<Button-2>',
                                    self.on_store_click_position, add='+')

    def bind_trigger(self, obj):
        # avoid addition of overlapped point
        self.object.canvas.tag_bind(obj.id, '<Enter>',
                                    self.unbind_add_point, add='+')
        self.object.canvas.tag_bind(obj.id, '<Leave>',
                                    self.bind_add_point, add='+')

        # hide remove point if not point
        self.object.canvas.tag_bind(obj.id, '<Enter>',
                                    lambda e, point=obj: self.bind_remove_point(point, e), add='+')
        self.object.canvas.tag_bind(obj.id, '<Leave>',
                                    self.unbind_remove_point, add='+')

    def add_triggerer(self, obj):
        super().add_triggerer(obj)
        self.bind_trigger(obj)

    def unbind_edit(self):
        super().unbind_edit()
        self._unbind_item('Add slider')
        self._unbind_add_point()
        self._unbind_item('Refine')

    def bind_add_point(self, *args):
        self._bind_item('Add point', self.on_add_point)

    def unbind_add_point(self, *args):
        self._unbind_item('Add point')

    def bind_add_slider(self):
        self._bind_item('Add slider', self.on_add_slider)

    def bind_remove_point(self, point, *args):
        self._bind_item('Remove point',
                        lambda point=point: self.on_remove_point(point))

    def unbind_remove_point(self, *args):
        self._unbind_item('Remove point')

    def on_add_slider(self):
        SliderForm(self.object.canvas, line_names=[self.object.name])

    def on_add_point(self):
        coords = (self._x, self._y)
        new_coords = self.object.find_closest_point(coords)
        self.object.add_point(new_coords)

    def on_refine(self):
        coords = self.object.canvas_coords
        for coords1, coords2 in zip(coords, coords[1::]):
            new_coords = (coords2 + coords1) / 2
            self.object.add_point(new_coords)

    def on_remove_point(self, point):
        self.object.remove_point(point)
        self.unbind_remove_point()
        self.bind_add_point()

    def on_store_click_position(self, event):
        self._x = event.x
        self._y = event.y


class SliderPopupMenu(ObjectPopupMenu):

    def _config_bindings(self):
        super()._config_bindings()

        if self.object.allow_edit:
            self.bind_refine()

    def _define_preferred_order(self):
        order = super()._define_preferred_order()
        order.extend(['Refine', 'Coarse'])
        return order

    def bind_refine(self):
        self._bind_item('Refine', self.on_refine)
        self._bind_item('Coarse', self.on_coarse)

    def unbind_edit(self):
        super().unbind_edit()
        self._unbind_item('Refine')
        self._unbind_item('Coarse')

    def on_refine(self):
        self.object.n_points = self.object.n_points + 1

    def on_coarse(self):
        self.object.n_points = self.object.n_points - 1


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
