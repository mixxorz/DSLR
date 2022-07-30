import sys
from datetime import datetime

import click

from .config import settings
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
        create_snapshot(name)
    except DSLRException as e:
        click.echo(click.style("Failed to create snapshot", fg="red"), err=True)
        click.echo(str(e), err=True)
        sys.exit(1)

    click.echo(click.style("Snapshot created", fg="green"))


@cli.command()
def restore():
    pass


@cli.command()
def list():
    snapshots = get_snapshots()

    if len(snapshots) == 0:
        click.echo(click.style("No snapshots found", fg="yellow"))
        return

    for snapshot in snapshots:
        click.echo(
            f'{datetime.fromtimestamp(snapshot.timestamp).strftime("%Y-%m-%d %H:%M:%S")} '
            + click.style(f"{snapshot.name}", fg="cyan")
        )
