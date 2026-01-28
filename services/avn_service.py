import json
import os
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _search_total(query: str) -> int:
    endpoint = os.getenv("AVN_SEARCH_ENDPOINT", "https://avn.com/api/search")
    timeout = float(os.getenv("AVN_SEARCH_TIMEOUT", "20"))
    payload = urlencode({"q": query, "page": 1}).encode("utf-8")
    req = Request(
        endpoint,
        data=payload,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return int(data.get("total") or 0)


def compute_avn_scores(names: list[str]) -> dict[str, int]:
    if not names:
        return {}

    sleep_seconds = float(os.getenv("AVN_SLEEP_SECONDS", "1"))
    raw_totals: dict[str, int] = {}

    for name in names:
        raw_totals[name] = _search_total(name)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    max_value = max(raw_totals.values() or [0])
    if max_value <= 0:
        return {name: 0 for name in names}

    scores: dict[str, int] = {}
    for name, value in raw_totals.items():
        normalized = round((value / max_value) * 20)
        scores[name] = max(0, min(20, int(normalized)))

    return scores
