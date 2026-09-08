import re
from typing import Any

from codex_radar_push.core.models import RadarSection, RadarSnapshot
from codex_radar_push.core.intelligence import IntelligenceReport
from codex_radar_push.core.iq_table import format_intelligence_table, format_iq_table
from codex_radar_push.shared.text import collapse_spaces, html_section, strip_tags


def parse_radar_snapshot(current_json: dict[str, Any], html: str, intelligence: IntelligenceReport | None = None) -> RadarSnapshot:
    return RadarSnapshot(
        sections={
            "reset": _parse_reset(html),
            "quota": _parse_quota(html),
            "iq": _parse_iq(current_json, intelligence),
        }
    )


def _parse_reset(html: str) -> RadarSection:
    section = html_section(html, "reset-judgement")
    text = strip_tags(section)

    updated_at = ""
    match = re.search(r"重置雷达研判\s*([0-9]+月[0-9]+日[0-9:]+研判)", text)
    if match:
        updated_at = match.group(1)

    cards = []
    for title in ("发重置卡", "硬重置"):
        match = re.search(rf"{title}\s+([^\n]+)", text)
        if match:
            cards.append(f"{title}：{collapse_spaces(match.group(1))}")

    if not cards:
        cards.append(collapse_spaces(text)[:240])

    change_basis = _reset_change_basis(section, cards, text)
    return RadarSection("reset", "重置雷达", updated_at, "\n".join(cards), change_basis)


def _reset_change_basis(section: str, cards: list[str], text: str) -> str:
    signal = _reset_signal(section)
    action_parts = [part for part in (signal, *cards) if part]
    if action_parts:
        return "\n".join(action_parts)
    without_heading_time = re.sub(r"重置雷达研判\s*[0-9]+月[0-9]+日[0-9:]+研判", "", text)
    without_inline_time = re.sub(r"[0-9]+月[0-9]+日[0-9:]+研判", "", without_heading_time)
    return collapse_spaces(without_inline_time)


def _reset_signal(section: str) -> str:
    match = re.search(r'<div class="reset-judgement-head"[^>]*>.*?<strong>([^<]+)</strong>', section, flags=re.DOTALL)
    return collapse_spaces(match.group(1)) if match else ""


def _parse_quota(html: str) -> RadarSection:
    section = html_section(html, "quota-radar")
    text = strip_tags(section)

    updated_at = ""
    match = re.search(r"额度雷达\s*([0-9]+月[0-9]+日[0-9:]+更新)", text)
    if match:
        updated_at = match.group(1)

    rows = []
    row_pattern = re.compile(
        r"(20x Pro|5x Pro|Plus)\s+(\$[\d,.]+)\s+(\$[\d,.]+)\s+(实测|推测)"
    )
    for match in row_pattern.finditer(text):
        rows.append(
            f"{match.group(1)} 5h {match.group(2)} / 7d {match.group(3)} ({match.group(4)})"
        )

    trend = ""
    match = re.search(r"额度变化趋势\s+([^\n]+)", text)
    if match:
        trend = f"趋势：{collapse_spaces(match.group(1))}"

    recent_trend = _parse_quota_recent_trend(text)

    formula = ""
    match = re.search(r"本次公式：(.+?)(?:\n|$)", text)
    if match:
        formula = f"公式：{collapse_spaces(match.group(1))}"

    summary_parts = rows + [part for part in (trend, recent_trend, formula) if part]
    summary = "\n".join(summary_parts) if summary_parts else collapse_spaces(text)[:240]
    return RadarSection("quota", "额度雷达", updated_at, summary)


def _parse_quota_recent_trend(text: str) -> str:
    points = re.findall(r"(2026-[0-9]{2}-[0-9]{2}(?:-[a-z0-9_]+)?)\s+20x Pro 7d\s+(\$[\d,.]+)", text)
    if not points:
        return ""
    recent = points[-5:]
    return "近5次：" + " | ".join(f"{date} {value}" for date, value in recent)


def _parse_iq(current_json: dict[str, Any], intelligence: IntelligenceReport | None) -> RadarSection:
    if intelligence is not None:
        return RadarSection("iq", "智商雷达", intelligence.software_updated_at,
                            format_intelligence_table(intelligence), intelligence.change_basis)
    # Compatibility for callers with an explicit historical snapshot; live callers
    # must fetch the intelligence report and never fall back to this structure.
    model_iq = current_json.get("model_iq") or {}
    latest = model_iq.get("latest") or {}
    if not latest and not model_iq.get("comparisons"):
        return RadarSection("iq", "智商雷达", "", "")
    return RadarSection("iq", "智商雷达", str(model_iq.get("updated_at") or latest.get("date") or ""),
                        format_iq_table(model_iq))
