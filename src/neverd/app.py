

from neverd.menus import FileMenu


class App():

    def __init__(self, root, canvas, filename=None):
        self.root = root
        self.canvas = canvas
        self.filename = filename

        self._create_menubar()

    def _create_menubar(self):
        FileMenu(self.root, self.canvas, filename=self.filename)
