import os
import subprocess
from collections import namedtuple

from .config import settings
from .console import console

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
        console.log(f"COMMAND: {cmd}")

    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, shell=True
    ) as p:
        stdout, stderr = p.communicate()

        if settings.debug:
            console.log("STDOUT:\n", stdout.decode("utf-8"), "\n")
            console.log("STDERR:\n", stderr.decode("utf-8"), "\n")

        return Result(
            returncode=p.returncode,
            stdout=stdout.decode("utf-8"),
            stderr=stderr.decode("utf-8"),
        )
