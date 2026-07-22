from datetime import datetime
import unicodedata
from zoneinfo import ZoneInfo


def format_iq_table(model_iq: dict, now: datetime | None = None) -> str:
    rows = _model_rows(model_iq)
    if not rows:
        raise ValueError("降智雷达没有可用的模型数据")

    current_time = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    lines = [
        f"降智雷达：{current_time.strftime('%H:%M')}",
        "",
        "```",
        f"{_pad_display('模型', 18)}  {_rjust_display('分数', 5)}  耗时",
    ]
    lines.extend(
        f"{_pad_display(name, 18)}  {_rjust_display(f'{score:g}', 5)}  {duration}"
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
                latest["average_task_time_human"],
            )
        )

    for comparison in (model_iq.get("comparisons") or {}).values():
        metrics = comparison.get("latest") or {}
        if not _has_metrics(metrics):
            continue
        rows.append(
            (
                _display_name(comparison.get("label", "")),
                float(metrics["score"]),
                metrics["average_task_time_human"],
            )
        )
    return rows


def _has_metrics(metrics: dict) -> bool:
    return metrics.get("score") is not None and bool(metrics.get("average_task_time_human"))


def _root_model_name(metrics: dict) -> str:
    model = str(metrics.get("model", "")).removeprefix("gpt-5.6-")
    effort = str(metrics.get("reasoning_effort", ""))
    return _display_name(f"GPT-5.6 {model.title()} {effort}")


def _display_name(label: str) -> str:
    if label.startswith("GPT-5.6 "):
        return label.removeprefix("GPT-5.6 ")
    return label


def _display_width(value: str) -> int:
    return sum(2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in value)


def _pad_display(value: str, width: int) -> str:
    return value + " " * max(0, width - _display_width(value))


def _rjust_display(value: str, width: int) -> str:
    return " " * max(0, width - _display_width(value)) + value
