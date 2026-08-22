            def sha256_utf8(x: str | bytes) -> str:
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.sha256(x, usedforsecurity=False).hexdigest()
