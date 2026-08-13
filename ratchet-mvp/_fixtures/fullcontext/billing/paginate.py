"""Pagination helper — here to make the subsystem realistic context, unrelated to the task."""


def paginate(items, page_size: int = 50):
    for start in range(0, len(items), page_size):
        yield items[start:start + page_size]
