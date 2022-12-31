from datetime import datetime, timedelta, timezone

import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.checks import check_hierarchy
from utils.converters import TimeConverter
from utils.pagination import EmbedPaginator, EmbedPaginatorEntry
from utils.utils import get_duration_end_ts, get_reason


class Moderation(Cog):
    async def _ban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str,
        clean_history_duration: TimeConverter = disnake.utils.MISSING,
        ban_duration: timedelta | None = None,
    ):
        check_hierarchy(inter, member)
        await inter.response.defer()
        try:
            await member.ban(
                reason=get_reason(inter, reason, ban_duration), clean_history_duration=clean_history_duration
            )
        except disnake.HTTPException as e:
            await inter.send(
                "Failed to ban this member. This is probably because bot is "
                "missing permissions or its top role is not higher than target's one"
            )
            self.bot.log.warning("Failed to ban member %d", member.id, exc_info=e)

        try:
            await member.send(f"You were banned from **{inter.guild.name}** for `{reason}`.")
        except disnake.HTTPException:
            pass

        await inter.send(f"Successfully banned **{member}** for `{reason}`!")
        if ban_duration is not None:
            await self.bot.db.execute(
                "INSERT INTO tempbans (target_id, unban_time) VALUES ($1, $2)",
                member.id,
                get_duration_end_ts(ban_duration),
            )

    @commands.slash_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str,
        clean_history_duration: TimeConverter = disnake.utils.MISSING,
    ):
        """Bans a member

        Parameters
        -----------
        member: Member to ban
        reason: Reason for banning
        clean_history_duration: Delete messages for last ...
        """

        await self._ban(inter, member, reason, clean_history_duration)

    @commands.slash_command(name="tempban")
    @commands.has_permissions(ban_members=True)
    async def tempban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        duration: TimeConverter,
        reason: str = "No reason",
        clean_history_duration: TimeConverter = disnake.utils.MISSING,
    ):
        """Temporary bans a member

        Parameters
        ----------
        member: Member to ban
        duration: Duration of ban (eg. 1d12h)
        reason: Reason for ban
        clean_history_duration: Delete messages for last ...
        """

        await self._ban(inter, member, reason, clean_history_duration, duration)

    @commands.slash_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        """Kicks a member

        Parameters
        ----------
        member: Member to kick
        reason: Reason for kicking
        """
        check_hierarchy(inter, member)
        await inter.response.defer()

        try:
            await member.kick(reason=get_reason(inter, reason))
        except disnake.HTTPException as e:
            await inter.send(
                "Failed to kick this member. This is probably because bot is "
                "missing permissions or its top role is not higher than target's one"
            )
            self.bot.log.warning("Failed to kick member %d", member.id, exc_info=e)

        try:
            await member.send(f"You were kicked from **{inter.guild.name}** for `{reason}`.")
        except disnake.HTTPException:
            pass

        await inter.send(f"Successfully kicked **{member}** for `{reason}`!")

    @commands.slash_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        duration: TimeConverter,
        reason: str,
    ):
        """Timeouts a member

        Parameters
        -----------
        member: Member to timeout
        duration: Duration of the timeout (s, m, h, d format)
        reason: Reason for timeout
        """
        check_hierarchy(inter, member)
        await inter.response.defer()

        try:
            await member.timeout(duration=duration, reason=get_reason(inter, reason))
        except disnake.HTTPException as e:
            await inter.send("Failed to timeout this user")
            self.bot.log.warning("Failed to timeout %d", member.id, exc_info=e)
            return
        await inter.send(f"Successfully timed out **{member}** for `{reason}`")

    @commands.slash_command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        """Takes off timeout from a member

        Parameters
        -----------
        member: Member to untimeout
        """
        check_hierarchy(inter, member)
        await inter.response.defer()

        try:
            await member.timeout(duration=None, reason=f"Responsible moderator: {inter.user}")
        except disnake.HTTPException as e:
            await inter.send("Failed to untimeout this member")
            self.bot.log.warning("Failed to untimeout %d", member.id, exc_info=e)
            return
        await inter.send(f"Successfully took the timeout off from **{member}**!")

    @commands.slash_command(name="warn")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        """Adds warn to a member

        Parameters
        ----------
        member: Member to warn
        reason: Reason for warning
        """
        check_hierarchy(inter, member)
        await self.bot.db.execute(
            "INSERT INTO warns (target_id, moderator_id, assigned_at, reason) VALUES ($1, $2, $3, $4)",
            member.id,
            inter.user.id,
            int(datetime.now().timestamp()),
            reason,
        )
        await inter.send(f"Successfully warned **{member}** for `{reason}`")

    @commands.slash_command(name="warns")
    @commands.has_permissions(moderate_members=True)
    async def warns(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        """Lists member's warnings

        Parameters
        ----------
        member: Member whose warnings to view
        """
        data = await self.bot.db.fetchall(
            "SELECT id, moderator_id, assigned_at, reason FROM warns WHERE target_id = $1", member.id
        )
        if len(data) == 0:
            await inter.send("This user got no warnings!")
            return

        entries = [
            EmbedPaginatorEntry(
                f"#{row[0]}",
                f"Moderator: **{inter.guild.get_member(row[1])}** (<@{row[1]}>) ID: `{row[1]}`\n"
                f"Assigned at: {disnake.utils.format_dt(datetime.fromtimestamp(row[2]).astimezone(timezone.utc))}\n"
                f"Reason: `{row[3]}`",
            )
            for row in data
        ]

        await EmbedPaginator(
            disnake.Embed(
                color=disnake.Color.blurple(),
                title=f"{member}'s warnings",
                description=f"Total of **{len(entries)}** warnings",
            ),
            entries,
        ).init(inter)

    @commands.slash_command(name="clearwarns")
    @commands.has_permissions(moderate_members=True)
    async def clearwarns(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        """Clears all warns from a member

        Parameters
        ----------
        member: Member whose warns to clear
        """
        check_hierarchy(inter, member)
        await self.bot.db.execute("DELETE FROM warns WHERE target_id = $1", member.id)
        await inter.send(f"Successfully cleared all warnings from **{member}**!")

    @commands.slash_command(name="delwarn")
    @commands.has_permissions(moderate_members=True)
    async def delwarn(self, inter: disnake.ApplicationCommandInteraction, warn_id: int):
        """Deletes a particular warn case

        Parameters
        ----------
        warn_id: The warning ID
        """
        exists = await self.bot.db.fetchval("SELECT EXISTS(SELECT * FROM warns WHERE id = $1)", warn_id)
        if not exists:
            await inter.send(f"Warning **#{warn_id}** does not exist!")
            return
        await self.bot.db.execute("DELETE FROM warns WHERE id = $1", warn_id)
        await inter.send(f"Successfully deleted warning **#{warn_id}**!")
