import sys

import click
import timeago
from rich import box
from rich.table import Table

from .config import settings
from .console import console, cprint, eprint
from .operations import (
    DSLRException,
    SnapshotNotFound,
    create_snapshot,
    delete_snapshot,
    find_snapshot,
    get_snapshots,
)


@click.group
@click.option("--db", envvar="DATABASE_URL", required=True)
@click.option("--debug/--no-debug")
def cli(db, debug):
    # Update the settings singleton
    settings.initialize(url=db, debug=debug)


@cli.command()
@click.argument("name")
def snapshot(name: str):
    new = True

    try:
        snapshot = find_snapshot(name)

        click.confirm(
            click.style(
                f"Snapshot {snapshot.name} already exists. Overwrite?", fg="yellow"
            ),
            abort=True,
        )

        delete_snapshot(snapshot)
        new = False

    except SnapshotNotFound:
        pass

    try:
        with console.status("Creating snapshot"):
            create_snapshot(name)
    except DSLRException as e:
        eprint("Failed to create snapshot")
        eprint(e, style="white")
        sys.exit(1)

    if new:
        cprint(f"Created new snapshot {name}", style="green")
    else:
        cprint(f"Updated snapshot {name}", style="green")


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

    table = Table(box=box.SIMPLE)
    table.add_column("Name", style="cyan")
    table.add_column("Created")

    for snapshot in sorted(snapshots, key=lambda s: s.created_at, reverse=True):
        table.add_row(snapshot.name, timeago.format(snapshot.created_at))

    cprint(table)
