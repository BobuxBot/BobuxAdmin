import difflib
import re

import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.modals import ButtonRolesSetupModal

BUTTONROLE_CUSTOM_ID_PATTERN = re.compile(r"br-(\d{18,19})")


class ButtonRoleListeners(Cog):
    @Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if (
            isinstance(inter.component, disnake.Button)
            and len(ids := re.findall(BUTTONROLE_CUSTOM_ID_PATTERN, inter.component.custom_id)) > 0
        ):
            await inter.response.defer(ephemeral=True)
            role = inter.guild.get_role(int(ids[0]))  # not using snowflake cause role may get deleted
            if role is None:
                await inter.send(
                    "Could not find role associated with this button, please notify admins about this", ephemeral=True
                )
                return

            try:
                if role not in inter.user.roles:
                    await inter.user.add_roles(role)
                    txt = f"Successfully added {role.mention} to you!"
                else:
                    await inter.user.remove_roles(role)
                    txt = f"Successfully removed {role.mention} from you!"
                await inter.send(txt, ephemeral=True, allowed_mentions=disnake.AllowedMentions.all())
            except disnake.HTTPException as e:
                await inter.send("Failed to add/remove role", ephemeral=True)
                self.bot.log.error("Failed to do buttonrole operation for %d", inter.user.id, exc_info=e)


class ButtonRolesManagement(Cog):
    async def cog_slash_command_check(self, inter: disnake.ApplicationCommandInteraction) -> bool:
        if inter.user.guild_permissions.manage_roles:
            return True
        raise commands.MissingPermissions(["manage_roles"])

    @commands.slash_command(name="buttonroles")
    async def buttonroles(self, _):
        ...

    @buttonroles.sub_command(name="setup")
    async def buttonroles_setup(self, inter: disnake.ApplicationCommandInteraction):
        """Interactive buttonroles setup"""
        await inter.response.send_modal(ButtonRolesSetupModal())

    @buttonroles.sub_command(name="add")
    async def buttonroles_add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        button_name: str,
        role: disnake.Role,
        message: disnake.Message,
    ):
        """Add a button role to existing bot's message

        Parameters
        ----------
        button_name: Name for new button
        role: Role to assign on button click
        message: ID/channelID-messageID/URL of message to add the button to
        """
        if role >= inter.user.top_role:
            await inter.send(
                "You cannot create a button role for role higher or equal to your top role!", ephemeral=True
            )
            return
        if message.author.id != self.bot.user.id:
            await inter.send("Bot cannot edit messages of other users!", ephemeral=True)
            return
        await inter.response.defer()
        view = disnake.ui.View.from_message(message)
        view.add_item(
            disnake.ui.Button(label=button_name, style=disnake.ButtonStyle.blurple, custom_id=f"br-{role.id}")
        )
        await message.edit(view=view)
        await inter.send("Successfully added new buttonrole!")

    @buttonroles.sub_command(name="remove")
    async def buttonroles_remove(
        self, inter: disnake.ApplicationCommandInteraction, button_name: str, message: disnake.Message
    ):
        """Remove a button role to existing bot's message

        Parameters
        ----------
        button_name: Name of the button to remove
        message: ID/channelID-messageID/URL of message to remove the button from
        """
        if message.author.id != self.bot.user.id:
            await inter.send("Bot cannot edit messages of other users!", ephemeral=True)
            return
        await inter.response.defer()
        view = disnake.ui.View.from_message(message)
        buttons: dict[str, disnake.ui.Button] = {c.label: c for c in view.children if isinstance(c, disnake.ui.Button)}
        if len(buttons) == 0:
            await inter.send("There are no buttons on this message!", ephemeral=True)
            return
        try:
            button: disnake.ui.Button = buttons[difflib.get_close_matches(button_name, buttons.keys(), n=1)[0]]  # type: ignore     # noqa: E501
        except IndexError:
            await inter.send("Could not find any buttons with this name!", ephemeral=True)
            return
        if not button.custom_id.startswith("br-"):
            await inter.send("This button is not a buttonrole button!", ephemeral=True)
            return
        view.remove_item(button)
        await message.edit(view=view)
        await inter.send("Successfully removed this button from a message!")
