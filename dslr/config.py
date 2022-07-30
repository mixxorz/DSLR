from dataclasses import dataclass
from urllib.parse import urlparse

from .console import console


@dataclass
class DatabaseConnection:
    host: str
    port: int
    username: str
    password: str
    name: str


class Settings:
    url: str
    debug: bool

    db: DatabaseConnection

    def initialize(self, *, url: str, debug: bool):
        self.url = url
        self.debug = debug

        parsed = urlparse(url)

        self.db = DatabaseConnection(
            host=parsed.hostname or "",
            port=parsed.port or 5432,
            username=parsed.username or "",
            password=parsed.password or "",
            name=parsed.path[1:],
        )

        if debug:
            console.log(f"URL: {self.url}")
            console.log(f"DB: {self.db}")


# Settings singleton
settings = Settings()
