#!/usr/bin/env python3
"""Install as codex_radar_iq_table.py in the Hermes scripts directory."""
import os
from pathlib import Path
import runpy


project = os.environ.get("CODEX_RADAR_PROJECT_DIR")
project_dir = Path(project) if project else Path(__file__).resolve().parents[1] / "codex-radar-push"
runpy.run_path(str(project_dir / "scripts" / "codex_radar_iq_table.py"), run_name="__main__")
