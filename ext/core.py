from datetime import datetime

import disnake
from disnake.ext import commands, tasks
from tools import embeds
from tools.bot import AdminBot
from tools.constants import REACTIONS_MESSAGE_ID, REACTION_ROLES


class CoreListeners(commands.Cog):
    def __init__(self, bot: AdminBot):
        self.bot = bot

    @commands.Cog.listener("on_slash_command_error")
    async def slash_command_exception_handler(
        self, interaction: disnake.ApplicationCommandInteraction, error
    ):
        await interaction.send(
            embed=embeds.error(interaction, f"An error occured!\n```py\n{error}```"),
            ephemeral=True,
        )
        raise error

    @commands.Cog.listener("on_member_join")
    async def member_welcomer(self, member: disnake.Member):
        try:
            await member.send(
                f"Welcome to **{self.bot.server.name}**! We hope you will enjoy the time you will have in our server. \n\
Don't forget to check our rules out to avoid unpleased incidents :sunglasses:"
            )
        except:
            pass
        await self.bot.welcome_channel.send(
            f"**{member}** ({member.mention}) just joined the server! Now we're {self.bot.server.member_count}"
        )

    @commands.Cog.listener("on_member_remove")
    async def member_goodbyer(self, member: disnake.Member):
        await self.bot.welcome_channel.send(
            f"**{member}** has just left the server. Now we're {self.bot.server.member_count}"
        )

    @commands.Cog.listener("on_button_click")
    async def reaction_role_handler(self, interaction: disnake.MessageInteraction):
        if interaction.message.id == REACTIONS_MESSAGE_ID:
            role_id = REACTION_ROLES[str(interaction.component.emoji)]
            role = self.bot.server.get_role(role_id)
            if not role in interaction.author.roles:
                await interaction.author.add_roles(role)
                await interaction.send(
                    f"{interaction.author.mention}, you were assigned {role.mention}!",
                    ephemeral=True,
                )
            else:
                await interaction.author.remove_roles(role)
                await interaction.send(
                    f"{interaction.author.mention}, removed {role.mention} from you!",
                    ephemeral=True,
                )


class CoreLoops(commands.Cog):
    def __init__(self, bot: AdminBot):
        self.bot = bot
        self.unban_loop.start()

    @tasks.loop(minutes=1)
    async def unban_loop(self):
        threshold = datetime.now().timestamp()
        async with self.bot.db.execute(
            "SELECT id FROM bans WHERE unban_timestamp < ?", (threshold,)
        ) as cur:
            async for row in cur:
                try:
                    await self.bot.server.unban(disnake.Object(row[0]))
                except Exception as e:
                    print(f"Failed to unban {row[0]}:\n{e}")

        await self.bot.db.execute(
            "DELETE FROM bans WHERE unban_timestamp < ?", (threshold,)
        )
        await self.bot.db.commit()

    @unban_loop.before_loop
    async def loop_waiter(self):
        await self.bot.wait_until_ready()


def setup(bot: AdminBot):
    bot.add_cog(CoreListeners(bot))
    bot.add_cog(CoreLoops(bot))
