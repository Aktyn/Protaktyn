def clamp_f(value: float, min_: float, max_: float):
    return max(min(value, max_), min_)


def clamp_i(value: int, min_: int, max_: int):
    return max(min(value, max_), min_)


def mix(v1: float, v2: float, factor: float):
    return v1 * (1 - factor) + v2 * factor
