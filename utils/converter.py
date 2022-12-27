from datetime import timedelta
from re import search

import disnake
from disnake.ext.commands import Converter, converter_method

from utils.errors import TimeConversionFailure


class TimeConverter(Converter, timedelta):
    @converter_method
    async def convert(self, inter: disnake.ApplicationCommandInteraction, argument: str) -> timedelta:
        arg = argument.lower().replace(" ", "")
        values = {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}
        for k in values.copy():
            try:
                value = search(r"\d+" + k[0], arg).group()
                values[k] = int(value.replace(k[0], ""))
            except (AttributeError, ValueError):
                pass

        delta = timedelta(**values)
        if delta.total_seconds() == 0:
            raise TimeConversionFailure(argument)

        return delta.total_seconds()
