from typing import Any, List, Tuple

import psycopg2


class PGClient:
    """
    Thin wrapper around psycopg2
    """

    def __init__(self, host, port, user, password, dbname):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
        )
        self.cur = self.conn.cursor()

    def execute(self, sql, data) -> List[Tuple[Any, ...]]:
        self.cur.execute(sql, data)
        return self.cur.fetchall()
