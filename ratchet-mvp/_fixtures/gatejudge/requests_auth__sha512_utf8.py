            def sha512_utf8(x: str | bytes) -> str:
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.sha512(x, usedforsecurity=False).hexdigest()
