import re


def parse_random_args(message: str) -> tuple[int | None, int | None, list[str]]:
    s = re.sub(r"^/?cf\s+random\s*", "", message, flags=re.IGNORECASE)
    if not s:
        return None, None, []

    rating_low = None
    rating_high = None
    tags: list[str] = []
    tokens = [x for x in s.split() if x]
    i = 0
    while i < len(tokens):
        token = tokens[i]
        low_high = None
        lower = token.lower()
        if lower.startswith("rating="):
            low_high = _parse_rating(token.split("=", 1)[1])
        elif lower.startswith("r="):
            low_high = _parse_rating(token.split("=", 1)[1])
        elif lower.startswith("tag="):
            raw = token.split("=", 1)[1]
            while i + 1 < len(tokens):
                nxt = tokens[i + 1]
                nxt_lower = nxt.lower()
                if "=" in nxt or nxt_lower.startswith(("rating=", "r=", "tag=", "tags=")):
                    break
                if _parse_rating(nxt) is not None:
                    break
                raw += f" {nxt}"
                i += 1
            tags.extend(_parse_tags(raw))
            i += 1
            continue
        elif lower.startswith("tags="):
            raw = token.split("=", 1)[1]
            while i + 1 < len(tokens):
                nxt = tokens[i + 1]
                nxt_lower = nxt.lower()
                if "=" in nxt or nxt_lower.startswith(("rating=", "r=", "tag=", "tags=")):
                    break
                if _parse_rating(nxt) is not None:
                    break
                raw += f" {nxt}"
                i += 1
            tags.extend(_parse_tags(raw))
            i += 1
            continue
        else:
            low_high = _parse_rating(token)
            if low_high is None:
                tags.extend(_parse_tags(token))
                i += 1
                continue

        if low_high is not None:
            rating_low, rating_high = low_high
        i += 1

    tags = [t.strip().lower() for t in tags if t.strip()]
    dedup_tags = []
    seen = set()
    for t in tags:
        if t in seen:
            continue
        seen.add(t)
        dedup_tags.append(t)
    return rating_low, rating_high, dedup_tags


def _parse_rating(value: str) -> tuple[int, int] | None:
    v = value.strip()
    if re.fullmatch(r"\d{3,4}", v):
        r = int(v)
        return r, r

    m = re.fullmatch(r"(\d{3,4})-(\d{3,4})", v)
    if not m:
        return None

    a, b = int(m.group(1)), int(m.group(2))
    if a > b:
        a, b = b, a
    return a, b


def _parse_tags(value: str) -> list[str]:
    return [x.strip().lower() for x in value.split(",") if x.strip()]
