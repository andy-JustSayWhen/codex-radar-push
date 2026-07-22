#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from codex_radar_push.features.radar_refresh_alert.runner import run


def main() -> int:
    message = run()
    if message:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
