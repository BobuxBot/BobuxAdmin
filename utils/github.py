from dataclasses import dataclass
from enum import Enum

from aiohttp import ClientSession

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
    repositories: tuple[str]

    async def setup(self) -> None:
        self._session = ClientSession(
            "https://api.github.com",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {env.main.GH_TOKEN}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        async with self._session.get(f"/orgs/{ORG_NAME}/repos") as resp:
            resp.raise_for_status()
            self.repositories = tuple(r["name"] for r in await resp.json())  # type: ignore

    async def close(self) -> None:
        await self._session.close()

    async def get_item(self, repository: str, number: int) -> Item | None:
        r = await self._session.get(f"/repos/{ORG_NAME}/{repository}/issues/{number}")
        if not r.ok:
            if r.status in (404, 410):
                return None
            r.raise_for_status()
        data = await r.json()
        item_type = ItemType.PR if "pull_request" in data else ItemType.ISSUE
        state = State(data["state"])
        if item_type == ItemType.PR and state == State.CLOSED and data["pull_request"]["merged_at"] is not None:
            state = State.MERGED
        return Item(number, data["title"], data["html_url"], state, item_type)

    async def create_issue(self, repository: str, title: str, labels: list[str], body: str | None) -> tuple[str, int]:
        payload = {"title": title, "labels": labels}
        if body:
            payload["body"] = body

        r = await self._session.post(f"/repos/{ORG_NAME}/{repository}/issues", json=payload)
        r.raise_for_status()
        data = await r.json()
        url: str = data["html_url"]
        number: int = data["number"]

        return url, number
