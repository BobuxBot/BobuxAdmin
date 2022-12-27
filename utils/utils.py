from datetime import datetime, timedelta

import disnake


def get_reason(inter: disnake.Interaction, reason: str, duration: timedelta | None = None) -> str:
    s = f"Responsible moderator: {inter.user} | Reason: {reason}"
    if duration is not None:
        s += f" | Duration: {duration}"
    return s


def get_duration_end_ts(duration: timedelta) -> int:
    return int((datetime.now() + duration).timestamp())
