import importlib
import inspect
import os
import sys
from typing import Any

import disnake
from disnake.ext import commands
from exencolorlogs import FileLogger

from utils import env, paths
from utils.database import Database
from utils.github import Github

REQUIRED_DIRS = [paths.LOGS]
for p in REQUIRED_DIRS:
    if not p.exists():
        p.mkdir(parents=True)


class Bot(commands.InteractionBot):
    def __init__(self) -> None:
        intents = disnake.Intents(
            emojis=True,
            guild_messages=True,
            guild_scheduled_events=True,
            guild_typing=True,
            guilds=True,
            members=True,
            message_content=True,
        )
        self.db = Database()
        self.github = Github()
        self.log = FileLogger("BOT", folder=paths.LOGS)

        super().__init__(
            intents=intents,
            activity=disnake.Activity(name="over bobux bank", type=disnake.ActivityType.watching),
        )

    async def start(self, *args: Any, **kwargs: Any) -> None:
        self.log.info("Starting bot...")
        await self.db.connect()
        await self.db.setup()
        await self.github.setup()

        await super().start(*args, **kwargs)

    def run(self) -> None:
        self.log.info("Loading extensions...")
        self.load_all_extensions("ext")
        self.disable_dm_commands()
        super().run(env.main.TOKEN)

    async def on_ready(self) -> None:
        self.log.ok("Bot is ready!")

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        self.log.error("Exception occurred at %s", event_method, exc_info=sys.exc_info())

    async def close(self) -> None:
        self.log.info("Shutting down...")
        await self.db.close()
        await self.github.close()
        await super().close()
        self.log.ok("Bot was shut down successfully")

    def auto_setup(self, module_name: str) -> None:
        module = importlib.import_module(module_name, None)
        sys.modules[module_name] = module
        members = inspect.getmembers(
            module,
            lambda x: inspect.isclass(x) and issubclass(x, commands.Cog) and x.__name__ != "Cog",
        )
        for member in members:
            self.add_cog(member[1](self))

        self.log.ok("%s loaded", module_name)

    def load_all_extensions(self, path: str) -> None:
        for file in os.listdir(path):
            full_path = os.path.join(path, file).replace("\\", "/")
            if os.path.isdir(full_path):
                self.load_all_extensions(full_path)

            elif full_path.endswith(".py"):
                self.auto_setup(full_path[:-3].replace("/", "."))

    def disable_dm_commands(self) -> None:
        for command in self.slash_commands:
            command.body.dm_permission = False


class Cog(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @property
    def log(self) -> FileLogger:
        return self.bot.log
