import sys
from datetime import datetime

import click

from .config import settings
from .console import console, cprint, eprint
from .operations import DSLRException, create_snapshot, get_snapshots


@click.group
@click.option("--db", envvar="DATABASE_URL", required=True)
@click.option("--debug/--no-debug")
def cli(db, debug):
    # Update the settings singleton
    settings.initialize(url=db, debug=debug)


@cli.command()
@click.argument("name")
def snapshot(name: str):
    try:
        with console.status("Creating snapshot"):
            create_snapshot(name)
    except DSLRException as e:
        eprint("Failed to create snapshot")
        eprint(e, style="white")
        sys.exit(1)

    cprint("Snapshot created", style="green")


@cli.command()
def restore():
    pass


@cli.command()
def list():
    try:
        snapshots = get_snapshots()
    except DSLRException as e:
        eprint("Failed to list snapshots")
        eprint(f"{e}", style="white")
        sys.exit(1)

    if len(snapshots) == 0:
        cprint("No snapshots found", style="yellow")
        return

    for snapshot in snapshots:
        click.echo(
            f'{datetime.fromtimestamp(snapshot.timestamp).strftime("%Y-%m-%d %H:%M:%S")} '
            + click.style(f"{snapshot.name}", fg="cyan")
        )
