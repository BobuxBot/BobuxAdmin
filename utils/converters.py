from datetime import timedelta

import disnake
from disnake.ext.commands import Converter, converter_method
from durations_nlp import Duration

from utils.errors import TimeConversionFailure


class TimeConverter(Converter, timedelta):
    @converter_method
    async def convert(self, inter: disnake.ApplicationCommandInteraction, argument: str) -> timedelta:
        duration = Duration(argument)
        delta = timedelta(seconds=duration.to_seconds())
        if delta.total_seconds() == 0:
            raise TimeConversionFailure(argument)

        return delta
