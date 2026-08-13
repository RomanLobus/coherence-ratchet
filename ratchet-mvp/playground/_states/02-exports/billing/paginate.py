def paginate(items, page_size=50):
    pages = []
    for start in range(0, len(items), page_size):
        pages.append(items[start:start + page_size])
    return pages
