import math


def clamp_f(value: float, min_: float, max_: float):
    return max(min(value, max_), min_)


def clamp_i(value: int, min_: int, max_: int):
    return max(min(value, max_), min_)


def mix(v1: float, v2: float, factor: float):
    return v1 * (1 - factor) + v2 * factor


def normalize_array(array: list[float], try_handle_small_values=True):
    min_value = min(0.0, min(array))
    max_value = max(array) - min_value
    if max_value < 1e-8:
        if not try_handle_small_values:
            return array
        scaled = [(x - min_value) * 1e8 for x in array]
        return normalize_array(scaled, False)
    return [(x - min_value) / max_value for x in array]


def linearly_weighted_average(values: list[float], reverse=False):
    sum_ = 0.
    if len(values) == 0:
        return 0.
    values_count = len(values)
    # sum of sequence of consecutive integer numbers in range [1, values_count]
    weights_sum = (values_count ** 2 + values_count) / 2

    for index, value in enumerate(values):
        sum_ += value * (index + 1 if not reverse else values_count - index)

    return sum_ / weights_sum


def distance_sqr(pos1: tuple[float, float], pos2: tuple[float, float]):
    """
    Args:
        pos1: position of the first point
        pos2: position of the second point

    Returns: squared distance between two points.
    """
    return (pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2


def distance(pos1: tuple[float, float], pos2: tuple[float, float]):
    """
    Args:
        pos1: position of the first point
        pos2: position of the second point

    Returns: distance between two points.
    """
    return math.sqrt(distance_sqr(pos1, pos2))
