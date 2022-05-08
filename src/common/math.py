def clamp_f(value: float, min_: float, max_: float):
    return max(min(value, max_), min_)


def clamp_i(value: int, min_: int, max_: int):
    return max(min(value, max_), min_)
