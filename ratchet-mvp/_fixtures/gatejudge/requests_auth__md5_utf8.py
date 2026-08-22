            def md5_utf8(x: str | bytes) -> str:
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.md5(x, usedforsecurity=False).hexdigest()
