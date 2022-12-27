from typing import Any, Iterable

import aiosqlite
from aiosqlite import Row
from exencolorlogs import FileLogger

from utils import paths


class Database:
    _con: aiosqlite.Connection

    def __init__(self) -> None:
        self._log = FileLogger("DB", folder=paths.LOGS)

    async def connect(self) -> None:
        self._log.info("Connecting to database...")
        self._con = await aiosqlite.connect(paths.DB)
        self._log.ok("Connected to database %s successfully", paths.DB.as_posix())

    async def close(self) -> None:
        self._log.info("Closing database connection...")
        await self._con.close()
        self._log.ok("Database connection closed successfully!")

    async def setup(self) -> None:
        self._log.info("Executing setup script...")
        with open(paths.BASE_CONFIG) as f:
            await self._con.executescript(f.read())
        self._log.ok("Setup script was executed successfully!")

    async def execute(self, sql: str, *args: Any) -> aiosqlite.Cursor:
        cur = await self._con.execute(sql, args)
        await self._con.commit()
        return cur

    async def fetchrow(self, sql: str, *args: Any) -> Row | None:
        return await (await self.execute(sql, *args)).fetchone()

    async def fetchval(self, sql: str, *args: Any) -> Any | None:
        try:
            return (await self.fetchrow(sql, *args))[0]
        except IndexError:
            return None

    async def fetchall(self, sql: str, *args: Any) -> Iterable[Row]:
        return await (await self.execute(sql, *args)).fetchall()
