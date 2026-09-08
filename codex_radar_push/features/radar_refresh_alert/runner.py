from datetime import datetime
from pathlib import Path
import time
from urllib.error import URLError
from zoneinfo import ZoneInfo

from codex_radar_push.core.codex_radar_client import fetch_intelligence, fetch_html
from codex_radar_push.core.radar_display import format_radar_message
from codex_radar_push.core.radar_parser import parse_radar_snapshot
from codex_radar_push.core.state_store import changed_sections, load_state, save_state

DEFAULT_STATE_PATH = Path("/opt/data/codex-radar-push/state/radar-refresh-state.json")
MIN_ALERT_INTERVAL_SECONDS = 10 * 60
QUIET_TIMEZONE = ZoneInfo("Asia/Shanghai")
QUIET_START_HOUR = 23
QUIET_END_HOUR = 7


def evaluate_snapshot(
    snapshot,
    state_path: Path = DEFAULT_STATE_PATH,
    now: float | None = None,
) -> tuple[list[str], str]:
    state = load_state(state_path)
    changed = changed_sections(state, snapshot)
    metadata = _state_metadata(state)
    if not changed:
        save_state(state_path, snapshot, metadata)
        return [], ""

    current_time = time.time() if now is None else now
    last_alert_at = float(state.get("last_alert_at") or 0)
    if last_alert_at and current_time - last_alert_at < MIN_ALERT_INTERVAL_SECONDS:
        # Keep the last reported baseline so additions remain pending after cooldown.
        return [], ""

    metadata["last_alert_at"] = current_time
    metadata["last_alert_sections"] = changed
    save_state(state_path, snapshot, metadata)
    return changed, format_message(snapshot, changed)


def format_message(snapshot, changed: list[str]) -> str:
    message = format_radar_message(snapshot, changed, "Codex 雷达刷新")
    if "```" in message:
        return message
    return f"```text\n{message}\n```"


def run(state_path: Path = DEFAULT_STATE_PATH, now: float | None = None) -> str:
    current_time = time.time() if now is None else now
    if is_quiet_time(current_time):
        return ""
    try:
        intelligence = fetch_intelligence()
        html = fetch_html()
    except (OSError, TimeoutError, URLError):
        return ""
    snapshot = parse_radar_snapshot({}, html, intelligence)
    _, message = evaluate_snapshot(snapshot, state_path, current_time)
    return message


def is_quiet_time(now: float | None = None) -> bool:
    current_time = time.time() if now is None else now
    hour = datetime.fromtimestamp(current_time, QUIET_TIMEZONE).hour
    return hour >= QUIET_START_HOUR or hour < QUIET_END_HOUR


def _state_metadata(state: dict) -> dict:
    keys = (
        "last_alert_at",
        "last_alert_sections",
        "last_suppressed_at",
        "last_suppressed_sections",
    )
    return {key: state[key] for key in keys if key in state}
