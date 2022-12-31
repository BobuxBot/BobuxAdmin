from datetime import datetime, timedelta
from typing import Iterable

import disnake


def get_reason(inter: disnake.Interaction, reason: str, duration: timedelta | None = None) -> str:
    s = f"Responsible moderator: {inter.user} | Reason: {reason}"
    if duration is not None:
        s += f" | Duration: {duration}"
    return s


def get_duration_end_ts(duration: timedelta) -> int:
    return int((datetime.now() + duration).timestamp())


def join_and(sep: str, iterable: Iterable[str]) -> str:
    seq = list(iterable)
    if len(seq) == 0:
        raise TypeError("Cannot join an empty sequence")
    elif len(seq) == 1:
        return seq[0]
    elif len(seq) == 2:
        return " and ".join(seq)
    return sep.join(seq[:-1]) + " and " + seq[-1]


def n_s(num: int) -> str:
    n = str(num)
    return "s" if not n.endswith("1") or n.endswith("11") else ""
