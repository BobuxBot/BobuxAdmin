from dataclasses import dataclass

import disnake


class ButtonNotFound(Exception):
    def __init__(self, d: dict[str, ...]):
        super().__init__("Unable to find button with %s" % ", ".join(f"{k}={v}" for k, v in d))


@dataclass
class EmbedPaginatorEntry:
    name: str
    value: str
    inline: bool = False


class EmbedPaginator:
    _msg: disnake.InteractionMessage
    _view: "PaginatorView"

    def __init__(self, base_embed: disnake.Embed, entries: list[EmbedPaginatorEntry], max_entries: int = 5):
        self._base_embed = base_embed
        self._entries: list[EmbedPaginatorEntry] = entries
        self._current_page = 0
        self._max_page = (len(entries) + max_entries - 1) // max_entries - 1
        self._max_entries = max_entries

    def _get_current_embed(self) -> disnake.Embed:
        start = self._current_page * self._max_entries
        end = start + self._max_entries
        embed = self._base_embed.copy()
        for field in self._entries[start:end]:
            embed.add_field(field.name, field.value, inline=field.inline)
        return embed

    async def init(self, inter: disnake.ApplicationCommandInteraction) -> None:
        embed = self._get_current_embed()
        if self._max_page == 0:
            await inter.send(embed=embed)
            return
        self._view = PaginatorView(self, inter.user.id)
        await inter.send(embed=embed, view=self._view)
        self._msg = await inter.original_response()

    async def update(self, inter: disnake.MessageInteraction) -> None:
        await inter.response.edit_message(embed=self._get_current_embed(), view=self._view)

    async def previous_page(self, inter: disnake.MessageInteraction) -> None:
        if self._current_page < 1:
            return
        self._current_page -= 1
        self._view.enable_button(custom_id="forward")
        if self._current_page <= 0:
            self._view.disable_button(custom_id="back")
        await self.update(inter)

    async def next_page(self, inter: disnake.MessageInteraction) -> None:
        if self._current_page >= self._max_page:
            return
        self._current_page += 1
        self._view.enable_button(custom_id="back")
        if self._current_page >= self._max_page:
            self._view.disable_button(custom_id="forward")
        await self.update(inter)

    async def stop(self, inter: disnake.MessageInteraction) -> None:
        self._view.disable_all_buttons()
        await inter.response.edit_message(view=self._view)

    async def timeout(self) -> None:
        self._view.disable_all_buttons()
        await self._msg.edit(view=self._view)


class PaginatorView(disnake.ui.View):
    def __init__(self, paginator: EmbedPaginator, user_id: int, *, timeout: float | None = 180.0):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.paginator = paginator

    def disable_button(self, **kwargs) -> None:
        for child in self.children:
            if isinstance(child, disnake.ui.Button) and any(getattr(child, n) == v for n, v in kwargs.items()):
                child.disabled = True
                return
        raise ButtonNotFound(kwargs)

    def enable_button(self, **kwargs) -> None:
        for child in self.children:
            if isinstance(child, disnake.ui.Button) and any(getattr(child, n) == v for n, v in kwargs.items()):
                child.disabled = False
                return
        raise ButtonNotFound(kwargs)

    def disable_all_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, disnake.ui.Button):
                child.disabled = True

    async def on_timeout(self) -> None:
        await self.paginator.timeout()

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.send(
                "This button is not for you, go press something else", ephemeral=True, delete_after=3
            )
            return False
        return True

    @disnake.ui.button(emoji="⬅️", custom_id="back", disabled=True, style=disnake.ButtonStyle.blurple)
    async def back_btn(self, _, inter: disnake.MessageInteraction):
        await self.paginator.previous_page(inter)

    @disnake.ui.button(emoji="⏹️", custom_id="stop", style=disnake.ButtonStyle.blurple)
    async def stop_btn(self, _, inter: disnake.MessageInteraction):
        await self.paginator.stop(inter)

    @disnake.ui.button(emoji="➡️", custom_id="forward", style=disnake.ButtonStyle.blurple)
    async def forward_btn(self, _, inter: disnake.MessageInteraction):
        await self.paginator.next_page(inter)
