def convert(timer):
    pos = ["s", "m", "h", "d"]
    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}
    unit = timer[-1]

    if unit not in pos:
        return -1
    try:
        val = int(timer[:-1])
    except ValueError:
        return -2

    return val * time_dict[unit]
