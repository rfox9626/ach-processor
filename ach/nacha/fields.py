def num(value, width) -> str:
    return str(value).rjust(width, "0")


def alpha(text, width) -> str:
    return text.upper()[:width].ljust(width, " ")


def check_digit(routing8: str) -> str:
    weights = [3, 7, 1, 3, 7, 1, 3, 7]
    total = sum(int(d) * w for d, w in zip(routing8, weights, strict=True))
    return str((10 - total % 10) % 10)
