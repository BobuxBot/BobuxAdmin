from datetime import timedelta
from re import search

from disnake.ext.commands import Converter, converter_method

from tools.exceptions import TimeConversionError


class TimeConverter(Converter):
    @converter_method
    async def convert(self, _, arg: str) -> timedelta:
        arg = arg.lower().replace(" ", "")  # lower the string and remove spaces
        values = {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}
        for k in values.copy():
            try:
                value = search(
                    "\d+" + k[0], arg
                ).group()  # search for a number that stands next to a certain letter
                values[k] = int(value.replace(k[0], ""))  # extract the number
            except:
                pass  # if the number wasn't found, just leave it with the default value - 0

        if all(i == 0 for i in values.values()):
            raise TimeConversionError(arg)

        return timedelta(**values)
