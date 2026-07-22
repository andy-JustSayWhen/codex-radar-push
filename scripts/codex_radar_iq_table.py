#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from codex_radar_push.core.codex_radar_client import fetch_current_json
from codex_radar_push.core.iq_table import format_iq_table


def main() -> None:
    current = fetch_current_json()
    print(format_iq_table(current.get("model_iq") or {}))


if __name__ == "__main__":
    main()
