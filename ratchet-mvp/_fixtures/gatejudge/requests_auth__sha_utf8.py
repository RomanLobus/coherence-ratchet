            def sha_utf8(x: str | bytes) -> str:
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.sha1(x, usedforsecurity=False).hexdigest()
