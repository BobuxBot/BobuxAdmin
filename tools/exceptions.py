from disnake.ext.commands import CommandError


class TimeConversionError(CommandError):
    def __init__(self, arg: str):
        super().__init__(
            f"Could not convert `{arg}` to time. Time examples: `2h5m`, `10h`"
        )
