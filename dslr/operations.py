import os
import subprocess
from collections import namedtuple
from time import time
from typing import List

from .config import settings


Result = namedtuple("Result", ["returncode", "stdout", "stderr"])
Snapshot = namedtuple("Snapshot", ["dbname", "name", "timestamp"])


def exec(cmd: str) -> Result:
    """
    Executes a command.
    """

    # Set PG environment variables based on the settings
    env = os.environ.copy()
    env["PGHOST"] = settings.db.host or env.get("PGHOST", "")
    env["PGPORT"] = str(settings.db.port) or env.get("PGPORT", "")
    env["PGUSER"] = settings.db.username or env.get("PGUSER", "")
    env["PGPASSWORD"] = settings.db.password or env.get("PGPASSWORD", "")

    if settings.debug:
        print(f"COMMAND: {cmd}")

    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, shell=True
    ) as p:
        stdout, stderr = p.communicate()

        if settings.debug:
            print("STDOUT:\n", stdout.decode("utf-8"), "\n")
            print("STDERR:\n", stderr.decode("utf-8"), "\n")

        return Result(
            returncode=p.returncode,
            stdout=stdout.decode("utf-8"),
            stderr=stderr.decode("utf-8"),
        )


class DSLRException(Exception):
    pass


def get_snapshots() -> List[Snapshot]:
    """
    Returns the list of database snapshots

    Snapshots are databases that follow the naming convention:

    dslr_<timestamp>_<snapshot_name>
    """
    # Find the snapshot databases
    result = exec("psql -c 'SELECT datname FROM pg_database'")

    lines = sorted(
        [
            line.strip()
            for line in result.stdout.split("\n")
            if line.strip().startswith("dslr_")
        ]
    )

    # Parse the name into a Snapshot
    parts = [line.split("_") for line in lines]
    return [
        Snapshot(dbname=line, name="_".join(part[2:]), timestamp=int(part[1]))
        for part, line in zip(parts, lines)
    ]


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
        raise ValueError(f'Snapshot with name "{snapshot_name}" does not exist.') from e


def create_snapshot(snapshot_name: str):
    """
    Takes a snapshot of the database


    Snapshotting works by creating a new database using the local database as a
    template.

        createdb -T wagtailkit_repo_name dslr_<timestamp>_<name>
    """
    result = exec(
        f"createdb -T {settings.db.name} dslr_{round(time())}_{snapshot_name}"
    )

    if result.returncode != 0:
        raise DSLRException(result.stderr)
