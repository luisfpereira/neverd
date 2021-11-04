
import tkinter as tk

import click


@click.group()
def main_cli():
    pass


@click.command()
@click.argument("filename", nargs=1)
def gui(filename):
    from tk_2d_dialog.helpers import load_from_json

    load_from_json(filename)
    tk.mainloop()


main_cli.add_command(gui)
