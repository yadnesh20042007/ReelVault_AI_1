import re

from app.schemas.domain import EvDate, Extracted, EvStr, FetchedPost


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()


def contains(haystack: str, needle: str) -> bool:
    return bool(needle) and norm(needle) in norm(haystack)


def ground(ex: Extracted, post: FetchedPost) -> tuple[Extracted, list[str]]:
    source = f"{post.transcript or ''}\n{post.caption or ''}"
    dropped: list[str] = []

    def check(name: str, f: EvStr | EvDate):
        if f.value is not None and not (f.quote and contains(source, f.quote)):
            dropped.append(name)
            f.value, f.quote = None, None

    for name in ("title", "organizer", "deadline_raw", "deadline", "eligibility", "reward", "mode", "location"):
        check(name, getattr(ex, name))
    if ex.deadline_raw.value is None and ex.deadline.value is not None:
        ex.deadline.value = None
        dropped.append("deadline(no raw)")
    ex.links = [l for l in ex.links if l.value and l.quote and contains(source, l.quote)]
    return ex, dropped
