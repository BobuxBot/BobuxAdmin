from datetime import timedelta, datetime


def to_discord_timestamp(delta: timedelta):
    return f"<t:{int((datetime.now() + delta).timestamp())}>"
