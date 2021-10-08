import click


@click.group()
def main_cli():
    pass


@click.command()
@click.argument("filename", nargs=1)
def gui(filename):
    from tk_2d_dialog.main import main

    main(filename)


main_cli.add_command(gui)
