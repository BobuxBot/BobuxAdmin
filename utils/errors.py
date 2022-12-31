from disnake.ext import commands


class CustomError(commands.CommandError):
    pass


class TimeConversionFailure(CustomError):
    def __init__(self, arg: str):
        super().__init__(f"Could not convert `{arg}` to time")


class HierarchyError(CustomError):
    def __init__(self):
        super().__init__("You cannot use this command on someone with equal or higher top role than you.")
