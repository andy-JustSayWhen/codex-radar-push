from datetime import datetime
import unicodedata
import math
import re
from collections import Counter
from zoneinfo import ZoneInfo

from codex_radar_push.core.intelligence import IntelligenceReport


def format_intelligence_table(report: IntelligenceReport, now: datetime | None = None) -> str:
    model_names = {row.model: _short_model_name(row.model) for row in report.rows}
    counts = Counter(model_names.values())
    rows = []
    for row in report.rows:
        name = model_names[row.model]
        if counts[name] > 1:
            name = row.model.removeprefix("gpt-").replace("-", " ")
        name = f"{name} {row.effort}".strip()
        minutes = row.software.minutes
        duration = f"{math.floor(minutes + 0.5)}分钟" if minutes is not None else "—"
        rows.append((name, row.software.score, duration))
    return _format_rows(rows, now)


def _short_model_name(model: str) -> str:
    name = re.sub(r"^gpt-", "", model, flags=re.IGNORECASE)
    match = re.fullmatch(r"\d+(?:\.\d+)*(?:-(.+))?", name)
    if match and match.group(1):
        return match.group(1).replace("-", " ").title()
    return name if match else name.replace("-", " ").title()


def format_iq_table(model_iq: dict, now: datetime | None = None) -> str:
    return _format_rows(_model_rows(model_iq), now)


def _format_rows(rows: list[tuple[str, float, str]], now: datetime | None = None) -> str:
    if not rows:
        raise ValueError("降智雷达没有可用的模型数据")

    current_time = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    width = max(18, *(_display_width(row[0]) for row in rows))
    score_width = max(5, *(len(f"{row[1]:g}") for row in rows))
    lines = [
        f"降智雷达：{current_time.strftime('%H:%M')}",
        "",
        "```",
        f"{_pad_display('模型', width)}  {_rjust_display('分数', score_width)}  耗时",
    ]
    lines.extend(
        f"{_pad_display(name, width)}  {_rjust_display(f'{score:g}', score_width)}  {duration}"
        for name, score, duration in rows
    )
    lines.append("```")
    return "\n".join(lines)


def _model_rows(model_iq: dict) -> list[tuple[str, float, str]]:
    rows = []
    latest = model_iq.get("latest") or {}
    if _has_metrics(latest):
        rows.append(
            (
                _root_model_name(latest),
                float(latest["score"]),
                latest.get("average_task_time_human") or "—",
            )
        )

    for key, comparison in (model_iq.get("comparisons") or {}).items():
        metrics = comparison.get("latest") or {}
        if not _has_metrics(metrics):
            continue
        rows.append(
            (
                _display_name(comparison.get("label") or key),
                float(metrics["score"]),
                metrics.get("average_task_time_human") or "—",
            )
        )
    return rows


def _has_metrics(metrics: dict) -> bool:
    return metrics.get("score") is not None


def _root_model_name(metrics: dict) -> str:
    model = str(metrics.get("model") or "未知模型")
    effort = str(metrics.get("reasoning_effort", ""))
    return f"{model} {effort}".strip()


def _display_name(label: str) -> str:
    return label


def _display_width(value: str) -> int:
    return sum(2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in value)


def _pad_display(value: str, width: int) -> str:
    return value + " " * max(0, width - _display_width(value))


def _rjust_display(value: str, width: int) -> str:
    return " " * max(0, width - _display_width(value)) + value
