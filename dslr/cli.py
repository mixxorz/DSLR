import os
import sys

import click
import timeago
import tomli
from rich import box
from rich.table import Table

from .config import settings
from .console import console, cprint, eprint
from .operations import (
    SnapshotNotFound,
    create_snapshot,
    delete_snapshot,
    export_snapshot,
    find_snapshot,
    get_snapshots,
    import_snapshot,
    rename_snapshot,
    restore_snapshot,
)


def complete_snapshot_names(ctx, param, incomplete):
    """
    Returns a list of snapshot names for completion
    """
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        settings.initialize(url=db_url, debug=False)
        return [
            snapshot.name
            for snapshot in get_snapshots()
            if snapshot.name.startswith(incomplete)
        ]

    return []


def next_not_none(iterable):
    """
    Returns the next item in the iterable that is not None or ""
    """
    return next((item for item in iterable if item is not None and item != ""), None)


@click.group
@click.option(
    "--url",
    help="The database connection string to the database you want to take "
    "snapshots of."
    "\n\nExample: postgres://username:password@host:port/database_name",
)
@click.option("--debug/--no-debug", help="Show additional debugging information.")
def cli(url, debug):
    toml_params = {}
    try:
        with open("dslr.toml", "rb") as tomlf:
            toml_params = tomli.load(tomlf)
    except FileNotFoundError:
        pass

    config = {
        "url": next_not_none(
            [url, toml_params.get("url"), os.environ.get("DATABASE_URL")]
        )
        or "",
        "debug": next_not_none([debug, toml_params.get("debug"), False]),
    }

    # Update the settings singleton
    settings.initialize(**config)


@cli.command()
@click.argument("name", shell_complete=complete_snapshot_names)
@click.option(
    "-y",
    "--yes",
    "overwrite_confirmed",
    is_flag=True,
    help="Overwrite existing snapshot without confirmation.",
)
def snapshot(name: str, overwrite_confirmed: bool):
    """
    Takes a snapshot of the database
    """
    new = True

    try:
        snapshot = find_snapshot(name)

        if not overwrite_confirmed:
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
    except Exception as e:
        eprint("Failed to create snapshot")
        eprint(e, style="white")
        sys.exit(1)

    if new:
        cprint(f"Created new snapshot {name}", style="green")
    else:
        cprint(f"Updated snapshot {name}", style="green")


@cli.command()
@click.argument("name", shell_complete=complete_snapshot_names)
def restore(name):
    """
    Restores the database from a snapshot
    """
    try:
        snapshot = find_snapshot(name)
    except SnapshotNotFound:
        eprint(f"Snapshot {name} does not exist", style="red")
        sys.exit(1)

    with console.status("Restoring snapshot"):
        try:
            restore_snapshot(snapshot)
        except Exception as e:
            eprint("Failed to restore snapshot")
            eprint(e, style="white")
            sys.exit(1)

    cprint(f"Restored database from snapshot {snapshot.name}", style="green")


@cli.command()
def list():
    """
    Shows a list of all snapshots
    """
    try:
        snapshots = get_snapshots()
    except Exception as e:
        eprint("Failed to list snapshots")
        eprint(f"{e}", style="white")
        sys.exit(1)

    if len(snapshots) == 0:
        cprint("No snapshots found", style="yellow")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("Name", style="cyan")
    table.add_column("Created")
    table.add_column("Size", justify="right")

    for snapshot in sorted(snapshots, key=lambda s: s.created_at, reverse=True):
        table.add_row(snapshot.name, timeago.format(snapshot.created_at), snapshot.size)

    cprint(table)


@cli.command()
@click.argument("name", shell_complete=complete_snapshot_names)
def delete(name):
    """
    Deletes a snapshot
    """
    try:
        snapshot = find_snapshot(name)
    except SnapshotNotFound:
        eprint(f"Snapshot {name} does not exist", style="red")
        sys.exit(1)

    try:
        delete_snapshot(snapshot)
    except Exception as e:
        eprint("Failed to delete snapshot")
        eprint(e, style="white")
        sys.exit(1)

    cprint(f"Deleted snapshot {snapshot.name}", style="green")


@cli.command()
@click.argument("old_name", shell_complete=complete_snapshot_names)
@click.argument("new_name", shell_complete=complete_snapshot_names)
@click.option(
    "-y",
    "--yes",
    "overwrite_confirmed",
    is_flag=True,
    help="Overwrite existing snapshot without confirmation.",
)
def rename(old_name: str, new_name: str, overwrite_confirmed: bool):
    """
    Renames a snapshot
    """
    try:
        old_snapshot = find_snapshot(old_name)
    except SnapshotNotFound:
        eprint(f"Snapshot {old_name} does not exist", style="red")
        sys.exit(1)

    try:
        existing_snapshot = find_snapshot(new_name)

        if not overwrite_confirmed:
            click.confirm(
                click.style(
                    f"Snapshot {existing_snapshot.name} already exists. Overwrite?",
                    fg="yellow",
                ),
                abort=True,
            )

        delete_snapshot(existing_snapshot)
    except SnapshotNotFound:
        pass

    try:
        rename_snapshot(old_snapshot, new_name)
    except Exception as e:
        eprint("Failed to rename snapshot")
        eprint(e, style="white")
        sys.exit(1)

    cprint(f"Renamed snapshot {old_name} to {new_name}", style="green")


@cli.command()
@click.argument("name", shell_complete=complete_snapshot_names)
def export(name):
    """
    Exports a snapshot to a file
    """
    try:
        snapshot = find_snapshot(name)
    except SnapshotNotFound:
        eprint(f"Snapshot {name} does not exist", style="red")
        sys.exit(1)

    try:
        with console.status("Exporting snapshot"):
            export_path = export_snapshot(snapshot)
    except Exception as e:
        eprint("Failed to export snapshot")
        eprint(e, style="white")
        sys.exit(1)

    cprint(f"Exported snapshot {snapshot.name} to {export_path}", style="green")


@cli.command("import")
@click.argument("filename", type=click.Path(exists=True))
@click.argument("name", shell_complete=complete_snapshot_names)
@click.option(
    "-y",
    "--yes",
    "overwrite_confirmed",
    is_flag=True,
    help="Overwrite existing snapshot without confirmation.",
)
def import_(filename: str, name: str, overwrite_confirmed):
    """
    Imports a snapshot from a file
    """
    filename = click.format_filename(filename)

    try:
        snapshot = find_snapshot(name)

        if not overwrite_confirmed:
            click.confirm(
                click.style(
                    f"Snapshot {snapshot.name} already exists. Overwrite?", fg="yellow"
                ),
                abort=True,
            )

        delete_snapshot(snapshot)
    except SnapshotNotFound:
        pass

    try:
        with console.status("Importing snapshot"):
            import_snapshot(filename, name)
    except Exception as e:
        eprint("Failed to import snapshot")
        eprint(e, style="white")
        sys.exit(1)

    cprint(f"Imported snapshot {name} from {filename}", style="green")
