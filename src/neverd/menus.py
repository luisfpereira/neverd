
import json
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

from neverd.utils import get_menubar
from neverd.helpers import update_canvas_from_dict


class FileMenu(tk.Menu):

    def __init__(self, root, canvas, filename=None, label='File', **kwargs):
        menubar = get_menubar(root)
        self.filename = filename
        self.canvas = canvas
        self.root = root

        super().__init__(menubar, tearoff=0, **kwargs)
        menubar.add_cascade(label=label, menu=self)

        self._add_items()

    def _add_items(self):
        self.add_command(label='Save', command=self.on_save)
        self.add_command(label='Save as...', command=self.on_save_as)
        self.add_command(label='Load', command=self.on_load)
        self.add_separator()
        self.add_command(label='Exit', command=self.on_exit)

    def _save(self):
        self.canvas.dump(self.filename)

    def on_save(self):
        if self.filename is None:
            self.on_save_as()
        else:
            self._save()

    def on_save_as(self):
        filename = filedialog.asksaveasfilename(defaultextension='.json')

        if filename == '':
            return

        self.filename = filename
        self._save()

        return filename

    def on_load(self):
        filename = filedialog.askopenfilename(title="Load file",
                                              filetypes=(('json files', '.json'),))

        if filename == '':
            return

        self.canvas.clear()

        with open(filename, 'r') as file:
            data = json.load(file)

        self.filename = filename
        update_canvas_from_dict(self.canvas, data)

    def on_exit(self):
        save = messagebox.askyesno('Save before exiting',
                                   'Save changes before exit?')

        if save:
            self.on_save()

        self.root.quit()
