from datetime import datetime
from typing import Union

from disnake import ApplicationCommandInteraction, Embed, Member, User

GREEN = 0x00FF00
RED = 0xFF0000
YELLOW = 0xFFFF00


class BobuxEmbed(Embed):
    def __init__(
        self,
        inter: Union[ApplicationCommandInteraction, Member, User],
        *args,
        set_author_icon: bool = True,
        footer_text: str = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs, timestamp=datetime.now())
        footer_text = footer_text or str(inter.author)
        if set_author_icon:
            url = None
            if isinstance(inter, ApplicationCommandInteraction):
                url = inter.author.avatar.url
            else:
                url = inter.avatar.url
            self.set_footer(text=footer_text, icon_url=url)


def success(
    inter: Union[ApplicationCommandInteraction, Member, User],
    title: str,
    description: str,
):
    return BobuxEmbed(inter, color=GREEN, title=f"✅ {title}", description=description)


def error(
    inter: Union[ApplicationCommandInteraction, Member, User],
    description: str,
    title: str = "Error Occured",
):
    return BobuxEmbed(inter, color=RED, title=f"❌ {title}", description=description)


def warning(
    inter: Union[ApplicationCommandInteraction, Member, User],
    title: str,
    description: str,
):
    return BobuxEmbed(inter, color=YELLOW, title="⚠️ " + title, description=description)
