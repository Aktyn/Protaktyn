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


def linearly_weighted_average(values: list[float]):
    sum_ = 0.

    for index, value in enumerate(values):
        sum_ += value * (index + 1)

    values_count = len(values)
    weights_sum = (values_count ** 2 + values_count) / 2
    return sum_ / weights_sum
