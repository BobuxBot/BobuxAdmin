from typing import Iterable


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
