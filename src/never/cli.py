
import tkinter as tk

import click


@click.group()
def main_cli():
    pass


@click.command()
@click.option("--filename", '-f', nargs=1, type=str, default=None)
def gui(filename):
    from never.helpers import load_from_json
    from never.helpers import load_from_dict

    if filename is None:
        load_from_dict({})
    else:
        load_from_json(filename)
    tk.mainloop()


main_cli.add_command(gui)
