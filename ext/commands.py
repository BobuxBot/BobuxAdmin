from datetime import datetime
from typing import Callable

import disnake
from disnake.ext import commands
from tools import embeds
from tools.bot import AdminBot
from tools.constants import NOTIFICATIONS_CHANNEL_ID
from tools.converters import TimeConverter
from tools.utils import to_discord_timestamp


class Moderation(commands.Cog):
    def __init__(self, bot: AdminBot):
        self.bot = bot

    def cog_slash_command_check(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> bool:
        return (
            inter.author.guild_permissions.manage_guild
            or self.bot.staff_role in inter.author.roles
        )

    @commands.slash_command(name="mute", description="Mutes (timeouts) a member.")
    async def mute(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        time: TimeConverter,
        reason: str = "No reason provided",
    ):
        if inter.author.top_role.position <= user.top_role.position:
            await inter.send(embed=embeds.error(inter, "You cannot mute someone with higher top role than yours"), ephemeral=True)
            return

        await user.timeout(
            duration=time, reason=f"{reason} | Responsible moderator: {inter.author}"
        )
        await inter.send(
            embed=embeds.success(
                inter,
                "User Muted",
                f"Successfully muted {user.mention} until {to_discord_timestamp(time)}.\nReason: `{reason}`",
            )
        )
        try:
            await user.send(
                embed=embeds.warning(
                    user,
                    "Muted",
                    f"You were muted in **{inter.guild.name}** until {to_discord_timestamp(time)}`.\nReason: `{reason}`",
                )
            )
        except:
            pass

    @commands.slash_command(name="unmute", description="Unmutes a member.")
    async def unmute(
        self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member
    ):
        if inter.author.top_role.position <= user.top_role.position:
            await inter.send(embed=embeds.error(inter, "You cannot unmute someone with higher top role than yours"), ephemeral=True)
            return

        await user.timeout(
            duration=None,
            reason=f"Manual unmute | Responsible moderator: {inter.author}",
        )
        await inter.send(
            embed=embeds.success(
                inter, "User Unmuted", f"Successfully unmuted {user.mention}"
            )
        )

    @commands.slash_command(name="ban", description="Bans a member.")
    async def ban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        reason: str = "No reason provided",
        time: TimeConverter = None,
    ):
        if inter.author.top_role.position <= user.top_role.position:
            await inter.send(embed=embeds.error(inter, "You cannot ban someone with higher top role than yours"), ephemeral=True)
            return

        await inter.response.defer()
        time_txt = f" until {to_discord_timestamp(time)}" if time is not None else ""
        try:
            await user.send(
                embed=embeds.warning(
                    user,
                    "Banned",
                    f"You were banned from **{inter.guild.name}**{time_txt}.\nReason: `{reason}`",
                )
            )
        except:
            pass
        await user.ban(
            reason=f'{reason} | Responsible moderator: {inter.author} | Time: {time if time is not None else "permanent"}'
        )
        if time is not None:
            await self.bot.db.execute(
                "INSERT INTO bans VALUES (?, ?)",
                (user.id, (datetime.now() + time).timestamp()),
            )
            await self.bot.db.commit()
        await inter.send(
            embed=embeds.success(
                inter,
                "User Banned",
                f"Successfully banned **{user}**{time_txt}.\nReason: `{reason}`",
            )
        )

    @commands.slash_command(name="kick", description="Kicks a member.")
    async def kick(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        reason: str = "No reason provided",
    ):
        if inter.author.top_role.position <= user.top_role.position:
            await inter.send(embed=embeds.error(inter, "You cannot kick someone with higher top role than yours"), ephemeral=True)
            return

        await user.kick(reason=f"{reason} | Responsible moderator: {inter.author}")
        await inter.send(
            embed=embeds.success(
                inter,
                "User Kicked",
                f"Successfully kicked **{user}**.\nReason: `{reason}`",
            )
        )
        try:
            await user.send(
                embed=embeds.warning(
                    user,
                    "Kicked",
                    f"You were kicked from **{inter.guild.name}**.\nReason: `{reason}`",
                )
            )
        except:
            pass

    @commands.slash_command(name="purge", description="Purges messages in a channel")
    async def purge(
        self,
        inter: disnake.ApplicationCommandInteraction,
        amount: int,
        channel: disnake.TextChannel = None,
        user: disnake.Member = None,
    ):
        await inter.response.defer(ephemeral=True)
        channel = channel or inter.channel
        c: Callable[[disnake.Message], bool] = None
        if user is None:
            c = lambda m: not m.pinned
        else:
            c = lambda m: not m.pinned and m.author.id == user.id

        amount = len(await channel.purge(limit=amount, check=c))
        await inter.send(
            f"Successfully purged `{amount}` messages from {channel.mention}",
            delete_after=5,
        )

    @commands.message_command(name="Purge all below")
    async def purge_all_below(
        self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message
    ):
        await inter.response.defer(ephemeral=True)
        amount = len(await inter.channel.purge(after=message.created_at))
        await inter.send(
            f"Successfully purged `{amount}` messages from {inter.channel.mention}"
        )


class Awards(commands.Cog):
    def __init__(self, bot: AdminBot):
        self.bot = bot

    @commands.slash_command(name="award", description="Adds bugpoints to a member.")
    @commands.has_any_role("Moderator", "Support", "Bot Coder", "Admin")
    async def award(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        amount: int = commands.Param(ge=5, le=20),
    ):
        await self.bot.check_user(user.id)
        await self.bot.db.execute(
            "UPDATE users SET bugpoints = bugpoints + ? WHERE id = ?", (amount, user.id)
        )
        await self.bot.db.commit()
        await inter.send(
            embed=embeds.success(
                inter,
                "Award Given",
                f"Successfully gave {user.mention} **{amount}** points!",
            )
        )

        cur = await self.bot.db.execute(
            "SELECT bugpoints FROM users WHERE id = ?", (user.id,)
        )
        score: int = (await cur.fetchone())[0]

        roles = {
            10: self.bot.server.get_role(860947939936829451),
            50: self.bot.server.get_role(860947783908720640),
            100: self.bot.server.get_role(860947657937125386),
        }
        for i in roles:
            if score >= i and not roles[i] in user.roles:
                await user.add_roles(roles[i])
                await inter.send(
                    f"Congratulations, {user.mention}, you have obtained {roles[i].mention}!",
                    allowed_mentions=disnake.AllowedMentions(users=True),
                )

    @commands.slash_command(
        name="bugpoints", description="Shows your or user's bugpoints"
    )
    async def bugpoints(
        self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None
    ):
        user = user or inter.author
        await self.bot.check_user(user.id)
        cur = await self.bot.db.execute(
            "SELECT bugpoints FROM users WHERE id = ?", (user.id,)
        )
        score: int = (await cur.fetchone())[0]
        await inter.send(f"{user.mention} has **{score} bug points!**")


class Admin(commands.Cog):
    def __init__(self, bot: AdminBot):
        self.bot = bot

    async def cog_slash_command_check(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        return await self.bot.is_owner(inter.author)

    @commands.slash_command(enabled=False, hidden=True)
    async def rrsetup(self, inter: disnake.ApplicationCommandInteraction):
        view = disnake.ui.View(timeout=None)
        view.stop()
        items = [("⬆️", "Server Updates"), ("🥵", "Bot Updates"), ("📰", "Bot News")]
        for item in items:
            view.add_item(
                disnake.ui.Button(
                    style=disnake.ButtonStyle.blurple, emoji=item[0], label=item[1]
                )
            )
        m = await self.bot.server.get_channel(NOTIFICATIONS_CHANNEL_ID).send(
            "Choose a role to assign/remove", view=view
        )
        await inter.send(f"ID: {m.id}")


def setup(bot: AdminBot):
    bot.add_cog(Moderation(bot))
    bot.add_cog(Awards(bot))
    bot.add_cog(Admin(bot))
