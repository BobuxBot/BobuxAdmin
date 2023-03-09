from dataclasses import dataclass
from enum import Enum

from aiohttp import ClientResponseError, ClientSession

from utils import env
from utils.constants import ORG_NAME


class State(Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ItemType(Enum):
    ISSUE = 0
    PR = 1


@dataclass
class Item:
    number: int
    title: str
    url: str
    state: State
    type: ItemType

    @property
    def emoji(self) -> str:
        if self.type == ItemType.PR:
            return {
                State.OPEN: "<:propen:1082736247673466911>",
                State.CLOSED: "<:prclosed:1082736251167309875>",
                State.MERGED: "<:merged:1082736253667127337>",
            }[self.state]
        return {State.OPEN: "<:isopened:1082737004225232947>", State.CLOSED: "<:isclosed:1082737006754406481>"}[
            self.state
        ]

    def get_txt(self) -> str:
        return f"{self.emoji} [{self.title[:64]}{'...' if len(self.title) > 64 else ''} (#{self.number})]({self.url})"


class Github:
    _session: ClientSession

    def __init__(self) -> None:
        self.repositories: list[str] = []  # presumed to be constant, never updates

    async def setup(self) -> None:
        self._session = ClientSession(
            "https://api.github.com",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {env.main.GH_TOKEN}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            raise_for_status=True,
        )
        async with self._session.get(f"/orgs/{ORG_NAME}/repos") as resp:
            self.repositories = [r["name"] for r in await resp.json()]

    async def close(self) -> None:
        await self._session.close()

    async def get_item(self, repository: str, number: int) -> Item | None:
        try:
            r = await self._session.get(f"/repos/{ORG_NAME}/{repository}/issues/{number}")
        except ClientResponseError:
            return None
        data = await r.json()
        item_type = ItemType.PR if "pull_request" in data else ItemType.ISSUE
        state = State(data["state"])
        if item_type == ItemType.PR and state == State.CLOSED and data["pull_request"]["merged_at"] is not None:
            state = State.MERGED
        return Item(number, data["title"], data["html_url"], state, item_type)
