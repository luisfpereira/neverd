
import platform
import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):

    def __init__(self, holder, width=100, height=100, fixed_width=False,
                 fixed_height=False):
        self._sys = platform.system()
        self.width = width
        self.height = height
        self.fixed_width = fixed_width
        self.fixed_height = fixed_height
        self.scrollbar_y = None
        self.scrollbar_x = None

        canvas_holder = ttk.Frame(holder)
        canvas_holder.pack()

        self.canvas = tk.Canvas(canvas_holder)
        self.canvas.grid(row=0, column=0, sticky="news")

        super().__init__(self.canvas)

        self.bind("<Configure>", self.on_frame_configure)
        self.canvas.create_window((0, 0), window=self,
                                  anchor="nw")

    def _activate_scrollbar_y(self):
        if self.scrollbar_y is not None:
            return

        self.scrollbar_y = ttk.Scrollbar(self.canvas.master, orient='vertical',
                                         command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self._bind_scroll_y_activation()

    def _deactivate_scrollbar_y(self):
        if self.scrollbar_y is None:
            return

        self.scrollbar_y.destroy()
        self.scrollbar_y = None

    def _activate_scrollbar_x(self):
        if self.scrollbar_x is not None:
            return

        self.scrollbar_x = ttk.Scrollbar(self.canvas.master, orient="horizontal",
                                         command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar_x.grid(row=1, column=0, sticky="we")
        self._bind_scroll_x_activation()

    def _deactivate_scrollbar_x(self):
        if self.scrollbar_x is None:
            return

        self.scrollbar_x.destroy()
        self.scrollbar_x = None

    def _bind_scroll_y_activation(self):
        self.canvas.bind('<Enter>', self._bind_scroll_y, add='+')
        self.canvas.bind('<Leave>', self._unbind_scroll_y, add='+')

    def _bind_scroll_x_activation(self):
        self.canvas.bind('<Enter>', self._bind_scroll_x, add='+')
        self.canvas.bind('<Leave>', self._unbind_scroll_x, add='+')

    def _bind_scroll_y(self, *args):
        if self._sys == 'Linux':
            self.canvas.bind_all("<4>", self.on_mouse_wheel)
            self.canvas.bind_all("<5>", self.on_mouse_wheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def _unbind_scroll_y(self, *args):
        if self._sys == 'Linux':
            self.canvas.unbind_all("<4>")
            self.canvas.unbind_all("<5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")

    def _bind_scroll_x(self, *args):
        if self._sys == 'Linux':
            self.canvas.bind_all("<Shift-Button-4>", self.on_shift_mouse_wheel)
            self.canvas.bind_all("<Shift-Button-5>", self.on_shift_mouse_wheel)
        else:
            self.canvas.bind_all("<Shift-MouseWheel>", self.on_shift_mouse_wheel)

    def _unbind_scroll_x(self, *args):
        if self._sys == 'Linux':
            self.canvas.unbind_all("<Shift-Button-4>")
            self.canvas.unbind_all("<Shift-Button-5>")
        else:
            self.canvas.unbind_all("<Shift-MouseWheel>")

    def _get_delta(self, event):
        delta = -1 * event.delta if self._sys != 'Linux' else -1
        if self._sys == 'Windows':
            delta /= 120

        if self._sys == 'Linux' and event.num == 5:
            delta *= -1

        return delta

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(self._get_delta(event), "units")

    def on_shift_mouse_wheel(self, event):
        self.canvas.xview_scroll(self._get_delta(event), "units")

    def on_frame_configure(self, event):
        scroll_y = event.height > self.height or self.fixed_height
        scroll_x = event.width > self.width or self.fixed_width

        height = self.height if scroll_y else event.height
        width = self.width if scroll_x else event.width

        self.canvas.configure(height=height, width=width,
                              scrollregion=self.canvas.bbox("all"))

        if scroll_y:
            self._activate_scrollbar_y()
        else:
            self._deactivate_scrollbar_y()

        if scroll_x:
            self._activate_scrollbar_x()
        else:
            self._deactivate_scrollbar_x()
