
import tkinter as tk

import click


@click.group()
def main_cli():
    pass


@click.command()
@click.option("--filename", '-f', nargs=1, type=str, default=None)
def gui(filename):
    from neverd.helpers import load_from_json
    from neverd.helpers import load_from_dict
    from neverd.app import App

    root = tk.Tk()

    if filename is None:
        canvas = load_from_dict({}, holder=root)
    else:
        canvas = load_from_json(filename, holder=root)

    App(root, canvas, filename=filename)

    tk.mainloop()


main_cli.add_command(gui)
