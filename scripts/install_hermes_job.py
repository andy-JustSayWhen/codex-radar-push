#!/usr/bin/env python3
import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path


HERMES_DATA_DIR = Path(os.environ.get("HERMES_DATA_DIR", "/opt/data"))
JOBS_PATH = HERMES_DATA_DIR / "cron/jobs.json"
SCRIPTS_DIR = HERMES_DATA_DIR / "scripts"
PROJECT_DIR = Path(os.environ.get("CODEX_RADAR_PROJECT_DIR", str(HERMES_DATA_DIR / "codex-radar-push")))
OLD_JOB_NAMES = {"codexradar-model-iq"}
NEW_JOB_ID = "codexradarrefresh"
NEW_JOB_NAME = "codexradar-refresh-alert"
WRAPPER_SCRIPT = "codex_radar_refresh_watch.py"
SCHEDULE_EXPR = "5 * * * *"


def main() -> int:
    delivery_target = os.environ.get("CODEX_RADAR_DELIVERY_TARGET", "").strip()
    if ":" not in delivery_target:
        raise ValueError("CODEX_RADAR_DELIVERY_TARGET must use platform:chat_id format")
    delivery_platform, delivery_chat_id = delivery_target.split(":", 1)
    if not JOBS_PATH.exists():
        raise FileNotFoundError(f"Hermes jobs file not found: {JOBS_PATH}")
    install_wrapper_script()

    payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    jobs = payload.get("jobs", [])

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = JOBS_PATH.with_name(f"jobs.json.bak-{timestamp}-codex-radar-refresh")
    shutil.copy2(JOBS_PATH, backup_path)

    jobs = [
        job
        for job in jobs
        if job.get("id") != NEW_JOB_ID
        and job.get("name") != NEW_JOB_NAME
        and job.get("name") not in OLD_JOB_NAMES
    ]

    now = datetime.now(timezone.utc)
    new_job = {
        "id": NEW_JOB_ID,
        "name": NEW_JOB_NAME,
        "prompt": "",
        "skills": [],
        "skill": None,
        "model": None,
        "provider": None,
        "base_url": None,
        "script": WRAPPER_SCRIPT,
        "no_agent": True,
        "context_from": None,
        "schedule": {
            "kind": "cron",
            "expr": SCHEDULE_EXPR,
            "display": SCHEDULE_EXPR,
        },
        "schedule_display": SCHEDULE_EXPR,
        "repeat": {
            "times": None,
            "completed": 0,
        },
        "enabled": True,
        "state": "scheduled",
        "paused_at": None,
        "paused_reason": None,
        "created_at": now.isoformat(),
        "next_run_at": (now + timedelta(hours=1)).isoformat(),
        "last_run_at": None,
        "last_status": None,
        "last_error": None,
        "last_delivery_error": None,
        "deliver": delivery_target,
        "origin": {
            "platform": delivery_platform,
            "chat_id": delivery_chat_id,
            "chat_name": None,
            "thread_id": None,
        },
        "enabled_toolsets": None,
        "workdir": str(PROJECT_DIR),
        "fire_claim": None,
    }
    jobs.append(new_job)
    payload["jobs"] = jobs
    payload["updated_at"] = now.isoformat()
    JOBS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"installed {NEW_JOB_NAME}")
    print(f"backup {backup_path}")
    return 0


def install_wrapper_script() -> None:
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    wrapper_path = SCRIPTS_DIR / WRAPPER_SCRIPT
    wrapper_path.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "import sys\n"
        "\n"
        f"os.chdir({str(PROJECT_DIR)!r})\n"
        "os.execv(sys.executable, [sys.executable, \"scripts/codex_radar_refresh_watch.py\"])\n",
        encoding="utf-8",
    )
    wrapper_path.chmod(0o755)


if __name__ == "__main__":
    raise SystemExit(main())
