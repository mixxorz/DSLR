import os
import subprocess
from collections import namedtuple
from typing import Any, List, Optional, Tuple, Union

try:
    from psycopg import sql
except ImportError:
    from psycopg2 import sql

from dslr.pg_client import PGClient

from .config import settings
from .console import console

Result = namedtuple("Result", ["stdout", "stderr"])


def exec_shell(*cmd: str) -> Result:
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
        console.log(f"COMMAND: {cmd}")

    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    ) as p:
        stdout, stderr = p.communicate()

        if settings.debug:
            console.log("STDOUT:\n", stdout.decode("utf-8"), "\n")
            console.log("STDERR:\n", stderr.decode("utf-8"), "\n")

        if p.returncode != 0:
            raise RuntimeError(f"Command failed: {cmd}")

        return Result(
            stdout=stdout.decode("utf-8"),
            stderr=stderr.decode("utf-8"),
        )


# Singleton instance of PGClient
pg_client: Optional[PGClient] = None


def exec_sql(
    sql: Union[sql.Composed, str], data: Optional[List[Any]] = None
) -> Optional[List[Tuple[Any, ...]]]:
    """
    Executes a SQL query.
    """
    global pg_client

    if not pg_client:
        # We always want to connect to the `postgres` and not the target
        # database because none of our operations need to query the target
        # database.
        pg_client = PGClient(
            host=settings.db.host,
            port=settings.db.port,
            user=settings.db.username,
            password=settings.db.password,
            dbname="postgres",
        )

    return pg_client.execute(sql, data)
