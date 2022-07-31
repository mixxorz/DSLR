from collections import namedtuple
from datetime import datetime
from typing import List, Optional

from .config import settings
from .runner import exec, exec_sql

Snapshot = namedtuple("Snapshot", ["dbname", "name", "created_at"])


class DSLRException(Exception):
    pass


def generate_snapshot_db_name(
    snapshot_name: str, created_at: Optional[datetime] = None
) -> str:
    """
    Generates a database name for a snapshot
    """
    if not created_at:
        created_at = datetime.now()

    timestamp = round(created_at.timestamp())

    return f"dslr_{timestamp}_{snapshot_name}"


def kill_connections(dbname: str):
    """
    Kills all connections to the given database
    """
    result = exec(
        "psql",
        "-d",
        "postgres",
        "-c",
        "SELECT pg_terminate_backend(pg_stat_activity.pid) "
        f"FROM pg_stat_activity WHERE pg_stat_activity.datname = '{dbname}'",
    )

    if result.returncode != 0:
        raise DSLRException(result.stderr)


def get_snapshots() -> List[Snapshot]:
    """
    Returns the list of database snapshots

    Snapshots are databases that follow the naming convention:

    dslr_<timestamp>_<snapshot_name>
    """
    # Find the snapshot databases
    result = exec_sql("SELECT datname FROM pg_database WHERE datname LIKE 'dslr_%'")

    snapshot_dbnames = sorted([row[0] for row in result])

    # Parse the name into a Snapshot
    parts = [dbname.split("_") for dbname in snapshot_dbnames]
    return [
        Snapshot(
            dbname=line,
            name="_".join(part[2:]),
            created_at=datetime.fromtimestamp(int(part[1])),
        )
        for part, line in zip(parts, snapshot_dbnames)
    ]


class SnapshotNotFound(Exception):
    pass


def find_snapshot(snapshot_name: str) -> Snapshot:
    """
    Returns the snapshot with the given name
    """
    snapshots = get_snapshots()

    try:
        return next(
            snapshot for snapshot in snapshots if snapshot.name == snapshot_name
        )
    except StopIteration as e:
        raise SnapshotNotFound(
            f'Snapshot with name "{snapshot_name}" does not exist.'
        ) from e


def create_snapshot(snapshot_name: str):
    """
    Takes a snapshot of the database

    Snapshotting works by creating a new database using the local database as a
    template.

        createdb -T source_db_name dslr_<timestamp>_<name>
    """
    kill_connections(settings.db.name)

    result = exec(
        "createdb", "-T", settings.db.name, generate_snapshot_db_name(snapshot_name)
    )

    if result.returncode != 0:
        raise DSLRException(result.stderr)


def delete_snapshot(snapshot: Snapshot):
    """
    Deletes the given snapshot
    """
    result = exec("dropdb", snapshot.dbname)

    if result.returncode != 0:
        raise DSLRException(result.stderr)


def restore_snapshot(snapshot: Snapshot):
    """
    Restores the database from the given snapshot
    """
    kill_connections(settings.db.name)

    result = exec("dropdb", settings.db.name)

    if result.returncode != 0:
        raise DSLRException(result.stderr)

    result = exec("createdb", "-T", snapshot.dbname, settings.db.name)

    if result.returncode != 0:
        raise DSLRException(result.stderr)


def rename_snapshot(snapshot: Snapshot, new_name: str):
    """
    Renames the given snapshot
    """
    result = exec(
        "psql",
        "-c",
        f'ALTER DATABASE "{snapshot.dbname}" RENAME TO '
        f'"{generate_snapshot_db_name(new_name, snapshot.created_at)}"',
    )

    if result.returncode != 0:
        raise DSLRException(result.stderr)


def export_snapshot(snapshot: Snapshot) -> str:
    """
    Exports the given snapshot to a file
    """
    export_path = f"{snapshot.name}_{snapshot.created_at:%Y%m%d-%H%M%S}.dump"
    result = exec("pg_dump", "-Fc", "-d", snapshot.dbname, "-f", export_path)

    if result.returncode != 0:
        raise DSLRException(result.stderr)

    return export_path


def import_snapshot(import_path: str, snapshot_name: str):
    """
    Imports the given snapshot from a file
    """
    db_name = generate_snapshot_db_name(snapshot_name)
    result = exec("createdb", db_name)

    if result.returncode != 0:
        raise DSLRException(result.stderr)

    result = exec("pg_restore", "-d", db_name, "--no-acl", "--no-owner", import_path)

    if result.returncode != 0:
        raise DSLRException(result.stderr)
