from collections import namedtuple
from datetime import datetime
from typing import List, Optional

try:
    from psycopg import sql
except ImportError:
    from psycopg2 import sql

from .config import settings
from .runner import exec_shell, exec_sql

################################################################################
# Database operations
################################################################################


def kill_connections(dbname: str):
    """
    Kills all connections to the given database
    """
    exec_sql(
        "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity "
        "WHERE pg_stat_activity.datname = %s",
        [dbname],
    )


def create_database(*, dbname: str, template: Optional[str] = None):
    """
    Creates a new database with the given name, optionally using the given template
    """
    if template:
        exec_sql(
            sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(
                sql.Identifier(dbname),
                sql.Identifier(template),
            )
        )
    else:
        exec_sql(
            sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(dbname),
            )
        )


def drop_database(dbname: str):
    """
    Drops the given database
    """
    exec_sql(sql.SQL("DROP DATABASE {}").format(sql.Identifier(dbname)))


################################################################################
# Snapshot operations
################################################################################

Snapshot = namedtuple("Snapshot", ["dbname", "name", "created_at", "size"])


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


def get_snapshots() -> List[Snapshot]:
    """
    Returns the list of database snapshots

    Snapshots are databases that follow the naming convention:

    dslr_<timestamp>_<snapshot_name>
    """
    # Find the snapshot databases
    result = exec_sql(
        """
        SELECT
            datname,
            pg_size_pretty(pg_database_size(datname))
        FROM pg_database
        WHERE datname LIKE 'dslr_%'
        """
    )

    if result is None:
        raise RuntimeError("Did not get results from database.")

    return [
        Snapshot(
            dbname=line,
            name="_".join(part[2:]),
            created_at=datetime.fromtimestamp(int(part[1])),
            size=size,
        )
        for line, part, size in [(row[0], row[0].split("_"), row[1]) for row in result]
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
    """
    kill_connections(settings.db.name)
    create_database(
        dbname=generate_snapshot_db_name(snapshot_name), template=settings.db.name
    )


def delete_snapshot(snapshot: Snapshot):
    """
    Deletes the given snapshot
    """
    drop_database(snapshot.dbname)


def restore_snapshot(snapshot: Snapshot):
    """
    Restores the database from the given snapshot
    """
    kill_connections(settings.db.name)
    drop_database(settings.db.name)
    create_database(dbname=settings.db.name, template=snapshot.dbname)


def rename_snapshot(snapshot: Snapshot, new_name: str):
    """
    Renames the given snapshot
    """
    exec_sql(
        sql.SQL("ALTER DATABASE {} RENAME TO {}").format(
            sql.Identifier(snapshot.dbname),
            sql.Identifier(generate_snapshot_db_name(new_name, snapshot.created_at)),
        )
    )


def export_snapshot(snapshot: Snapshot) -> str:
    """
    Exports the given snapshot to a file
    """
    export_path = f"{snapshot.name}_{snapshot.created_at:%Y%m%d-%H%M%S}.dump"
    exec_shell("pg_dump", "-Fc", "-d", snapshot.dbname, "-f", export_path)

    return export_path


def import_snapshot(import_path: str, snapshot_name: str):
    """
    Imports the given snapshot from a file
    """
    dbname = generate_snapshot_db_name(snapshot_name)
    create_database(dbname=dbname)

    exec_shell("pg_restore", "-d", dbname, "--no-acl", "--no-owner", import_path)
