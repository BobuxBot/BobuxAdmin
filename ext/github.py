import asyncio
import re

import disnake

from utils.bot import Cog
from utils.constants import DEVELOPER_ROLE_ID

REPO_TAG_PATTERN = re.compile(r"([-A-Za-z0-9_]*)#(\d+)")


class GithubCog(Cog):
    @Cog.listener()
    async def on_message(self, msg: disnake.Message):
        if msg.author.get_role(DEVELOPER_ROLE_ID) is None:
            return
        content = msg.clean_content
        tags: list[tuple[str, str]] = re.findall(REPO_TAG_PATTERN, content)  # type: ignore
        if len(tags) == 0:
            return
        ordered: dict[str, set[int]] = {}
        for tag in tags:
            repo = tag[0] or "Bobux"
            if repo not in self.bot.github.repositories:
                continue
            num = int(tag[1])
            if repo not in ordered:
                ordered[repo] = set()
            ordered[repo].add(num)
        await msg.add_reaction("<a:loading:1082740409240928316>")

        fetched_items = 0
        embed = disnake.Embed(title="Referencing Issues and PRs", color=0x00FFFF)
        for repo, numbers in ordered.items():
            if fetched_items > 8:
                break
            coros = [self.bot.github.get_item(repo, num) for num in numbers]
            if fetched_items + len(coros) > 8:
                coros = coros[: 8 - fetched_items]
            fetched_items += len(coros)
            items = list(filter(None, await asyncio.gather(*coros)))
            if len(items) == 0:
                continue
            embed.add_field(repo, "\n".join(i.get_txt() for i in items), inline=False)
        await msg.clear_reactions()
        if len(embed.fields) > 0:
            await msg.reply(embed=embed, fail_if_not_exists=False)
