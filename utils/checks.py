import disnake

from utils.errors import HierarchyError


def check_hierarchy(inter: disnake.Interaction, member: disnake.Member):
    assert isinstance(user := inter.user, disnake.Member)
    if user.top_role <= member.top_role:
        raise HierarchyError()
