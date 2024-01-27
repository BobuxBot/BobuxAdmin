import asyncio
import re
from enum import StrEnum

import aiohttp
import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.constants import DEVELOPER_ROLE_ID

REPO_TAG_PATTERN = re.compile(r"([-A-Za-z0-9_]*)#(\d+)")


class Majority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRIT = "CRIT"


class DeploymentVersion(StrEnum):
    BETA = "beta"
    PRODUCTION = "production"


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

    @commands.slash_command(name="bugreport")
    @commands.has_role(DEVELOPER_ROLE_ID)
    async def bugreport(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str,
        majority: Majority,
        version: DeploymentVersion,
        body: str | None = None,
    ):
        """
        Create an issue on github labeled as bug

        Parameters
        ----------
        title: Issue title
        majority: Majority of the bug
        version: Production | beta
        body: Issue body (recommended to edit in github after creation instead)
        """

        await inter.response.defer()

        try:
            url, number = await self.bot.github.create_issue(
                "Bobux", title, ["type: bug", f"majority: {majority}", f"rel: {version}"], body
            )
        except aiohttp.ClientResponseError as e:
            await inter.send(f"Failed to create issue: {e.status} {e.message}")
        else:
            await inter.send(f"Successfully created new issue: [#{number}]({url})")

    @commands.slash_command(name="idea")
    @commands.has_role(DEVELOPER_ROLE_ID)
    async def idea(self, inter: disnake.ApplicationCommandInteraction, title: str, body: str | None = None):
        """
        Create an issue on github labeled as idea

        Parameters
        ----------
        title: Issue title
        body: Issue body (recommended to edit in github after creation instead)
        """

        await inter.response.defer()

        try:
            url, number = await self.bot.github.create_issue("Bobux", title, ["type: idea"], body)
        except aiohttp.ClientResponseError as e:
            await inter.send(f"Failed to create issue: {e.status} {e.message}")
        else:
            await inter.send(f"Successfully created new issue: [#{number}]({url})")
