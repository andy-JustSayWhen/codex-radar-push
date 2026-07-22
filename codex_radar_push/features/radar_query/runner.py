from codex_radar_push.core.codex_radar_client import fetch_current_json, fetch_html
from codex_radar_push.core.radar_display import format_radar_message
from codex_radar_push.core.radar_parser import parse_radar_snapshot

ALL_SECTIONS = ["reset", "quota", "iq"]


def resolve_query_sections(query: str) -> list[str]:
    normalized = (query or "").lower().replace(" ", "")
    if "额度" in normalized or "quota" in normalized:
        return ["quota"]
    if "智商" in normalized or "降智" in normalized or "iq" in normalized:
        return ["iq"]
    if "重置" in normalized or "reset" in normalized:
        return ["reset"]
    return list(ALL_SECTIONS)


def format_query_response(snapshot, section_keys: list[str]) -> str:
    return format_radar_message(snapshot, section_keys, "Codex 雷达最新状态")


def query_latest(query: str = "") -> str:
    current = fetch_current_json()
    html = fetch_html()
    snapshot = parse_radar_snapshot(current, html)
    return format_query_response(snapshot, resolve_query_sections(query))
