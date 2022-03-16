

from neverd.objects import GeometricCanvas
from neverd.menus import DefaultMenubar


class App():

    def __init__(self, root, canvas=None, filename=None):
        self.root = root
        self.canvas = canvas or self._create_default_canvas(root)
        self.filename = filename

        self._create_menubar()

    def _create_default_canvas(self, holder):
        canvas = GeometricCanvas(holder)
        canvas.pack(fill='both', expand=True)
        return canvas

    def _create_menubar(self):
        menubar = DefaultMenubar(self.canvas)
        menubar.menus[0].filename = self.filename
        menubar.activate()
