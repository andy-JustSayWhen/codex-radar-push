# ADR 0001: Hermes Cron Script Location

## Status

Accepted

## Context

Hermes `no_agent` cron jobs resolve the `script` field relative to `HERMES_HOME/scripts`. The job must reference the installed wrapper name rather than a project-relative path.

Hermes therefore looked for `/opt/data/scripts/scripts/codex_radar_refresh_watch.py` and emitted repeated failure notifications:

```text
Script not found: /opt/data/scripts/scripts/codex_radar_refresh_watch.py
```

## Decision

Keep project source code under `/opt/data/codex-radar-push`, but install a thin Python wrapper script in `/opt/data/scripts/codex_radar_refresh_watch.py`.

The Hermes cron job must store:

```json
{
  "script": "codex_radar_refresh_watch.py",
  "workdir": "/opt/data/codex-radar-push"
}
```

Hermes executes cron scripts with Python, so the wrapper must be valid Python even if it has a shebang. The wrapper changes into the project directory and executes the real feature entrypoint:

```python
import os
import sys

os.chdir("/opt/data/codex-radar-push")
os.execv(sys.executable, [sys.executable, "scripts/codex_radar_refresh_watch.py"])
```

## Consequences

- Hermes cron remains compatible with its script sandbox.
- Project code keeps FCMA layout and does not need to live under `/opt/data/scripts`.
- Future installers must create or update the wrapper whenever they install the cron job.
- Do not set the cron `script` field to `scripts/...` for this project.
