from datetime import datetime

import disnake
from disnake.ext import commands, tasks

from utils.bot import Bot, Cog
from utils.constants import GUILD_ID


class SystemListeners(Cog):
    @Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, err: commands.CommandError):
        await inter.send(embed=disnake.Embed(color=0xFF0000, title="Error Occurred", description=f"```py\n{err}```"))
        self.bot.log.error("Error occurred in command /%s", inter.application_command.name, exc_info=err)


class SystemLoops(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.ban_checks.start()

    @tasks.loop(minutes=30)
    async def ban_checks(self):
        await self.bot.wait_until_ready()
        now = datetime.now().timestamp()
        data = await self.bot.db.fetchall("SELECT target_id FROM tempbans WHERE unban_time < $1", now)
        guild = self.bot.get_guild(GUILD_ID)
        assert guild is not None, "failed to get main guild"

        for record in data:
            self.bot.log.info("Attempting to unban %d", id := record[0])
            try:
                await guild.unban(disnake.Object(id))
                self.bot.log.ok("Unbanned %d", id)
            except disnake.HTTPException as e:
                self.bot.log.warning("Failed to unban user %d", id, exc_info=e)

        await self.bot.db.execute("DELETE FROM tempbans WHERE unban_time < $1", now)
