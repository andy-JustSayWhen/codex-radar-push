import re
from typing import Any

from codex_radar_push.core.models import RadarSection, RadarSnapshot
from codex_radar_push.shared.text import collapse_spaces, html_section, strip_tags


def parse_radar_snapshot(current_json: dict[str, Any], html: str) -> RadarSnapshot:
    return RadarSnapshot(
        sections={
            "reset": _parse_reset(html),
            "quota": _parse_quota(html),
            "iq": _parse_iq(current_json, html),
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


def _parse_iq(current_json: dict[str, Any], html: str) -> RadarSection:
    section = html_section(html, "model-iq")
    text = strip_tags(section)

    updated_at = ""
    match = re.search(r"降智雷达\s*([0-9]+月[0-9]+日[0-9:]+更新)", text)
    if match:
        updated_at = match.group(1)

    model_iq = current_json.get("model_iq", {}) or {}
    summary_parts = _parse_iq_cards(model_iq, section)
    run_cost = _parse_iq_run_cost(text)
    trend = _parse_iq_recent_trend(model_iq)
    summary = "\n".join([part for part in (run_cost, *summary_parts, trend) if part])
    if summary:
        latest_date = str((model_iq.get("latest", {}) or {}).get("date", ""))
        return RadarSection("iq", "智商雷达", updated_at or latest_date, summary)

    latest = model_iq.get("latest", {}) or {}
    return RadarSection("iq", "智商雷达", updated_at or str(latest.get("date", "")), _format_iq_latest(latest))


def _parse_iq_run_cost(text: str) -> str:
    match = re.search(r"(本次 Codex 多模型智商测试共消耗等价 \$[\d.]+ 的 API 费用。)", text)
    return collapse_spaces(match.group(1)) if match else ""


def _parse_iq_cards(model_iq: dict[str, Any], section: str) -> list[str]:
    card_pattern = re.compile(
        r'<div class="model-iq-score-chip[^"]*"[^>]*data-model-key="([^"]+)"[^>]*>'
        r'.*?<span>([^<]+)</span>'
        r'.*?<strong>([^<]+)</strong>'
        r'.*?<span class="model-iq-score-mini">([^<]+)</span>'
        r'.*?<span class="model-iq-score-mini">([^<]+)</span>',
        flags=re.DOTALL | re.IGNORECASE,
    )
    cards = []
    for match in card_pattern.finditer(section):
        key, label, score, cost, duration = match.groups()
        metrics = _iq_metrics_for_card(model_iq, key, label)
        status = metrics.get("status", "")
        passed = metrics.get("passed", "")
        tasks = metrics.get("tasks", "")
        date = metrics.get("date", "")
        result = f"{collapse_spaces(label)} {score}"
        if status:
            result += f" ({status})"
        if passed != "" and tasks != "":
            result += f" {passed}/{tasks}"
        result += f" 费用 {cost} 耗时 {duration}"
        if date:
            result += f" date={date}"
        cards.append(result)
    return cards


def _iq_metrics_for_card(model_iq: dict[str, Any], key: str, label: str) -> dict[str, Any]:
    if key == "gpt_55_xhigh":
        return model_iq.get("latest", {}) or {}

    comparison = (model_iq.get("comparisons", {}) or {}).get(key, {}) or {}
    if comparison.get("latest"):
        return comparison.get("latest", {}) or {}

    normalized_label = label.lower().replace("gpt-", "gpt_").replace(".", "").replace("-", "_")
    for comparison_key, comparison_value in (model_iq.get("comparisons", {}) or {}).items():
        if comparison_key == normalized_label:
            return comparison_value.get("latest", {}) or {}
    return {}


def _parse_iq_recent_trend(model_iq: dict[str, Any]) -> str:
    recent_days = (model_iq.get("latest", {}) and model_iq.get("recent_days", [])) or []
    if not recent_days:
        return ""

    recent = recent_days[-5:]
    points = []
    for item in recent:
        date = item.get("date", "")
        score = item.get("score", "")
        status = item.get("status", "")
        passed = item.get("passed", "")
        tasks = item.get("tasks", "")
        if date and score != "":
            suffix = f" {passed}/{tasks}" if passed != "" and tasks != "" else ""
            state = f" ({status})" if status else ""
            points.append(f"{date}: {score}{state}{suffix}")
    return "GPT-5.5-xhigh近5次：" + " → ".join(points) if points else ""


def _format_iq_latest(latest: dict[str, Any]) -> str:
    model = str(latest.get("model") or "gpt-5.5").lower()
    effort = str(latest.get("reasoning_effort") or "").lower()
    score = latest.get("score", "")
    status = latest.get("status", "")
    passed = latest.get("passed", "")
    tasks = latest.get("tasks", "")
    date = latest.get("date", "")

    name = f"{model}-{effort}" if effort else model
    summary = f"{name} {score} ({status}) {passed}/{tasks} date={date}"
    return collapse_spaces(summary)
