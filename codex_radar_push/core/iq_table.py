from datetime import datetime
import unicodedata
from zoneinfo import ZoneInfo

from codex_radar_push.core.intelligence import IntelligenceReport


def format_intelligence_table(report: IntelligenceReport, now: datetime | None = None) -> str:
    current_time = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    lines = [f"智商雷达：{current_time.strftime('%m-%d %H:%M')}（北京时间）",
             f"共 {len({row.model for row in report.rows})} 个模型 / {len(report.rows)} 个档位",
             f"工程数据：{_source_time(report.software_updated_at)}",
             f"视觉数据：{_source_time(report.visual_updated_at)}", "", "```"]
    rows = [(row.name, _score(row.composite), _score(row.software.score if row.software else None),
             _score(row.visual.score if row.visual else None),
             f"{row.minutes:.1f}分" if row.minutes is not None else "—") for row in report.rows]
    headers = ("模型 / 档位", "综合", "工程", "视觉", "耗时")
    widths = [max(_display_width(row[i]) for row in [headers, *rows]) for i in range(len(headers))]
    for row in [headers, *rows]:
        lines.append("  ".join(_pad_display(value, widths[i]) if i == 0 else _rjust_display(value, widths[i])
                               for i, value in enumerate(row)))
    lines.extend(["```", "综合分及耗时按两个分项的有效题量加权；— 表示分项数据未齐全。"])
    return "\n".join(lines)


def _score(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


def _source_time(value: str) -> str:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Shanghai")).strftime("%m-%d %H:%M")


def format_iq_table(model_iq: dict, now: datetime | None = None) -> str:
    rows = _model_rows(model_iq)
    if not rows:
        raise ValueError("降智雷达没有可用的模型数据")

    current_time = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    width = max(18, *(_display_width(row[0]) for row in rows))
    lines = [
        f"降智雷达：{current_time.strftime('%H:%M')}",
        "",
        "```",
        f"{_pad_display('模型', width)}  {_rjust_display('分数', 5)}  耗时",
    ]
    lines.extend(
        f"{_pad_display(name, width)}  {_rjust_display(f'{score:g}', 5)}  {duration}"
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
