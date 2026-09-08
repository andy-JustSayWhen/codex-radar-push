from codex_radar_push.core.codex_radar_client import fetch_intelligence, fetch_html
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
    if section_keys == ["iq"]:
        return snapshot.sections["iq"].summary
    return format_radar_message(snapshot, section_keys, "Codex 雷达最新状态")


def query_latest(query: str = "") -> str:
    sections = resolve_query_sections(query)
    intelligence = fetch_intelligence() if "iq" in sections else None
    html = fetch_html() if any(key in sections for key in ("quota", "reset")) else ""
    snapshot = parse_radar_snapshot({}, html, intelligence)
    return format_query_response(snapshot, sections)
