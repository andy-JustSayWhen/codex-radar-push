import re
from dataclasses import dataclass

from codex_radar_push.core.models import RadarSection, RadarSnapshot


def format_radar_message(snapshot: RadarSnapshot, section_keys: list[str], title: str) -> str:
    lines = [f"{title}  {_message_date(snapshot, section_keys)}".rstrip()]
    for key in section_keys:
        section = snapshot.sections[key]
        if key == "reset":
            lines.extend(["", *_format_reset(section)])
        elif key == "quota":
            lines.extend(["", *_format_quota(section)])
        elif key == "iq":
            lines.extend(["", *_format_iq(section)])
    lines.extend(["", "数据来自 Codex 雷达 codexradar.com"])
    return "\n".join(lines)


def _message_date(snapshot: RadarSnapshot, section_keys: list[str]) -> str:
    for key in section_keys:
        match = re.search(r"([0-9]+月[0-9]+日)", snapshot.sections[key].updated_at)
        if match:
            return match.group(1)
    return ""


def _section_time(updated_at: str) -> str:
    match = re.search(r"([0-9]{1,2}:[0-9]{2})", updated_at)
    return match.group(1) if match else updated_at


def _format_reset(section: RadarSection) -> list[str]:
    cards = _summary_lines(section.summary)
    reset_card = _strip_label(_find_line(cards, "发重置卡"), "发重置卡")
    hard_reset = _strip_label(_find_line(cards, "硬重置"), "硬重置")
    lines = [f"重置雷达  {_section_time(section.updated_at)}"]
    if reset_card:
        lines.append(f"重置卡：{reset_card}")
    if hard_reset:
        lines.append(f"硬重置：{hard_reset}")
    if len(lines) == 1 and section.summary:
        lines.extend(_summary_lines(section.summary))
    return lines


def _format_quota(section: RadarSection) -> list[str]:
    lines = [f"额度雷达  {_section_time(section.updated_at)}", "当前额度"]
    rows = _quota_rows(section.summary)
    for row in rows:
        lines.append(f"{row.tier:<7}  5h {row.five_h:>8}  7d {row.seven_d:>10}  {row.source}")
    if not rows and section.summary:
        lines.extend(_summary_lines(section.summary))

    change = _quota_change(section.summary)
    trend = _quota_trend(section.summary)
    if trend:
        labels = " → ".join(_money_short(value) for _, value in trend)
        lines.extend(["", "20x Pro 7d 近5次", labels, _sparkline([_money_to_float(value) for _, value in trend])])
    if change:
        lines.append(f"本次变化：{change}")
    return lines


def _format_iq(section: RadarSection) -> list[str]:
    if section.summary.startswith(("智商雷达：", "降智雷达：")):
        return section.summary.splitlines()
    lines = [f"智商雷达  {_section_time(section.updated_at)}"]
    cost = re.search(r"本次 Codex 多模型智商测试共消耗等价 (\$[\d.]+) 的 API 费用", section.summary)
    if cost:
        lines.append(f"本次成本：{cost.group(1)}")

    cards = _iq_cards(section.summary)
    if not cards and section.summary:
        lines.extend(_summary_lines(section.summary))
        return lines
    if cards:
        lines.append("")
    for card in cards:
        lines.append(f"{card.name:<16} {card.score:g} {card.status:<6} {card.passed}/{card.tasks}")
        lines.append(f"{_score_bar(card.score)}  {card.cost}  {card.duration}")
        lines.append("")

    quality_recommendation = _recommend_quality_iq_card(cards)
    value_recommendation = _recommend_value_iq_card(cards)
    if quality_recommendation:
        lines.append(f"保质量：{quality_recommendation.name}（{quality_recommendation.score:g} {quality_recommendation.status}，{quality_recommendation.passed}/{quality_recommendation.tasks}）")
    if value_recommendation:
        lines.append(f"性价比：{value_recommendation.name}（{value_recommendation.score:g} {value_recommendation.status}，{value_recommendation.cost}，{value_recommendation.duration}）")
    return _trim_empty_tail(lines)


def _summary_lines(summary: str) -> list[str]:
    return [line.strip() for line in summary.splitlines() if line.strip()]


def _find_line(lines: list[str], prefix: str) -> str:
    return next((line for line in lines if line.startswith(prefix)), "")


def _strip_label(line: str, label: str) -> str:
    return re.sub(rf"^{re.escape(label)}[：:\s]*", "", line).strip()


@dataclass(frozen=True)
class QuotaRow:
    tier: str
    five_h: str
    seven_d: str
    source: str


def _quota_rows(summary: str) -> list[QuotaRow]:
    rows = []
    pattern = re.compile(r"(20x Pro|5x Pro|Plus)\s+5h\s+(\$[\d,.]+)\s+/\s+7d\s+(\$[\d,.]+)\s+\(([^)]+)\)")
    for match in pattern.finditer(summary):
        rows.append(QuotaRow(*match.groups()))
    return rows


def _quota_change(summary: str) -> str:
    match = re.search(r"趋势：(\$[\d,.]+)\s+→\s+(\$[\d,.]+)\s+\(([-\$\d,.]+),\s+([-\d.]+%)\)", summary)
    if not match:
        return ""
    return f"{match.group(3)}（{match.group(4)}）"


def _quota_trend(summary: str) -> list[tuple[str, str]]:
    match = re.search(r"近5次：(.+?)(?:\n|$)", summary)
    if not match:
        return []
    return re.findall(r"(2026-[0-9]{2}-[0-9]{2}(?:-[a-z0-9_]+)?)\s+(\$[\d,.]+)", match.group(1))


def _money_to_float(value: str) -> float:
    return float(value.replace("$", "").replace(",", ""))


def _money_short(value: str) -> str:
    return f"${_money_to_float(value):,.0f}"


def _sparkline(values: list[float]) -> str:
    if not values:
        return ""
    ticks = "▁▂▃▄▅▆▇█"
    low = min(values)
    high = max(values)
    if high == low:
        return ticks[-1] * len(values)
    return "".join(ticks[round((value - low) / (high - low) * (len(ticks) - 1))] for value in values)


@dataclass(frozen=True)
class IqCard:
    name: str
    score: float
    status: str
    passed: int
    tasks: int
    cost: str
    duration: str


def _iq_cards(summary: str) -> list[IqCard]:
    cards = []
    pattern = re.compile(
        r"(GPT-[0-9.]+-[a-z]+)\s+([\d.]+)\s+\(([^)]+)\)\s+([0-9]+)/([0-9]+)\s+费用\s+(\$[\d.]+)\s+耗时\s+([0-9.]+h)",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(summary):
        name, score, status, passed, tasks, cost, duration = match.groups()
        cards.append(
            IqCard(
                name=_format_model_name(name),
                score=float(score),
                status=status,
                passed=int(passed),
                tasks=int(tasks),
                cost=cost,
                duration=duration,
            )
        )
    return cards


def _format_model_name(name: str) -> str:
    model, effort = name.rsplit("-", 1)
    return f"{model} {effort}"


def _score_bar(score: float) -> str:
    filled = max(0, min(10, round(score / 120 * 10)))
    return "█" * filled + "░" * (10 - filled)


def _recommend_quality_iq_card(cards: list[IqCard]) -> IqCard | None:
    if not cards:
        return None
    return max(
        cards,
        key=lambda card: (
            card.score,
            _status_rank(card.status),
            card.passed / card.tasks if card.tasks else 0,
            -_money_to_float(card.cost),
            -_hours_to_float(card.duration),
        ),
    )


def _recommend_value_iq_card(cards: list[IqCard]) -> IqCard | None:
    candidates = [card for card in cards if card.score >= 90 and card.status.lower() != "red"]
    if not candidates:
        candidates = cards
    return max(
        candidates,
        key=lambda card: (
            card.score / _money_to_float(card.cost),
            card.score,
            -_hours_to_float(card.duration),
        ),
    )


def _status_rank(status: str) -> int:
    return {"green": 3, "yellow": 2, "red": 1}.get(status.lower(), 0)


def _hours_to_float(value: str) -> float:
    return float(value.rstrip("h"))


def _trim_empty_tail(lines: list[str]) -> list[str]:
    while lines and lines[-1] == "":
        lines.pop()
    return lines
