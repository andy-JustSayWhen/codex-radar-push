import os
from pathlib import Path
import subprocess
import sys


def reply_to_radar(*, platform, text, source, **_):
    if platform != "feishu" or source.get("chat_type") != "dm":
        return None
    if "".join(text.lower().split()) not in {"codex智商", "codex降智"}:
        return None

    data_dir = Path(__file__).resolve().parents[2]
    project = Path(os.environ.get("CODEX_RADAR_PROJECT_DIR") or data_dir / "radar")
    script = project / "scripts" / "codex_radar_iq_table.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=project, capture_output=True, encoding="utf-8", timeout=25, check=True,
        )
        reply = result.stdout.strip()
    except (OSError, UnicodeError, subprocess.SubprocessError):
        reply = ""
    return {"action": "handled", "reply": reply or "暂时读不到智商榜单，请稍后再试。"}


def register(context):
    context.register_hook("post_gateway_admission", reply_to_radar)
