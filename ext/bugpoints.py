import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.constants import BUGPOINTS_ROLES, POINTS_ASSIGNERS_ROLES_IDS
from utils.utils import join_and, n_s


class BugPoints(Cog):
    async def _check_bugpoints(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        current_bugpoints: int = await self.bot.db.get_bug_points(member.id)
        available_roles: set[disnake.Role] = {
            member.guild.get_role(v) for k, v in BUGPOINTS_ROLES.items() if k <= current_bugpoints
        }
        unavailable_roles = {member.guild.get_role(i) for i in BUGPOINTS_ROLES.values()} - available_roles
        current_roles: set[disnake.Role] = set(member.roles)
        roles_to_add = available_roles - current_roles
        roles_to_remove = unavailable_roles & current_roles
        if len(roles_to_remove) > 0:
            await member.remove_roles(*roles_to_remove)
        if len(roles_to_add) == 0:
            return
        await member.add_roles(*roles_to_add)
        await inter.send(
            f"Congratulations {member.mention}, you got "
            f"**{join_and('**, **', map(lambda x: x.mention, roles_to_add))}**",
            allowed_mentions=disnake.AllowedMentions(users=True, roles=False),
        )

    @commands.slash_command(name="bugpoints")
    async def bugpoints(self, _):
        ...

    @bugpoints.sub_command(name="add")
    @commands.has_any_role(*POINTS_ASSIGNERS_ROLES_IDS)
    async def bugpoints_add(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, amount: commands.Range[1, 3]
    ):
        """Add bugpoints to a user

        Parameters
        ----------
        member: Member to add bugpoints to
        amount: Amount of bugpoints to add
        """
        amount: int
        await self.bot.db.update_bug_points(member.id, amount)
        await inter.send(f"Successfully added **{amount}** points to **{member}**!")
        await self._check_bugpoints(inter, member)

    @bugpoints.sub_command(name="remove")
    @commands.has_any_role(*POINTS_ASSIGNERS_ROLES_IDS)
    async def bugpoints_remove(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, amount: commands.Range[1, ...]
    ):
        """Remove bugpoints from a user

        Parameters
        ----------
        member: Member to add bugpoints to
        amount: Amount of bugpoints to add
        """
        amount: int
        await self.bot.db.update_bug_points(member.id, -amount)
        await inter.send(f"Successfully removed **{amount}** points from **{member}**!")
        await self._check_bugpoints(inter, member)

    @bugpoints.sub_command(name="show")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bugpoints_show(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None):
        """Show current amount of bugpoints of a member

        Parameters
        ----------
        member: Member whose points to check (you if unspecified)
        """
        member = member or inter.user
        amount: int = await self.bot.db.get_bug_points(member.id)
        await inter.send(f"This member has **{amount} point{n_s(amount)}**")
