"""Zero-dependency test runner, for when pytest is not installed.

    python3 tests/run.py
"""

import importlib
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main() -> int:
    modules = sorted(
        f[:-3] for f in os.listdir(HERE)
        if f.startswith("test_") and f.endswith(".py")
    )
    passed = total = 0
    for modname in modules:
        t = importlib.import_module(modname)
        for name in [n for n in dir(t) if n.startswith("test_")]:
            total += 1
            try:
                getattr(t, name)()
                print(f"  PASS  {modname}.{name}")
                passed += 1
            except Exception:
                print(f"  FAIL  {modname}.{name}")
                traceback.print_exc()
    print(f"\n{passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
