import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.converter import TimeConverter as convert
from utils.errors import HierarchyError


class moderation(Cog):
    @commands.slash_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason"
    ):
        """Bans a member

        Parameters
        -----------
        member: The member to ban
        reason: The reason for banning
        """
        if inter.user.top_role > member.top_role:
            try:
                await member.send(
                    embed=disnake.Embed(
                        title="Banned",
                        description=f"You have been banned from {inter.guild.name} for **{reason}**!",
                    )
                )
            except disnake.HTTPException:
                pass
            finally:
                await inter.send(
                    embed=disnake.Embed(
                        title="Member banned",
                        description=f"⚒ | {member.mention} has been banned from this server by {inter.user.mention} for **{reason}**!",
                        color=disnake.Color.red(),
                    )
                )
                await inter.guild.ban(member)
        else:
            raise HierarchyError

    @commands.slash_command(name="tempban")
    async def tempban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        duration: convert,
        reason: str = "No reason",
    ):
        """Temporary bans a member

        Parameters
        ----------
        member: The member to temp ban
        duration: The duration for banning. (s, m, h ,d format)
        reason: The reason for temp banning
        """
        if inter.user.top_role > member.top_role:

            try:
                await member.send(
                    embed=disnake.Embed(
                        title="Banned",
                        description=f"You have been banned from {inter.guild.name} for **{reason}**!",
                    )
                )
            except disnake.HTTPException:
                pass
            finally:
                await inter.send(
                    embed=disnake.Embed(
                        title="Member banned",
                        description=f"{member.mention} has been banned from this server by {inter.user.mention} for **{reason}**!",
                        color=disnake.Color.red(),
                    )
                )
                duration = round(disnake.utils.utcnow().timestamp() + duration)
                await inter.guild.ban(member)
                await self.bot.db.execute(
                    f"INSERT INTO tempbans (guild_id, target_id, unban_time) VALUES (?, ?, ?)",
                    inter.guild.id,
                    member.id,
                    duration,
                )
        else:
            raise HierarchyError

    @commands.slash_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason"
    ):
        """Kicks a member

        Parameters
        ----------
        member: The member to kick
        reason: The reason for kicking
        """
        if inter.user.top_role > member.top_role:
            try:

                await member.send(
                    embed=disnake.Embed(
                        title="Kicked",
                        description=f"You have been kicked from {inter.guild.name} for **{reason}**!",
                    )
                )

            except disnake.HTTPException:
                pass
            finally:
                await inter.send(
                    embed=disnake.Embed(
                        title="Member kicked",
                        description=f"{member.mention} has been kicked from this server by {inter.user.mention} for **{reason}**!",
                        color=disnake.Color.red(),
                    )
                )
                await inter.guild.kick(member)
        else:
            raise HierarchyError

    @commands.slash_command(name="timeout")
    @commands.has_permissions(mute_members=True)
    async def timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        duration: convert,
        reason: str = "No reason",
    ):
        """Timeouts a member

        Parameters
        -----------
        member: The member to timeout
        duration: Duration of the timeout (s, m, h, d format)
        reason: The reason for timeouting
        """
        if inter.user.top_role > member.top_role:
            try:
                await inter.guild.timeout(user=member, duration=duration, reason=reason)

            except disnake.HTTPException:
                pass
            finally:
                await inter.send(
                    embed=disnake.Embed(
                        title="Member timedout",
                        description=f"{member.mention} has been timedout by {inter.user.mention}!",
                        color=disnake.Color.green(),
                    )
                )
        else:
            raise HierarchyError

    @commands.slash_command(name="untimeout")
    @commands.has_permissions(mute_members=True)
    async def untimeout(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason"
    ):
        """Untimeouts a member from timeout

        Parameters
        -----------
        member: The member to untimeout
        reason: The reason for untimeouting
        """
        if inter.user.top_role > member.top_role:
            try:
                await inter.guild.timeout(user=member, duration=None, reason=reason)

            except disnake.HTTPException:
                pass
            finally:
                await inter.send(
                    embed=disnake.Embed(
                        title="Member untimedout",
                        description=f"{member.mention} has been untimedout by {inter.user.mention}!",
                        color=disnake.Color.green(),
                    )
                )
        else:
            raise HierarchyError

    @commands.slash_command(name="warn")
    async def warn(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @warn.sub_command(name="add")
    @commands.has_permissions(moderate_members=True)
    async def add(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "No reason"
    ):
        """Adds warn to a member

        Parameters
        ----------
        member: The member to warn
        reason: The reason for warning
        """
        if inter.user.top_role > member.top_role:
            assigned_at = round(disnake.utils.utcnow().timestamp())
            await self.bot.db.execute(
                f"INSERT INTO warns (target_id, moderator_id, assigned_at, reason) VALUES (?, ?, ?. ?)",
                member.id,
                inter.user.id,
                assigned_at,
                f"{reason}",
            )
            await inter.send(f"Successfully warned {member.mention}!")
        else:
            raise HierarchyError

    @warn.sub_command(name="clear")
    @commands.has_permissions(moderate_members=True)
    async def clear(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        """Clears all warns from a member

        Parameters
        ----------
        member: The member to clear all warns
        """
        if inter.user.top_role > member.top_role:
            await self.bot.db.execute("DELETE FROM warns WHERE target_id = ?", (member.id))
            await inter.send(f"Successfully cleared all warns from {member.mention}")
        else:
            raise HierarchyError

    @warn.sub_command(name="delete")
    @commands.has_permissions(moderate_members=True)
    async def delete(self, inter: disnake.ApplicationCommandInteraction, warnid: int):
        """Deletes a particular warn case

        Parameters
        ----------
        warnid: The warnd id to delete from database
        """
        await self.bot.db.execute("DELETE FROM warns WHERE id = ?", (warnid))
        await inter.send(f"Successfully deleted warnd id **{warnid}**!")
