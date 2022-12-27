import disnake
from disnake.ext import commands, tasks

from utils.bot import Bot, Cog


class SystemListeners(Cog):
    @Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, err: commands.CommandError):
        await inter.send(embed=disnake.Embed(color=0xFF0000, title="Error Occurred", description=f"```py\n{err}```"))
        self.bot.log.error("Error occurred in command /%s", inter.application_command.name, exc_info=err)


class SystemLoops(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.ban_checks.start()

    @tasks.loop(seconds=5)
    async def ban_checks(self):
        await self.bot.wait_until_ready()
        present_time = round(disnake.utils.utcnow().timestamp())
        data = await self.bot.db.fetchrow("SELECT target_id, guild_id FROM tempbans WHERE unban_time < ?", present_time)

        if data is None:
            return

        try:
            guild = self.bot.get_guild(data[1])
            member = self.bot.get_user(data[0])
            await guild.unban(member)
            await self.bot.db.execute("DELETE FROM tempbans WHERE target_id = ?", (member.id))
        except disnake.HTTPException:
            pass
