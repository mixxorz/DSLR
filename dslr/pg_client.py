from typing import Any, List, Optional, Tuple

import psycopg2

from dslr.console import console

from .config import settings


class PGClient:
    """
    Thin wrapper around psycopg2
    """

    def __init__(self, host, port, user, password, dbname):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname

        self.conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
        )
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        self.cur = self.conn.cursor()

    def execute(self, sql, data) -> Optional[List[Tuple[Any, ...]]]:
        if settings.debug:
            console.log(f"SQL: {sql}")
            console.log(f"DATA: {data}")

        self.cur.execute(sql, data)

        try:
            result = self.cur.fetchall()
        except psycopg2.ProgrammingError:
            result = None

        return result
