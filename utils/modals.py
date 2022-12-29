import difflib
import re

import disnake.ui


def _extract_button_roles(inter: disnake.ModalInteraction, raw: str) -> list[disnake.ui.Button]:
    roles_d: dict[str, disnake.Role] = {r.name: r for r in inter.guild.roles if r < inter.user.top_role}
    raw_pairs: list[tuple[str, ...]] = [tuple(s.split("=")) for s in raw.splitlines()]
    buttons: list[disnake.ui.Button] = []
    for role_name, button_name in raw_pairs:
        try:
            if re.fullmatch("\d{18,19}", role_name) is not None:
                role_id = int(role_name)
                if inter.guild.get_role(role_id) is None:
                    continue
            else:
                role_id: int = roles_d[difflib.get_close_matches(role_name.strip(' "'), roles_d.keys(), n=1)[0]].id  # type: ignore     # noqa: E501
        except IndexError:
            continue
        buttons.append(
            disnake.ui.Button(
                label=button_name.strip(' "'), custom_id=f"br-{role_id}", style=disnake.ButtonStyle.blurple
            )
        )
    return buttons


class ButtonRolesSetupModal(disnake.ui.Modal):
    def __init__(self):
        super().__init__(
            title="Setup Buttonroles",
            components=[
                disnake.ui.TextInput(
                    label="Message",
                    custom_id="message",
                    style=disnake.TextInputStyle.paragraph,
                    placeholder="Text to send in buttonroles message",
                    max_length=1024,
                ),
                disnake.ui.TextInput(
                    label="Button Roles",
                    custom_id="button_roles",
                    style=disnake.TextInputStyle.paragraph,
                    placeholder='"RoleName | ID = Button Name" pairs each on new line',
                ),
            ],
        )

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        message: str = interaction.text_values["message"]
        button_roles_raw: str = interaction.text_values["button_roles"]
        fail_embed = (
            disnake.Embed(
                color=disnake.Color.red(), description="Here's message and buttons data so you can paste it back"
            )
            .add_field("Message", f"```\n{message}```", inline=False)
            .add_field("Buttons", button_roles_raw, inline=False)
        )
        try:
            buttons = _extract_button_roles(interaction, button_roles_raw)
        except Exception as e:
            await interaction.send(
                "Failed to process button roles data, make sure you follow this format:\n"
                "```\nRole Name 1 = Button Name 1\nRole Name 2 = Button Name 2```",
                embed=fail_embed,
            )
            interaction.bot.log.error(  # type: ignore
                "Failed to process button roles data %s", button_roles_raw, exc_info=e
            )
            return

        if len(buttons) == 0:
            await interaction.send("Could not recognise any roles.", ephemeral=True)
            return

        await interaction.response.defer()
        view = disnake.ui.View()
        for button in buttons:
            view.add_item(button)

        try:
            await interaction.channel.send(message, view=view)
            await interaction.send("Successfully created new button roles message!")
        except disnake.Forbidden:
            await interaction.send("Bot does not have permission to send messages in this channel!", embed=fail_embed)
        except disnake.HTTPException:
            await interaction.send("Failed to send message in this channel!", embed=fail_embed)
