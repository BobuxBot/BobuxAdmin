import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.constants import POINTS_ASSIGNERS_ROLES_IDS, SUGGESTION_POINTS_ROLES
from utils.utils import join_and, n_s


class SuggestionPoints(Cog):
    async def _check_points(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        current_points: int = await self.bot.db.get_suggestion_points(member.id)
        available_roles: set[disnake.Role] = {
            member.guild.get_role(v) for k, v in SUGGESTION_POINTS_ROLES.items() if k <= current_points
        }
        unavailable_roles = {member.guild.get_role(i) for i in SUGGESTION_POINTS_ROLES.values()} - available_roles
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

    @commands.slash_command(name="suggestionpoints")
    async def suggestionpoints(self, _):
        ...

    @suggestionpoints.sub_command(name="add")
    @commands.has_any_role(*POINTS_ASSIGNERS_ROLES_IDS)
    async def suggestionpoints_add(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, amount: commands.Range[int, 1, 10]
    ):
        """Add suggestion points to a user

        Parameters
        ----------
        member: Member to add suggestion points to
        amount: Amount of suggestion points to add
        """
        amount: int
        await self.bot.db.update_suggestion_points(member.id, amount)
        await inter.send(f"Successfully added **{amount}** points to **{member}**!")
        await self._check_points(inter, member)

    @suggestionpoints.sub_command(name="remove")
    @commands.has_any_role(*POINTS_ASSIGNERS_ROLES_IDS)
    async def suggestionpoints_remove(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, amount: commands.Range[int, 1, ...]
    ):
        """Remove suggestion points from a user

        Parameters
        ----------
        member: Member to add suggestion points to
        amount: Amount of suggestion points to add
        """
        amount: int
        await self.bot.db.update_suggestion_points(member.id, -amount)
        await inter.send(f"Successfully removed **{amount}** points from **{member}**!")
        await self._check_points(inter, member)

    @suggestionpoints.sub_command(name="show")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def suggestionpoints_show(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None
    ):
        """Show current amount of suggestion points of a member

        Parameters
        ----------
        member: Member whose points to check (you if unspecified)
        """
        member = member or inter.user
        amount: int = await self.bot.db.get_suggestion_points(member.id)
        await inter.send(f"This member has **{amount} point{n_s(amount)}**")
