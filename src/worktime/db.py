import sqlite3
from datetime import datetime, timedelta

from worktime.models import WorkTime

DEFAULT_DB_NAME = "worktime.db"


class Database:
    def __init__(self, name: str = DEFAULT_DB_NAME):
        self.name = name
        self._connection: sqlite3.Connection | None = None

    def create(self) -> None:
        con = sqlite3.connect(self.name)
        with con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS worktime (
                    id INTEGER PRIMARY KEY,
                    start DATETIME NOT NULL,
                    end DATETIME NOT NULL,
                    pause INTEGER NOT NULL
                )
                """
            )
        self._connection = con

    def insert_worktime(self, worktime: WorkTime) -> None:
        with self._connection as con:
            con.execute(
                "INSERT INTO worktime (start, end, pause) VALUES (?, ?, ?)",
                (
                    worktime.start.isoformat(),
                    worktime.end.isoformat(),
                    int(worktime.pause.total_seconds() / 60),
                ),
            )

    def query_worktime(self, start: datetime, end: datetime) -> list[WorkTime]:
        with self._connection as con:
            return [
                WorkTime(
                    datetime.fromisoformat(data[0]),
                    datetime.fromisoformat(data[1]),
                    timedelta(minutes=data[2]),
                    data[3],
                )
                for data in con.execute(
                    "SELECT start, end, pause, id FROM worktime WHERE start >= ? AND end <= ?",
                    (start.isoformat(), end.isoformat()),
                ).fetchall()
            ]

    def delete_worktime(self, worktime_id: int) -> None:
        with self._connection as con:
            con.execute("DELETE FROM worktime WHERE id = ?", (worktime_id,))

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
