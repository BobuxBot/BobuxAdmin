from os import listdir

from aiosqlite import connect
from cryptography.fernet import Fernet
from disnake import AllowedMentions, ApplicationCommandInteraction, Intents, TextChannel
from disnake.ext.commands import Bot

from tools.constants import SERVER_ID, STAFF_ROLE_ID, WELCOME_CHANNEL_ID


class AdminBot(Bot):
    def __init__(self):
        intents = Intents.default()
        intents.members = True
        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=intents,
            test_guilds=[SERVER_ID],
            allowed_mentions=AllowedMentions.none(),
        )
        self.add_app_command_check(self.global_check, slash_commands=True)
        for name in listdir("ext"):
            if name.endswith(".py"):
                self.load_extension("ext." + name[:-3])

    async def start(self, *args, **kwargs):
        self.db = await connect("core.db")
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS users (id INT UNIQUE NOT NULL, bugpoints INT DEFAULT 0)"
        )
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS bans (id INT UNIQUE NOT NULL, unban_timestamp REAL NOT NULL)"
        )
        await self.db.commit()
        await super().start(*args, **kwargs)

    async def close(self):
        await self.db.close()
        await super().close()

    async def on_ready(self):
        print("Bot is ready!")
        self.server = self.get_guild(SERVER_ID)
        self.welcome_channel: TextChannel = self.server.get_channel(WELCOME_CHANNEL_ID)
        self.staff_role = self.server.get_role(STAFF_ROLE_ID)

    def run(self):
        token = None
        with open("token.crypt", "rb") as token_f, open("key.key", "rb") as key_f:
            token = Fernet(key_f.read()).decrypt(token_f.read()).decode()

        super().run(token)

    def global_check(self, interaction: ApplicationCommandInteraction):
        return interaction.guild_id == SERVER_ID

    async def check_user(self, user_id: int):
        print(user_id)
        await self.db.execute(
            f"INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,)
        )
        await self.db.commit()
