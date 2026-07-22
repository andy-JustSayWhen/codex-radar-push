#!/usr/bin/env python3
import os
import sys

os.chdir("/opt/data/codex-radar-push")
os.execv(sys.executable, [sys.executable, "scripts/codex_radar_refresh_watch.py"])
