import re

import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.modals import ButtonRolesSetupModal
from utils.utils import get_closest_button

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

    async def check_button(
        self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message, button_name: str
    ) -> tuple[disnake.ui.View, disnake.ui.Button] | tuple[None, None]:
        none = (None,) * 2
        if message.author.id != self.bot.user.id:
            await inter.send("Bot cannot edit messages of other users!", ephemeral=True)
            return none
        view = disnake.ui.View.from_message(message)
        try:
            button = get_closest_button(view, button_name)
        except IndexError:
            await inter.send("Could not find any buttons with this name!", ephemeral=True)
            return none
        if button is None:
            await inter.send("There are no buttons on this message!", ephemeral=True)
            return none
        if not button.custom_id.startswith("br-"):
            await inter.send("This button is not a buttonrole button!", ephemeral=True)
            return none
        return view, button

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
        await inter.response.defer()
        view, button = await self.check_button(inter, message, button_name)
        if view is None:
            return
        view.remove_item(button)
        await message.edit(view=view)
        await inter.send("Successfully removed this button from a message!")

    @buttonroles.sub_command(name="enable")
    async def buttonroles_enable(
        self, inter: disnake.ApplicationCommandInteraction, button_name: str, message: disnake.Message
    ):
        """Enable a disabled role button on a message

        Parameters
        ----------
        button_name: Name of the button to enable
        message: ID/channelID-messageID/URL of message to enable the button on
        """
        await inter.response.defer()
        view, button = await self.check_button(inter, message, button_name)
        if view is None:
            return
        if not button.disabled:
            await inter.send("This button is already enabled!", ephemeral=True)
        button.disabled = False
        await message.edit(view=view)
        await inter.send("Successfully enabled this button!")

    @buttonroles.sub_command(name="disable")
    async def buttonroles_disable(
        self, inter: disnake.ApplicationCommandInteraction, button_name: str, message: disnake.Message
    ):
        """Disable an enabled role button on a message

        Parameters
        ----------
        button_name: Name of the button to disable
        message: ID/channelID-messageID/URL of message to disable the button on
        """
        await inter.response.defer()
        view, button = await self.check_button(inter, message, button_name)
        if view is None:
            return
        if button.disabled:
            await inter.send("This button is already disabled!", ephemeral=True)
        button.disabled = True
        await message.edit(view=view)
        await inter.send("Successfully disabled this button!")
