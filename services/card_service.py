def clamp_card_value(value: int | None) -> int | None:
    if value is None:
        return None
    return max(0, min(20, int(value)))


def compute_power_score(values: list[int | None]) -> int:
    return sum(v or 0 for v in values)


def compute_star_rating(score: int) -> int:
    if score <= 0:
        return 0
    return max(1, min(5, int(round(score / 20))))
