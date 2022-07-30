from urllib.parse import urlparse
from dataclasses import dataclass


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
            print(f"URL: {self.url}")
            print(f"DB: {self.db}")


# Settings singleton
settings = Settings()
